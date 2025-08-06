from functools import lru_cache
from typing import TYPE_CHECKING, Any, cast

import boto3

if TYPE_CHECKING:
    from mypy_boto3_secretsmanager import SecretsManagerClient
else:
    SecretsManagerClient = Any

from pydantic import AnyHttpUrl, PostgresDsn, ValidationError, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_dsn: PostgresDsn | None = None
    postgres_dsn_arn: str | None = None
    s3_endpoint_url: AnyHttpUrl | None = None
    s3_access_key: str | None = None
    s3_secret_key: str | None = None

    class Config:
        env_file = ".env"

    @model_validator(mode="after")
    def check_storage_config(self):
        using_minio = self.s3_endpoint_url is not None
        creds_provided = self.s3_access_key and self.s3_secret_key

        if using_minio and not creds_provided:
            raise ValueError(
                "S3_ACCESS_KEY and S3_SECRET_KEY are required when S3_ENDPOINT_URL is set."
            )

        if self.postgres_dsn and self.postgres_dsn_arn:
            raise ValueError(
                "Only one of POSTGRES_DSN or POSTGRES_DSN_ARN should be set."
            )
        if not self.postgres_dsn and not self.postgres_dsn_arn:
            raise ValueError("One of POSTGRES_DSN or POSTGRES_DSN_ARN must be set.")

        # test
        return self


@lru_cache()
def get_settings() -> Settings:
    try:
        print("Loading settings...")
        settings = Settings()
        print("Settings loaded successfully.")

        if settings.postgres_dsn_arn:
            print("Fetching Postgres DSN from Secrets Manager...")
            print(settings.postgres_dsn_arn)
            client: SecretsManagerClient = boto3.client("secretsmanager")  # type: ignore
            print("Client created, fetching secret...")
            response = client.get_secret_value(SecretId=settings.postgres_dsn_arn)
            print("Secret fetched successfully.")
            settings.postgres_dsn = cast(PostgresDsn, response.get("SecretString"))
            print("Postgres DSN set from Secrets Manager.")

        return settings
    except ValidationError as e:
        print("Invalid configuration:", e)
        raise
