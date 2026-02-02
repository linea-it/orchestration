"""Configuration module for cross-LSDB development pipeline."""

from pydantic import BaseModel


class Inputs(BaseModel):
    """Input parameters for hello world pipeline."""

    message: str = "Hello, World!"


class Config(BaseModel):
    """Configuration for hello world pipeline."""

    inputs: Inputs = Inputs()


if __name__ == "__main__":
    import yaml

    cfg = Config()

    with open("config.yml", "w", encoding="utf-8") as outfile:
        yaml.dump(cfg.model_dump(), outfile)
