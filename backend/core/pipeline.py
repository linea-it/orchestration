from pydantic import BaseModel, validator
from pathlib import Path
from django.conf import settings


class Pipeline(BaseModel):
    name: str
    path: str
    executor: str
    runner: str
    executable: str
    version: str
    display_name: str | None
    schema_config: str | None

    @validator('path', pre=True)
    def validate_path(cls, value):
        assert Path(value).is_dir(), f"Folder '{value}' not found."
        return value
    
    @validator('schema_config', pre=True)
    def validate_config(cls, value):
        assert Path(value).is_file(), f"File '{value}' not found."
        return value


if __name__ == "__main__":
    from core.utils import get_pipeline

    pipe_info = get_pipeline('cross_lsdb')
    pipeline = Pipeline(**pipe_info)