from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    backend: Literal["aws", "docker"] = Field()
    capture_id: str = Field()
    job_queue_arn: str = Field()
    features_job_definition_arn_prefix: str = Field()
    debug_features: str = Field()
    debug_wait_features: str = Field()


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore
