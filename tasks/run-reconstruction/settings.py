from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    backend: Literal["aws", "docker"] = Field()

    capture_id: str = Field()
    job_queue_arn: str = Field()
    features_job_definition_id: str = Field()

    debug_features: bool | None = None
    debug_wait_features: bool | None = None


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore
