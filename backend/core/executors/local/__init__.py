from core.executors import ExecutorBase, logger
from core.executors.local import tasks
from orchestration.celery import app
from django.conf import settings
import os


class ExecutorLocal(ExecutorBase):

    def __init__(self, process_id) -> None:
        super().__init__(process_id)

    def submit(self):
        logger.info("Preparing process...")
        env = os.environ.copy()
        env["PIPELINES_DIR"] = settings.PIPELINES_DIR
        args = {
            "stdout": str(self.out_file),
            "stderr": str(self.err_file),
            "cwd": str(self.cwd),
            "start_new_session": True,
            "env": env
        }
        logger.info("-> Pipeline: %s", self.title)
        logger.info("-> Command: %s", self.cmd)
        logger.info("-> Args: %s", args)
        logger.info("Submitted - Process ID: %s", self.process_id)
        return tasks.start.apply_async([self.process_id, self.cmd, args])
    
    def stop(self):
        logger.info(
            "Process marked to be stopped - Process ID: %s",
            str(self.process_id)
        )
        app.control.terminate(self.task_id)

    def finish(self):
        return "ExecutorLocal does not need this functionality"

    

