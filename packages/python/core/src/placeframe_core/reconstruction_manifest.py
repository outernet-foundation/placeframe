from __future__ import annotations

from pydantic import BaseModel

from .reconstruction_metrics import ReconstructionMetrics
from .reconstruction_options import ReconstructionOptions


MANIFEST_VERSION = 1


class Manifest(BaseModel):
    options: ReconstructionOptions
    metrics: ReconstructionMetrics
