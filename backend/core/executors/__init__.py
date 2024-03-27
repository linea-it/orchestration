from core.utils import get_pipeline, load_config
from core.pipeline import Pipeline
from core.models import Process
from django.conf import settings
import logging
import pathlib
import yaml
import json

logger = logging.getLogger("orchestration")


class ExecutorBase:

    def __init__(self, process_id) -> None:
        logger.info("Loading Process ID: %s", process_id)
        self.__process = Process.objects.get(id=process_id)
        self.__pipeline = self.__load_pipeline(self.__process.pipeline)
        self.__config = self.__load_config(self.__process.used_config)
        path = pathlib.Path(settings.PROCESSING_DIR, self.__process.path)
        logger.info("-> ProcessDir: %s", path)
        path.mkdir(parents=True, exist_ok=True)
        self.__cwd = path

        if not self.config_file.is_file():
            self.__create_config_file()
        
        if not self.process_file.is_file():
            self.__create_process_file()

    def __load_pipeline(self, pipeline):
        pipeline_data = get_pipeline(pipeline)
        return Pipeline(**pipeline_data)
    
    def __load_config(self, config):
        if config: return json.loads(config)
        config = load_config(self.__pipeline.schema_config)
        return config.model_dump()

    @property
    def pipeline_path(self):
        return self.__pipeline.path

    @property
    def executable(self):
        return pathlib.Path(self.__pipeline.path, self.__pipeline.executable)
    
    @property
    def pipeline(self):
        return self.__pipeline.name

    @property
    def title(self):
        return self.__pipeline.display_name

    @property
    def err_file(self):
        return pathlib.Path(self.__cwd, "run.err")

    @property
    def out_file(self):
        return pathlib.Path(self.__cwd, "run.out")

    @property
    def config_file(self):
        return pathlib.Path(self.__cwd, "config.yml")

    @property
    def process_file(self):
        return pathlib.Path(self.__cwd, "process.yml")

    def __create_process_file(self):
        with open(self.process_file, "w") as outfile:
            yaml.dump(self.__pipeline.model_dump(), outfile)

    def __create_config_file(self):
        with open(self.config_file, "w") as outfile:
            yaml.dump(self.__config, outfile)

    @property
    def cmd(self):
        return [
            self.__pipeline.runner,
            str(self.executable),
            str(self.config_file)
        ]
    
    @property
    def cwd(self):
        return self.__cwd

    @property
    def process_id(self):
        return self.__process.pk
    
    @property
    def used_worker(self):
        return self.__process.worker
    
    @property
    def pid(self):
        return self.__process.pid
    
    @property
    def task_id(self):
        return self.__process.task_id

    def submit(self):
        pass
    
    def stop(self):
        pass
