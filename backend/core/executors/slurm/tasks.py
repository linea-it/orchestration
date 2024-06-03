from core.models import Process
from celery import shared_task
import logging
import socket
import subprocess
from django.conf import settings
import pathlib
from django.utils.timezone import now
from core.utils import get_returncode
from core.executors.slurm.commands import status_by_job_id, scancel, sbatch

logger = logging.getLogger()


@shared_task
def start(process_id, sbatch_file, cwd):
    
    process = Process.objects.get(id=process_id)
    
    try:
        logger.info("Begin process[%s]", process_id)
        result = sbatch(sbatch_file, cwd)
        success_msg = 'Submitted batch job'
        stdout = result.stdout.decode('utf-8')

        if success_msg in stdout:
            logger.info(stdout)
            job_id = int(stdout.split(' ')[3])
            process.worker = socket.gethostname()
            process.pid = job_id
            process.status = 2  # number representing 'running' in db
            process.started_at = now()
            stderr = None
        else:
            stderr = result.stderr.decode('utf-8')
            logger.error("Error: %s", stderr)
            logger.error("Process[%s] failed.", process_id)
            process.status = 5  # number representing 'failure' in db
    except Exception as _err:
        stderr = _err
        logger.error("Error: %s", stderr)
        logger.error("Process[%s] failed.", process_id)
        process.status = 5  # number representing 'failure' in db
    finally:
        if stderr:
            err_file = pathlib.Path(settings.PROCESSING_DIR, process.path, "run.err")
            with open(err_file, "a", encoding="utf-8") as _file:
                _file.write(str(stderr))

    process.save()


@shared_task
def status(job_id):
    return status_by_job_id(job_id)


@shared_task
def check_running_processes():
    logger.debug("--> Check Running Processes...")
    # get running processes by slurm
    processes = Process.objects.filter(executor__exact='slurm', status__exact=2)
    for process in processes:
        worker = process.worker
        check_finish.apply_async(args=(process.pk,), queue=f"slurm.{worker}")


@shared_task
def check_finish(process_id):
    process = Process.objects.get(id=process_id)

    if not is_active(process.pid):
        logger.debug(f"Finishing process {process_id}")
        finalize_process(process_id)


@shared_task
def stop(process_id):
    process = Process.objects.get(id=process_id)
    status = is_active(process.pid)

    if not status:
        logger.info("JobId %s not running!")
        return status

    try:
        result = scancel(process.pid)
        stdout = result.stdout.decode('utf-8')
        logger.info(f"STDout: {stdout}")

        if result.returncode:
            stderr = result.stderr.decode('utf-8')
            logger.error("Error: %s", stderr)
            logger.error("Process[%s] stop failed: %s", process_id, process.pid)
            process.status = 5  # number representing 'failed' in db
        else:
            logger.info(stdout)
            process.status = 4  # number representing 'stopped' in db
            stderr = None

    except Exception as err:
        stderr = err
        logger.error("Error: %s", err)
        logger.error("Process[%s] stop failed: %s", process_id, process.pid)
        process.status = 5  # number representing 'failed' in db
    finally:
        if stderr:
            err_file = pathlib.Path(settings.PROCESSING_DIR, process.path, "run.err")
            with open(err_file, "a", encoding="utf-8") as _file:
                _file.write(str(stderr))

    process.ended_at = now()
    process.save()
    return process.status


def finalize_process(process_id):
    process = Process.objects.get(id=process_id)
    path = pathlib.Path(settings.PROCESSING_DIR, process.path)

    if not path.is_dir():
        logger.warn(f"ProcessDir not found: {str(path)}")
        return_code = -1

    return_code = get_returncode(str(path))

    if return_code == 0:
        logger.debug("Process[%s] succeeded.", process_id)
        process.status = 0  # number representing 'success' in db
    else:
        logger.debug("Process[%s] failed.", process_id)
        process.status = 5  # number representing 'failure' in db

    process.ended_at = now()
    process.save()


def is_active(job_id):
    try:
        status = status_by_job_id(job_id)
        if not status:
            return False

        logger.info("JobId %s status: %s", job_id, status)
        if "RUNNING" in status or "PENDING" in status:
            return True
        else:
            return False
    except Exception as err:
        logger.error("Error: %s", err)
        return False
