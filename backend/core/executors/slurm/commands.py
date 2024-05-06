import logging
import subprocess

JOBSTATUS = ["COMPLETED", "COMPLETING", "FAILED", "PENDING", "PREEMPTED", "RUNNING", "SUSPENDED", "STOPPED"]
logger = logging.getLogger()


def sbatch(sbatch_filepath, cwd="."):
    cmd = ["sbatch", sbatch_filepath]
    return subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def scancel(job_id):
    cmd = ["scancel", str(job_id)]
    logger.info("Stopping JobID %s...", job_id)
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def status_by_job_id(job_id):
    cmd = f"squeue --job {str(job_id)} -o '%T' | tail -1"
    logger.info(f"cmd: {cmd}")
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    status = proc.stdout.decode('utf-8').replace('\n','')

    if status in JOBSTATUS:
        logger.info("JobId %s status: %s", job_id, status)
        return status

    return None

