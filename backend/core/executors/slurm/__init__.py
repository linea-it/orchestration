from core.executors import ExecutorBase, logger
from core.executors.slurm import tasks
from django.conf import settings
import pathlib


class ExecutorSlurm(ExecutorBase):

    def __init__(self, process_id) -> None:
        super().__init__(process_id)

    def submit(self):
        logger.info("Preparing process...")

        sbatch_path = self.__create_sbatch_file()

        logger.info("-> Pipeline: %s", self.title)
        logger.info("-> Command: %s", self.cmd)
        logger.info("Submitted - Process ID: %s", self.process_id)
        return tasks.start.apply_async([self.process_id, sbatch_path, str(self.cwd)])

    def __create_sbatch_file(self):
        stemp = pathlib.Path(self.pipeline_path, "sbatch.template")
        assert stemp.is_file(), f"SLURM template not found: {stemp}"
        with open(stemp, encoding="utf-8") as _file:
            sbatch_template = _file.read()
            sbatch_str = sbatch_template.format(
                jobname=f"JOB_{self.process_id}",
                cwd=self.cwd,
                out=self.out_file,
                err=self.err_file,
                cmd=" ".join(self.cmd),
            )
            sbatch_file = pathlib.Path(self.cwd, "job.sbatch")
            with open(sbatch_file, "w", encoding="utf-8") as _file:
                _file.write(sbatch_str)

            return str(sbatch_file)


    def stop(self):
        logger.info("Stopping JobID: %s", self.process.pid)
        return tasks.stop.apply_async([self.process.pid])

