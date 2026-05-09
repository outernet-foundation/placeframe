from functools import lru_cache

from pydantic import AnyHttpUrl, Field, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    api_internal_url: AnyHttpUrl = Field()
    auth_token_url: AnyHttpUrl = Field()
    auth_client_id: str = Field()
    private_key_path: str = Field()

    minio_endpoint_url: AnyHttpUrl | None = None
    minio_access_key: str | None = None
    minio_secret_key: str | None = None
    captures_bucket: str = Field()
    reconstructions_bucket: str = Field()

    @model_validator(mode="after")
    def check_storage_config(self):
        using_minio = self.minio_endpoint_url is not None
        creds_provided = self.minio_access_key and self.minio_secret_key

        if using_minio and not creds_provided:
            raise ValueError("MINIO_ACCESS_KEY and MINIO_SECRET_KEY are required when MINIO_ENDPOINT_URL is set.")
        return self


@lru_cache()
def get_settings() -> Settings:
    return Settings.model_validate({})
