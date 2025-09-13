import os
from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, model_validator
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    postgres_host: str | None = None
    database_name: str | None = None
    database_password: str | None = None


class ApiSettings(DatabaseSettings):
    backend: Literal["aws", "docker"] = Field()

    s3_endpoint_url: AnyHttpUrl | None = None
    s3_access_key: str | None = None
    s3_secret_key: str | None = None

    job_queue_arn: str = Field()
    reconstruction_job_definition_id: str = Field()
    features_job_definition_id: str = Field()

    debug_reconstruction: bool | None = None
    debug_wait_reconstruction: bool | None = None
    debug_features: bool | None = None
    debug_wait_features: bool | None = None

    @model_validator(mode="after")
    def check_storage_config(self):
        using_minio = self.s3_endpoint_url is not None
        creds_provided = self.s3_access_key and self.s3_secret_key

        if using_minio and not creds_provided:
            raise ValueError("S3_ACCESS_KEY and S3_SECRET_KEY are required when S3_ENDPOINT_URL is set.")

        return self


@lru_cache()
def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()


@lru_cache()
def get_api_settings() -> ApiSettings:
    # During codegen, we don't have access to all env vars, so skip validation.
    if os.environ.get("CODEGEN"):
        return ApiSettings.model_construct()

    return ApiSettings.model_validate({})
