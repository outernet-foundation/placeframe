from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    backend: Literal["aws", "docker"]
    capture_id: str
    batch_job_array_index: str = Field(
        validation_alias=AliasChoices(
            "BATCH_JOB_ARRAY_INDEX",
            "AWS_BATCH_JOB_ARRAY_INDEX",
        )
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore
