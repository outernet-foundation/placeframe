from enum import Enum
from uuid import UUID

from core.localization_metrics import LocalizationMetrics
from core.transform import Transform
from pydantic import BaseModel


class LoadState(str, Enum):
    PENDING = "pending"
    LOADING = "loading"
    READY = "ready"
    FAILED = "failed"


class LoadStateResponse(BaseModel):
    status: LoadState
    error: str | None = None


class Localization(BaseModel):
    id: UUID
    transform: Transform
    metrics: LocalizationMetrics
