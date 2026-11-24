from functools import lru_cache
from os import environ

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_host: str = Field()
    database_name: str = Field()
    database_orchestration_user: str = Field()
    database_orchestration_user_password: str = Field()

    lease_timeout_s: int = 1800
    lease_heartbeat_cadence_s: int = 60

    @model_validator(mode="after")
    def check_lease_timeout_covers_heartbeats(self):
        if self.lease_timeout_s < 3 * self.lease_heartbeat_cadence_s:
            raise ValueError(
                f"LEASE_TIMEOUT_S ({self.lease_timeout_s}) must be at least 3 x LEASE_HEARTBEAT_CADENCE_S "
                f"({self.lease_heartbeat_cadence_s}), so a lapsed worker is reaped only after it missed "
                "several heartbeat chances, not one."
            )

        return self


@lru_cache()
def get_settings() -> Settings:
    if environ.get("CODEGEN"):
        return Settings.model_construct()

    return Settings.model_validate({})
