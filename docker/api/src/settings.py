from functools import lru_cache
from os import environ

from pydantic import AnyHttpUrl, Field, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    public_url: AnyHttpUrl = Field()

    auth_audience: str = Field()
    auth_issuer_url: AnyHttpUrl = Field()
    auth_url: AnyHttpUrl = Field()
    auth_token_url: AnyHttpUrl = Field()
    auth_certs_url: AnyHttpUrl = Field()

    postgres_host: str = Field()
    database_name: str = Field()
    database_api_user: str = Field()
    database_api_user_password: str = Field()
    database_auth_user: str = Field()
    database_auth_user_password: str = Field()
    database_orchestration_user: str = Field()
    database_orchestration_user_password: str = Field()

    minio_endpoint_url: AnyHttpUrl | None = None
    minio_access_key: str | None = None
    minio_secret_key: str | None = None

    localizer_container_url: AnyHttpUrl = Field()

    reconstructions_bucket: str = Field(...)

    @model_validator(mode="after")
    def check_storage_config(self):
        using_minio = self.minio_endpoint_url is not None
        creds_provided = self.minio_access_key and self.minio_secret_key

        if using_minio and not creds_provided:
            raise ValueError("MINIO_ACCESS_KEY and MINIO_SECRET_KEY are required when MINIO_ENDPOINT_URL is set.")

        return self


@lru_cache()
def get_settings() -> Settings:
    if environ.get("CODEGEN"):
        return Settings.model_construct()

    return Settings.model_validate({})
