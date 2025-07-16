from functools import lru_cache
from typing import Optional

from pydantic import AnyHttpUrl, PostgresDsn, ValidationError, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_dsn: PostgresDsn
    piccolo_admin_user: str
    piccolo_admin_password: str
    s3_endpoint_url: Optional[AnyHttpUrl] = None
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None

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
    try:
        return Settings()  # type: ignore[return-value]]
    except ValidationError as e:
        print("Invalid configuration:", e)
        raise
