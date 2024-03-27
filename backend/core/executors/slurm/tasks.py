from core.models import Process
from celery import shared_task
from celery.signals import task_revoked
import logging
import socket
import subprocess
import psutil
import time

logger = logging.getLogger()


@shared_task
def start(process_id, sbatch_file, cwd):
    
    process = Process.objects.get(id=process_id)
    
    try:
        cmd = ["sbatch", sbatch_file]
        logger.info("Begin process[%s]: %s", process_id, cmd)
        result = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE)
        success_msg = 'Submitted batch job'
        stdout = result.stdout.decode('utf-8')
        if success_msg in stdout:
            logger.info(stdout)
            job_id = int(stdout.split(' ')[3])
            process.worker = socket.gethostname()
            process.pid = job_id
            process.status = 2  # number representing 'running' in db
        else:
            err = result.stderr
            logger.error("Error: %s", err)
            logger.error("Process[%s] failed.", process_id)
            process.status = 5  # number representing 'failure' in db
    except Exception as err:
        logger.error("Error: %s", err)
        logger.error("Process[%s] failed.", process_id)
        process.status = 5  # number representing 'failure' in db

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
