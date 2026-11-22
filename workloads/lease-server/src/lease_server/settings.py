from functools import lru_cache
from os import environ

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_host: str = Field()
    database_name: str = Field()
    database_orchestration_user: str = Field()
    database_orchestration_user_password: str = Field()


@lru_cache()
def get_settings() -> Settings:
    if environ.get("CODEGEN"):
        return Settings.model_construct()

    return Settings.model_validate({})
