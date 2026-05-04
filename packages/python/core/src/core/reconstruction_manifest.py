from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field

from .reconstruction_metrics import ReconstructionMetrics
from .reconstruction_options import ReconstructionOptions

ReconstructionStatus = Literal[
    "queued",
    "pending",
    "downloading",
    "extracting_features",
    "matching_features",
    "training_opq_matrix",
    "training_product_quantizer",
    "verifying_geometry",
    "reconstructing",
    "uploading",
    "succeeded",
    "failed",
]


class PhaseProgress(BaseModel):
    current: int
    total: int
    attempt: int = 1


class ReconstructionManifest(BaseModel):
    capture_id: str
    status: ReconstructionStatus
    error: Optional[str] = Field(default=None)
    phase_progress: Optional[PhaseProgress] = Field(default=None)
    options: ReconstructionOptions
    metrics: ReconstructionMetrics
