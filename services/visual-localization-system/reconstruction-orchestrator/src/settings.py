from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field()
    worker_assume_role_arn: str = Field()
    backend: Literal["aws", "docker"] = Field()
    batch_job_queue: str = Field()
    batch_job_definition: str = Field()
    s3_captures_bucket_name: str = Field()
    s3_reconstructions_bucket_name: str = Field()


@lru_cache()
def get_settings() -> Settings:
    return Settings.model_validate({})
