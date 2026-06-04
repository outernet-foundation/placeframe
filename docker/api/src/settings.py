from functools import lru_cache
from os import environ
from typing import Literal

from pydantic import AnyHttpUrl, Field, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    public_url: AnyHttpUrl = Field()

    auth_mode: Literal["keycloak", "disabled"] = "keycloak"
    auth_audience: str | None = None
    auth_issuer_url: AnyHttpUrl | None = None
    auth_url: AnyHttpUrl | None = None
    auth_token_url: AnyHttpUrl | None = None
    auth_certs_url: AnyHttpUrl | None = None

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
    loki_url: AnyHttpUrl = Field()

    reconstructions_bucket: str = Field(...)

    @model_validator(mode="after")
    def check_storage_config(self):
        using_minio = self.minio_endpoint_url is not None
        creds_provided = self.minio_access_key and self.minio_secret_key

        if using_minio and not creds_provided:
            raise ValueError("MINIO_ACCESS_KEY and MINIO_SECRET_KEY are required when MINIO_ENDPOINT_URL is set.")

        return self

    @model_validator(mode="after")
    def check_auth_config(self):
        if self.auth_mode == "keycloak":
            missing = [
                name
                for name, value in (
                    ("auth_audience", self.auth_audience),
                    ("auth_issuer_url", self.auth_issuer_url),
                    ("auth_url", self.auth_url),
                    ("auth_token_url", self.auth_token_url),
                    ("auth_certs_url", self.auth_certs_url),
                )
                if value is None
            ]
            if missing:
                raise ValueError(f"AUTH_MODE=keycloak requires: {missing}")

        return self


@lru_cache()
def get_settings() -> Settings:
    if environ.get("CODEGEN"):
        return Settings.model_construct()

    return Settings.model_validate({})
