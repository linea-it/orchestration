""" _summary_ """

import pathlib
import logging
import os
from collections import namedtuple
import yaml


def get_pipeline(name):
    """_summary_

    Args:
        name (_type_): _description_

    Returns:
        _type_: _description_
    """

    pipe_dir = os.environ.get("PIPELINES_DIR")
    pipe_file = pathlib.Path(pipe_dir, "pipelines.yml")

    with open(pipe_file, encoding="UTF-8") as _file:
        pipelines = yaml.load(_file, Loader=yaml.loader.SafeLoader)
        pipeline = pipelines.get(name)

    basepath = pathlib.Path(pipe_dir, name)
    pipeline["basepath"] = basepath

    _pipeline = namedtuple("Pipeline", pipeline)
    return _pipeline(**pipeline)


def merge_config(config_file, user_config):
    """_summary_

    Args:
        config_file (_type_): _description_
        user_config (_type_): _description_

    Returns:
        _type_: _description_
    """

    with open(config_file, encoding="UTF-8") as _file:
        config = yaml.load(_file, Loader=yaml.loader.SafeLoader)

    logging.debug("User config: %s", user_config)
    logging.debug("Default config: %s", config)
    config.update(user_config)
    logging.debug("Merge config: %s", config)

    _config = namedtuple("ProcessConfig", config)
    return _config(**config)
