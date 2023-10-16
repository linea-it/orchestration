import logging.config
import logging
import os
import pathlib
import subprocess
import yaml

from symphony.process import run_pipeline
from symphony.utils import get_pipeline, merge_config
import symphony.config as CONFIG

logging.config.dictConfig(CONFIG.LOGGING)


class Maestro:
    """Responsible for managing pipeline processing

    Args:
        returncode (_type_): _description_

    Returns:
        _type_: _description_
    """

    def __init__(self, params) -> None:
        self.worker_id = os.getpid()
        self.task_id = params.get("task_id")
        self.prefix_task = self.task_id[:8]

        self.logger = logging.getLogger("orchest")
        self.pipename = params.get("pipeline-name")
        self.__loginfo(f"Loading pipeline: {self.pipename}")
        self.pipeline = get_pipeline(self.pipename)

        self.output_dir = params.get("output-dir")
        self.sandbox = pathlib.Path(
            self.output_dir, f"{self.pipename.lower()}.{self.prefix_task}"
        )

        self.config = None

        if hasattr(self.pipeline, "config"):
            pconf = pathlib.Path(self.pipeline.basepath, self.pipeline.config)
            self.config = merge_config(pconf, params.get("config", {}))

    def start(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        self.sandbox.mkdir(exist_ok=True)
        self.__loginfo(f"Sandbox created: {self.sandbox}")

        if self.config:
            self.__make_config_file()

        cmd, args = self.__mount_command()
        return run_pipeline(cmd, args)

    def registry_pid(self, subpid):
        """_summary_

        Args:
            subpid (_type_): _description_
        """
        pathpid = pathlib.Path(self.sandbox, "pid.yml")
        with open(pathpid, "w", encoding="UTF-8") as fpid:
            yaml.dump({"worker_id": self.worker_id, "child_id": subpid}, fpid)

    def finish(self, returncode):
        """_summary_

        Args:
            returncode (_type_): _description_

        Returns:
            _type_: _description_
        """
        if returncode is 0:
            mesg = f"Finished: {pathlib.Path(self.sandbox, 'run.out')}"
            self.__loginfo(mesg)
            return True

        mesg = f"Error!: {pathlib.Path(self.sandbox, 'run.err')}"
        self.__logerror(mesg)
        raise subprocess.SubprocessError("Error in run_pipeline")

    def __make_config_file(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        config_file = pathlib.Path(self.sandbox, self.pipeline.config)

        with open(config_file, "w", encoding="UTF-8") as file:
            yaml.dump(self.config._asdict(), file)

        return config_file

    def __mount_command(self):
        env = os.environ.copy()

        fullexec = pathlib.Path(self.pipeline.basepath, self.pipeline.executable)
        command = [self.pipeline.runner, fullexec]

        if self.config:
            command.append(self.pipeline.config)

        stdout = pathlib.Path(self.sandbox, "run.out")
        stderr = pathlib.Path(self.sandbox, "run.err")

        self.__loginfo(f"Running: {command}")

        return command, {
            "stdout": open(stdout, "w", encoding="UTF-8"),
            "stderr": open(stderr, "w", encoding="UTF-8"),
            "cwd": self.sandbox,
            "env": env,
        }

    def __loginfo(self, message):
        self.logger.info("taskID %s: %s", self.prefix_task, message)

    def __logerror(self, message):
        self.logger.error("taskID %s: %s", self.prefix_task, message)


if __name__ == "__main__":
    import argparse

    logger = logging.getLogger()

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--outputdir", default=".")
    parser.add_argument("-p", "--pipeline", default="pz_test")
    _args = parser.parse_args()

    _pipename = _args.pipeline

    _params = {"pipeline-name": _pipename, "output-dir": _args.outputdir}

    maestro = Maestro(_params)
    logger.info("Starting...")
    PROC = maestro.start()
    PROC.wait()
    maestro.finish(PROC)
    logger.info("Bye!")
