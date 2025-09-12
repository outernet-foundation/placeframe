from functools import cached_property, lru_cache
from typing import TYPE_CHECKING, Any, cast

import boto3
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

if TYPE_CHECKING:
    from mypy_boto3_secretsmanager import SecretsManagerClient
else:
    SecretsManagerClient = Any


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    postgres_host: str = Field()
    postgres_admin_user: str = Field()
    postgres_admin_password_secret_arn: str = Field()

    database_name: str = Field()
    database_password_secret_arn: str = Field()

    @cached_property
    def postgres_admin_password(self) -> str:
        client = cast(SecretsManagerClient, boto3.client("secretsmanager", region_name="us-east-1"))  # type: ignore[call-arg]
        return client.get_secret_value(SecretId=self.postgres_admin_password_secret_arn)["SecretString"]

    @cached_property
    def database_password(self) -> str:
        client = cast(SecretsManagerClient, boto3.client("secretsmanager", region_name="us-east-1"))  # type: ignore[call-arg]
        return client.get_secret_value(SecretId=self.database_password_secret_arn)["SecretString"]


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
