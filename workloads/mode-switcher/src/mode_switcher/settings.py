from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings

Mode = Literal["localization", "reconstruction"]


class Settings(BaseSettings):
    default_mode: Mode = "localization"


@lru_cache()
def get_settings() -> Settings:
    return Settings.model_validate({})
