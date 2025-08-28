from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    capture_id: str = Field()
    aws_batch_job_array_index: str = Field()


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore
