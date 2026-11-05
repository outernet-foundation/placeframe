"""The fusion algorithms, by name. `make("kalman:gate_chi2=30,slew_s=1")` builds one from a spec.

To try a new algorithm, add a module with a class that has the Fusion methods (base.py) and register
it in ALGORITHMS with its parameters dataclass (or None if it takes keyword arguments directly).
"""

from __future__ import annotations

from dataclasses import fields
from typing import Any

from .base import Decision, Fusion, measurement_alignment
from .kalman import Kalman, KalmanParams
from .snap import Snap
from .window import Window, WindowParams

ALGORITHMS: dict[str, tuple[type, type | None]] = {
    "kalman": (Kalman, KalmanParams),
    "snap": (Snap, None),
    "window": (Window, WindowParams),
}


def _value(text: str) -> Any:
    if text.lower() in ("true", "false"):
        return text.lower() == "true"
    for kind in (int, float):
        try:
            return kind(text)
        except ValueError:
            pass
    return text


def parse(spec: str) -> tuple[str, dict[str, Any]]:
    """ "kalman:gate_chi2=30,slew_s=1" -> ("kalman", {"gate_chi2": 30, "slew_s": 1})."""
    name, _, rest = spec.partition(":")
    settings = {}
    for item in filter(None, rest.split(",")):
        key, _, value = item.partition("=")
        settings[key.strip()] = _value(value.strip())
    return name, settings


def make(spec: str, label: str | None = None) -> Fusion:
    name, settings = parse(spec)
    if name not in ALGORITHMS:
        raise ValueError(f"Unknown algorithm {name!r}; have {', '.join(ALGORITHMS)}")
    cls, params_cls = ALGORITHMS[name]
    if params_cls is None:
        algorithm = cls(**settings)
    else:
        known = {f.name for f in fields(params_cls)}
        unknown = set(settings) - known
        if unknown:
            raise ValueError(f"{name} has no parameter {', '.join(sorted(unknown))}; has {', '.join(sorted(known))}")
        algorithm = cls(params_cls(**settings))
    algorithm.name = label or spec
    return algorithm


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
