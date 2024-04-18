from core.models import Process
from celery import shared_task
from celery.signals import task_revoked
import logging
import socket
import subprocess
import psutil
import time, datetime

logger = logging.getLogger()


@shared_task
def start(process_id, cmd, args=None):
    args = {} if not args else args

    if "stderr" in args:
        args["stderr"] = open(args["stderr"], "w", encoding="UTF-8")

    if "stdout" in args:
        args["stdout"] = open(args["stdout"], "w", encoding="UTF-8")

    logger.info("Begin process[%s]: %s", process_id, cmd)

    proc_child = subprocess.Popen(cmd, **args)
    # proc_child = subprocess.Popen(["bash", "/pipelines/cross_lsdb/test.sh"], **args)
    process = Process.objects.get(id=process_id)
    process.worker = socket.gethostname()
    process.pid = proc_child.pid
    process.status = 2  # number representing 'running' in db
    process.started_at = datetime.datetime.now()
    process.save()

    logger.info("-> system pid: %s", proc_child.pid)
    return_code = proc_child.wait()

    if return_code == 0:
        logger.info("Process[%s] succeeded.", process_id)
        process.status = 0  # number representing 'success' in db
    else:
        logger.info("Process[%s] failed.", process_id)
        process.status = 5  # number representing 'failure' in db

    process.ended_at = datetime.datetime.now()
    process.save()


@shared_task
@task_revoked.connect(sender=start)
def task_revoked_handler(request=None, **kwargs):
    """Responsible for handling the task revoke process."""
    task_id = request.id

    def on_terminate(proc):
        mesg = f"Child PID {proc.pid} terminated"
        if proc.returncode is not None:
            mesg = f" with exit code {proc.returncode}"

        logger.debug(mesg)

    try:
        process_id = request.args[0]
        process = Process.objects.get(id=process_id)
        sysproc = psutil.Process(process.pid)
        children = sysproc.children(recursive=True)
        children.append(sysproc)

        for child in children:
            child.terminate()

        _, alive = psutil.wait_procs(children, timeout=5, callback=on_terminate)

        for proc in alive:
            proc.kill()

        time.sleep(0.5)
        process.status = 4  # number representing 'revoked' in db
        process.save()
        logger.info("Task stopped: %s", task_id)
    except Exception as _:
        process_id = request.args[0]
        process = Process.objects.get(id=process_id)
        process.status = 5  # number representing 'failed' in db
        process.save()
        logger.info("Task stop failed : %s", task_id)
        logger.exception()
