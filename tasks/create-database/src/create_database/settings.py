from functools import cached_property, lru_cache
from typing import TYPE_CHECKING, Any, cast

import boto3
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

if TYPE_CHECKING:
    from mypy_boto3_secretsmanager import SecretsManagerClient
else:
    SecretsManagerClient = Any


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    backend: str = Field()
    cloudbeaver_service_id: str = Field()

    postgres_host: str
    postgres_admin_user: str
    postgres_admin_password_plaintext: str | None = Field(default=None, validation_alias="POSTGRES_ADMIN_PASSWORD")
    postgres_admin_password_secret_arn: str | None = Field(
        default=None, validation_alias="POSTGRES_ADMIN_PASSWORD_SECRET_ARN"
    )

    database_name: str
    database_password_plaintext: str | None = Field(default=None, validation_alias="DATABASE_PASSWORD")
    database_password_secret_arn: str | None = Field(default=None, validation_alias="DATABASE_PASSWORD_SECRET_ARN")

    @model_validator(mode="after")
    def _validate_password_sources(self) -> "Settings":
        admin_plain = bool(self.postgres_admin_password_plaintext)
        db_plain = bool(self.database_password_plaintext)
        admin_arn = bool(self.postgres_admin_password_secret_arn)
        db_arn = bool(self.database_password_secret_arn)

        # All-plaintext
        if admin_plain and db_plain and not (admin_arn or db_arn):
            return self
        # All-ARNs
        if admin_arn and db_arn and not (admin_plain or db_plain):
            return self

        raise ValueError(
            "Provide either BOTH plaintext passwords "
            "(POSTGRES_ADMIN_PASSWORD and DATABASE_PASSWORD) "
            "OR BOTH secret ARNs "
            "(POSTGRES_ADMIN_PASSWORD_SECRET_ARN and DATABASE_PASSWORD_SECRET_ARN). "
            "Do not mix sources."
        )

    # Resolved, non-optional values for the rest of the app:
    @cached_property
    def postgres_admin_password(self) -> str:
        if self.postgres_admin_password_plaintext:
            return self.postgres_admin_password_plaintext
        client = cast(SecretsManagerClient, boto3.client("secretsmanager", region_name="us-east-1"))  # type: ignore[call-arg]
        return cast(
            str,
            client.get_secret_value(
                SecretId=self.postgres_admin_password_secret_arn  # type: ignore[arg-type]
            )["SecretString"],
        )

    @cached_property
    def database_password(self) -> str:
        if self.database_password_plaintext:
            return self.database_password_plaintext
        client = cast(SecretsManagerClient, boto3.client("secretsmanager", region_name="us-east-1"))  # type: ignore[call-arg]
        return cast(
            str,
            client.get_secret_value(
                SecretId=self.database_password_secret_arn  # type: ignore[arg-type]
            )["SecretString"],
        )


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
