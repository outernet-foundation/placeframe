from functools import lru_cache
from os import environ

from pydantic import AnyHttpUrl, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_parse_none_str="")

    public_url: AnyHttpUrl = Field()

    auth_issuer_url: AnyHttpUrl | None = None
    auth_jwks_url: AnyHttpUrl | None = None
    auth_authorization_endpoint: AnyHttpUrl | None = None
    auth_token_endpoint: AnyHttpUrl | None = None
    auth_audience: str | None = None

    postgres_host: str = Field()
    database_name: str = Field()
    database_api_user: str = Field()
    database_api_user_password: str = Field()
    database_auth_user: str = Field()
    database_auth_user_password: str = Field()
    database_orchestration_user: str = Field()
    database_orchestration_user_password: str = Field()

    s3_endpoint_url: AnyHttpUrl | None = None
    s3_access_key: str | None = None
    s3_secret_key: str | None = None

    localizer_container_url: AnyHttpUrl = Field()
    loki_url: AnyHttpUrl = Field()

    reconstructions_bucket: str = Field(...)

    @model_validator(mode="after")
    def check_storage_config(self):
        using_s3 = self.s3_endpoint_url is not None
        creds_provided = self.s3_access_key and self.s3_secret_key

        if using_s3 and not creds_provided:
            raise ValueError("S3_ACCESS_KEY and S3_SECRET_KEY are required when S3_ENDPOINT_URL is set.")

        return self

    @model_validator(mode="after")
    def check_auth_config(self):
        if self.auth_issuer_url is None:
            present = [
                name
                for name, value in (
                    ("auth_jwks_url", self.auth_jwks_url),
                    ("auth_authorization_endpoint", self.auth_authorization_endpoint),
                    ("auth_token_endpoint", self.auth_token_endpoint),
                )
                if value is not None
            ]
            if present:
                raise ValueError(f"AUTH_ISSUER_URL is unset (anonymous mode) but endpoint URLs are set: {present}")

            return self

        missing = [
            name
            for name, value in (
                ("auth_jwks_url", self.auth_jwks_url),
                ("auth_authorization_endpoint", self.auth_authorization_endpoint),
                ("auth_token_endpoint", self.auth_token_endpoint),
            )
            if value is None
        ]
        if missing:
            raise ValueError(f"AUTH_ISSUER_URL is set (keycloak mode) and requires: {missing}")

        if self.public_url.scheme == "http":
            raise ValueError(
                "AUTH_ISSUER_URL is set but PUBLIC_URL is cleartext http; OAuth must not travel unencrypted."
            )

        self.auth_audience = self.auth_audience or "placeframe-api"

        return self


@lru_cache()
def get_settings() -> Settings:
    if environ.get("CODEGEN"):
        return Settings.model_construct()

    return Settings.model_validate({})
