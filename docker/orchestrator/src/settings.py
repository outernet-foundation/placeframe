from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field
from pydantic.functional_validators import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    backend: Literal["aws", "docker"] = Field()

    postgres_host: str = Field()
    database_name: str = Field()
    database_user: str = Field()
    database_user_password: str = Field()

    batch_job_queue: str = Field()
    batch_job_definition: str = Field()

    s3_endpoint_url: AnyHttpUrl | None = None
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    captures_bucket: str = Field()
    reconstructions_bucket: str = Field()

    debug_run_reconstruction: bool = Field()
    debug_wait_run_reconstruction: bool = Field()

    @model_validator(mode="after")
    def check_storage_config(self):
        using_minio = self.s3_endpoint_url is not None
        creds_provided = self.s3_access_key and self.s3_secret_key

        if using_minio and not creds_provided:
            raise ValueError("S3_ACCESS_KEY and S3_SECRET_KEY are required when S3_ENDPOINT_URL is set.")

        return self


@lru_cache()
def get_settings() -> Settings:
    return Settings.model_validate({})
