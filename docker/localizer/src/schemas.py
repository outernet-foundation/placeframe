from enum import Enum
from uuid import UUID

from core.localization_detail import LocalizationDetail
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
    # Present only when the request asked for it.
    detail: LocalizationDetail | None = None


class LocalizationFailure(BaseModel):
    """Why one reconstruction's attempt failed, with whatever detail it got to.

    A 422 used to collapse every reconstruction's reason into one joined string, so a caller
    could not tell which id failed, why, or how close it came. This keeps them separable.
    """

    id: UUID
    error: str
    detail: LocalizationDetail | None = None
