"""The fusion algorithms, by name. `make("kalman:gate_chi2=30,slew_s=1")` builds one from a spec.

To try a new algorithm, add a module with a class that has the Fusion methods (base.py) and register
it in ALGORITHMS (registry.py) with its parameters dataclass (or None if it takes keyword arguments directly).
"""

from __future__ import annotations

from .base import Decision, Fusion, measurement_alignment
from .kalman import Kalman, KalmanParams
from .registry import ALGORITHMS, make, parse
from .snap import Snap
from .window import Window, WindowParams

__all__ = [
    "ALGORITHMS",
    "Decision",
    "Fusion",
    "Kalman",
    "KalmanParams",
    "Snap",
    "Window",
    "WindowParams",
    "make",
    "measurement_alignment",
    "parse",
]
