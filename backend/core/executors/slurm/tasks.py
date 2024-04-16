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
def status(job_id):
    return get_status(job_id)


@shared_task
def stop(process_id):

    process = Process.objects.get(id=process_id)
    pstatus = get_status(process.pid)

    if not pstatus:
        logger.info("JobId %s not running!")
        return pstatus

    try:
        cmd = ["scancel", "--quiet", str(process.pid)]
        logger.info("Stopping process[%s]: JobID %s", process_id, process.pid)
        result = subprocess.run(cmd, stdout=subprocess.PIPE)
        success_msg = 'has been revoked'
        stdout = result.stdout.decode('utf-8')
        if success_msg in stdout:
            logger.info(stdout)
            process.status = 4  # number representing 'stopped' in db
            process.save()
        else:
            logger.error("Error: %s", result.stderr)
            logger.error("Process[%s] stop failed: %s", process_id, process.pid)
    except Exception as err:
        logger.error("Error: %s", err)
        logger.error("Process[%s] stop failed: %s", process_id, process.pid)

    return process.status


def get_status(job_id):
    try:
        cmd = ["squeue", "--job", str(job_id), "-o", '"%T"', "|", "tail", "-1"]
        result = subprocess.run(cmd, stdout=subprocess.PIPE)
        error_msg = 'Invalid job id specified'
        stdout = result.stdout.decode('utf-8')
        if error_msg in stdout:
            logger.error("Error: %s", result.stderr)
            return None
        else:
            logger.info("JobId %s status: %s", job_id, stdout)
            return stdout
    except Exception as err:
        logger.error("Error: %s", err)
        return None
