from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_dir: Path = Field()


@lru_cache()
def get_settings() -> Settings:
    return Settings.model_validate({})
