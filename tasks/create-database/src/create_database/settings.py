from __future__ import annotations

from functools import cached_property, lru_cache
from typing import Literal

from common.boto_clients import create_secretsmanager_client
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    backend: Literal["aws", "docker"] = Field()
    cloudbeaver_service_id: str = Field()
    ecs_cluster_arn: str | None = Field(default=None)

    postgres_host: str
    postgres_admin_user: str
    postgres_admin_password_plaintext: str | None = Field(default=None, validation_alias="POSTGRES_ADMIN_PASSWORD")
    postgres_admin_password_secret_arn: str | None = Field(default=None)

    database_name: str
    database_password_plaintext: str | None = Field(default=None, validation_alias="DATABASE_PASSWORD")
    database_password_secret_arn: str | None = Field(default=None)

    @model_validator(mode="after")
    def _validate_backend(self) -> Settings:
        if self.backend == "aws":
            if not self.postgres_admin_password_secret_arn:
                raise ValueError("POSTGRES_ADMIN_PASSWORD_SECRET_ARN must be set when backend='aws'.")
            if not self.database_password_secret_arn:
                raise ValueError("DATABASE_PASSWORD_SECRET_ARN must be set when backend='aws'.")
            if not self.ecs_cluster_arn:
                raise ValueError("ecs_cluster_arn and cloudbeaver_service_id must be set when backend='aws'.")

        if self.backend == "docker":
            if not self.postgres_admin_password_plaintext:
                raise ValueError("POSTGRES_ADMIN_PASSWORD must be set when backend='docker'.")
            if not self.database_password_plaintext:
                raise ValueError("DATABASE_PASSWORD must be set when backend='docker'.")

        return self

    @cached_property
    def postgres_admin_password(self) -> str:
        if self.postgres_admin_password_plaintext:
            return self.postgres_admin_password_plaintext

        client = create_secretsmanager_client()
        assert self.postgres_admin_password_secret_arn is not None
        return client.get_secret_value(SecretId=self.postgres_admin_password_secret_arn)["SecretString"]

    @cached_property
    def database_password(self) -> str:
        if self.database_password_plaintext:
            return self.database_password_plaintext

        assert self.database_password_secret_arn is not None
        client = create_secretsmanager_client()
        return client.get_secret_value(SecretId=self.database_password_secret_arn)["SecretString"]


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
