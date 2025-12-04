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
    "reconstructing",
    "training_opq_matrix",
    "training_product_quantizer",
    "uploading",
    "succeeded",
    "failed",
]


class ReconstructionManifest(BaseModel):
    capture_id: str
    status: ReconstructionStatus
    error: Optional[str] = Field(default=None)
    options: ReconstructionOptions
    metrics: ReconstructionMetrics
