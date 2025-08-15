from functools import lru_cache

from pydantic import AnyHttpUrl, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_user: str | None = None
    postgres_password: str | None = None
    postgres_host: str | None = None
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

        return self


@lru_cache()
def get_settings() -> Settings:
    return Settings()
