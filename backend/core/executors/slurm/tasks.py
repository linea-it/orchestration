from core.models import Process, ProcessStatus
from celery import shared_task
import logging
import socket
from django.conf import settings
import pathlib
from django.utils.timezone import now
from core.utils import get_returncode
from core.executors.slurm.commands import status_by_job_id, scancel, sbatch

logger = logging.getLogger("orchestration")

SLURM_CODES_ONGOING = ["COMPLETING", "PENDING", "RUNNING"]


@shared_task
def start(process_id, sbatch_file, cwd):
    """ Start the process. Register the process in the database with 'Queued' 
    status and ubmit it to Slurm.

    Args:
        process_id (int): process ID
        sbatch_file (str): sbatch file path 
        cwd (str): path to execution diretory
    """
    
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
            update_status(process, "QUEUED")
            process.started_at = now()
            stderr = None
        else:
            stderr = result.stderr.decode('utf-8')
            logger.error("Process[%s] failed: %s", process_id, stderr)
            update_status(process, "FAILED")
    except Exception as _err:
        stderr = _err
        logger.error("Process[%s] failed: %s", process_id, stderr)
        update_status(process, "FAILED")
    finally:
        if stderr:
            append_error(process.path, stderr)

    process.save()


@shared_task
def status(job_id):
    """ Return process status

    Args:
        job_id (int): job ID

    Returns:
        str: process status
    """

    return status_by_job_id(job_id)


@shared_task
def check_running_processes():
    """ Check and update the status of running processes """

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
        # checks the process exactly on the worker in which it was executed.
        check_finish.apply_async(args=(process.pk,), queue=f"slurm.{worker}")

    logger.debug(f"# processes: {len(processes)}")


@shared_task
def check_finish(process_id):
    """ Checks and updates the process finish

    Args:
        process_id (int): process ID
    """

    process = Process.objects.get(id=process_id)

    if not is_active(process):
        logger.debug(f"Finishing process {process_id}...")
        finalize_process(process_id)


@shared_task
def stop(process_id):
    """ Stop process in Slurm

    Args:
        process_id (int): process ID

    Returns:
        str: process status
    """

    process = Process.objects.get(id=process_id)
    slurm_status = is_active(process)

    if not slurm_status:
        logger.warn("JobId %s not running!")
        return status

    try:
        result = scancel(process.pid)
        stdout = result.stdout.decode('utf-8')
        logger.debug(f"SCANCEL stdout: {stdout}")

        if result.returncode:
            stderr = result.stderr.decode('utf-8')
            logger.error("Process[%s] stop failed: %s", process_id, stderr)
            update_status(process, "FAILED")
        else:
            logger.debug(stdout)
            update_status(process, "STOPPED")
            stderr = None

    except Exception as err:
        stderr = err
        logger.error("Process[%s] stop failed: %s", process_id, stderr)
        update_status(process, "FAILED")
    finally:
        if stderr:
            append_error(process.path, stderr)

    process.ended_at = now()
    process.save()

    return process.status


def finalize_process(process_id):
    """ Record the end of the process in the database.

    Args:
        process_id (int): process ID
    """

    process = Process.objects.get(id=process_id)
    path = pathlib.Path(settings.PROCESSING_DIR, process.path)

    if not path.is_dir():
        logger.warn(f"ProcessDir not found: {str(path)}")
        return_code = -1
    else:
        return_code = get_returncode(str(path))

    if return_code == 0:
        logger.debug("Process[%s] succeeded.", process_id)
        update_status(process, "SUCCESSFUL")
    else:
        logger.debug("Process[%s] failed.", process_id)
        update_status(process, "FAILED")

    process.ended_at = now()
    process.save()


def is_active(process):
    """ Checks if the process is in progress in Slurm. If it is still active 
    and the status is different in the database, it updates the status.

    Args:
        process (Process): Process object

    Returns:
        bool: True if the process is active otherwise False
    """

    try:
        job_id = process.pid
        slurm_status = status_by_job_id(job_id)
        if not slurm_status:
            return False

        logger.debug("JobId %s status: %s", job_id, slurm_status)
        if slurm_status in SLURM_CODES_ONGOING:
            if slurm_status != ProcessStatus(process.status).name:
                logger.debug("Updating... %s =! %s", slurm_status, ProcessStatus(process.status).name)
                update_status(process, slurm_status)
            return True
        else:
            return False
    except Exception as err:
        logger.error("Error: %s", err)
        append_error(process.path, err)
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


def get_status_id(job_status):
    """ Get status id 

    Args:
        job_status (str): status
    """

    try:
        st = [i[1] for i in ProcessStatus.choices].index(
            job_status.lower().capitalize()
        )
    except ValueError as err:
        logger.warn("Warning: %s", err)
        st = None
    
    return st


def append_error(path, message):
    """ Append error in log file

    Args:
        path (str): process path
        message (str): error message
    """
    err_file = pathlib.Path(
        settings.PROCESSING_DIR, path, "run.err"
    )
    with open(err_file, "a", encoding="utf-8") as _file:
        _file.write(f"\n{message}")