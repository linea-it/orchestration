import logging.config
import logging
import pathlib
import os
import importlib
import psutil
import yaml

from celery import Celery, Task as callbackcls
from celery.signals import task_revoked
from symphony.maestro import Maestro

import symphony.config as CONFIG

logging.config.dictConfig(CONFIG.LOGGING)
logger = logging.getLogger("orchest")

PYCALLBACK_CLASS = os.getenv("PYCALLBACK_CLASS")
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "pyamqp://guest@localhost//")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379")

app = Celery(
    "pipelines",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    broker_connection_retry_on_startup=False,
)

if PYCALLBACK_CLASS:
    package, clsname = PYCALLBACK_CLASS.split(".")
    callbackcls = getattr(importlib.import_module(package), clsname)


@app.task(base=callbackcls)
def run(params):
    """Runs pipeline

    Args:
        params (dict): process parameters
    """
    task_id = run.request.id
    logger.info("Starting task ID: %s", task_id)
    params["task_id"] = task_id
    maestro = Maestro(params)
    logger.info("Processing task ID: %s", task_id)
    process = maestro.start()
    spid = process.pid
    logger.info("Registering task ID: %s -> child ID: %s", task_id, str(spid))
    maestro.registry_pid(spid)
    process.wait()
    data = maestro.finish(process.returncode)
    logger.info("Done task ID: %s", task_id)
    return data


@task_revoked.connect(sender=run)
def task_revoked_handler(request=None, **kwargs):
    """Responsible for handling the task revoke process."""

    task_id = request.id
    logger.info("Handling task stop. Task ID: %s", task_id)

    def on_terminate(proc):
        mesg = f"Child ID {proc.pid} terminated"
        if proc.returncode is not None:
            mesg = f" with exit code {proc.returncode}"

        logger.debug(mesg)

    params = request.args[0]
    pipename = params.get("pipeline-name")
    outdir = params.get("output-dir")
    file_pids = pathlib.Path(outdir, f"{pipename}.{task_id[:8]}", "pid.yml")

    with open(file_pids, encoding="UTF-8") as fpids:
        data = yaml.load(fpids, Loader=yaml.loader.SafeLoader)
        _pid = data.get("child_id", None)
        logger.debug("Child ID: %s", _pid)

        parent = psutil.Process(_pid)
        children = parent.children(recursive=True)
        children.append(parent)

        for child in children:
            child.terminate()

        _, alive = psutil.wait_procs(children, timeout=5, callback=on_terminate)

        for proc in alive:
            proc.kill()

    logger.info("Task ID %s revoked", task_id)
