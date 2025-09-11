from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    postgres_host: str = Field()
    postgres_port: int = Field()
    postgres_admin_user: str = Field()
    postgres_admin_password: str = Field()

    cloudbeaver_url: AnyHttpUrl = Field()
    cloudbeaver_admin_user: str = Field()
    cloudbeaver_admin_password: str = Field()

    database_name: str = Field()
    database_password: str = Field()


@lru_cache()
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
