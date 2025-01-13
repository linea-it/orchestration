from core.models import Process, ProcessStatus
from celery import shared_task
import logging
import socket
from django.conf import settings
import pathlib
from django.utils.timezone import now
from core.utils import get_returncode
from core.executors.slurm.commands import status_by_job_id, scancel, sbatch

logger = logging.getLogger()

SLURM_CODES_ONGOING = ["COMPLETING", "PENDING", "RUNNING"]


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
            # process.status = 6  # number representing 'Queued' in db
            update_status(process, "QUEUED")
            process.started_at = now()
            stderr = None
        else:
            stderr = result.stderr.decode('utf-8')
            logger.error("Process[%s] failed: %s", process_id, stderr)
            # process.status = 5  # number representing 'Failed' in db
            update_status(process, "FAILED")
    except Exception as _err:
        stderr = _err
        logger.error("Process[%s] failed: %s", process_id, stderr)
        # process.status = 5  # number representing 'Failed' in db
        update_status(process, "FAILED")
    finally:
        if stderr:
            err_file = pathlib.Path(
                settings.PROCESSING_DIR, process.path, "run.err"
            )
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
    processes = []

    for st in ["PENDING", "RUNNING", "QUEUED"]:
        status_id = get_status_id(st)

        if status_id:
            processes += Process.objects.filter(
                executor__exact='slurm',
                status__exact=status_id
            )

    for process in processes:
        worker = process.worker
        check_finish.apply_async(args=(process.pk,), queue=f"slurm.{worker}")


@shared_task
def check_finish(process_id):
    process = Process.objects.get(id=process_id)

    if not is_active(process):
        logger.debug(f"Finishing process {process_id}")
        finalize_process(process_id)


@shared_task
def stop(process_id):
    process = Process.objects.get(id=process_id)
    status = is_active(process)

    if not status:
        logger.info("JobId %s not running!")
        return status

    try:
        result = scancel(process.pid)
        stdout = result.stdout.decode('utf-8')
        logger.debug(f"STDout: {stdout}")

        if result.returncode:
            stderr = result.stderr.decode('utf-8')
            logger.error("Process[%s] stop failed: %s", process_id, stderr)
            # process.status = 5  # number representing 'Failed' in db
            update_status(process, "FAILED")
        else:
            logger.info(stdout)
            # process.status = 4  # number representing 'Stopped' in db
            update_status(process, "STOPPED")
            stderr = None

    except Exception as err:
        stderr = err
        logger.error("Process[%s] stop failed: %s", process_id, stderr)
        # process.status = 5  # number representing 'Failed' in db
        update_status(process, "FAILED")
    finally:
        if stderr:
            err_file = pathlib.Path(
                settings.PROCESSING_DIR, process.path, "run.err"
            )
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
        # process.status = 0  # number representing 'Successful' in db
        update_status(process, "SUCCESSFUL")
    else:
        logger.debug("Process[%s] failed.", process_id)
        # process.status = 5  # number representing 'Failed' in db
        update_status(process, "FAILED")

    process.ended_at = now()
    process.save()


def is_active(process):
    try:
        job_id = process.pid
        status = status_by_job_id(job_id)
        if not status:
            return False

        logger.info("JobId %s status: %s", job_id, status)
        if status in SLURM_CODES_ONGOING:
            if status != ProcessStatus(process.status).name:
                update_status(process, status)
            return True
        else:
            return False
    except Exception as err:
        logger.error("Error: %s", err)
        return False


def update_status(process, status):
    """ Update status

    Args:
        process (Process): Process object
        status (str): Slurm status
    """

    
    status_id = get_status_id(status)

    if status_id:
        process.status = status_id
        process.save()


def get_status_id(status):
    """ Get status id 

    Args:
        status (status): status
    """

    try:
        st = [i[1] for i in ProcessStatus.choices].index(
            status.lower().capitalize()
        )
    except ValueError as err:
        logger.warn("Warning: %s", err)
        st = None
    
    return st