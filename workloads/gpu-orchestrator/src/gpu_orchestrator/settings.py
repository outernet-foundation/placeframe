from __future__ import annotations

from logging import getLogger
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

IDLE_WINDOW_FLOOR_S = 60
POLL_INTERVAL_FLOOR_S = 5

logger = getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_parse_none_str="", populate_by_name=True)

    gpu_contended: bool = True
    idle_window_s: int = Field(default=600, validation_alias="GPU_IDLE_WINDOW_S")
    poll_interval_s: int = Field(default=15, validation_alias="GPU_POLL_INTERVAL_S")
    retry_after_s: int = Field(default=60, validation_alias="GPU_RETRY_AFTER_SECONDS")
    compose_project: str = Field(validation_alias="COMPOSE_PROJECT_NAME")
    lease_server_url: str = Field(validation_alias="LEASE_SERVER_URL")
    localizer_url: str = Field(validation_alias="LOCALIZER_URL")

    # A bad timer must not brick the GPU (Q5/Q8): boot values below the floors clamp
    # with an Error log; runtime mutation below the floors is a hard 400 instead
    @model_validator(mode="after")
    def clamp_timer_floors(self) -> Self:
        if self.idle_window_s < IDLE_WINDOW_FLOOR_S:
            logger.error(
                "GPU_IDLE_WINDOW_S=%d below floor %d; clamping to the floor", self.idle_window_s, IDLE_WINDOW_FLOOR_S
            )
            self.idle_window_s = IDLE_WINDOW_FLOOR_S
        if self.poll_interval_s < POLL_INTERVAL_FLOOR_S:
            logger.error(
                "GPU_POLL_INTERVAL_S=%d below floor %d; clamping to the floor",
                self.poll_interval_s,
                POLL_INTERVAL_FLOOR_S,
            )
            self.poll_interval_s = POLL_INTERVAL_FLOOR_S
        return self
