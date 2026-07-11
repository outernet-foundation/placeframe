import shutil
from typing import Literal, get_args

from bashrun import bash_check

Gpu = Literal["auto", "cuda", "rocm", "none"]
GPU_TYPES = tuple(g for g in get_args(Gpu) if g not in ("auto", "none"))


def detect_gpu() -> Gpu:
    if shutil.which("nvidia-smi") and bash_check("nvidia-smi"):
        return "cuda"
    if shutil.which("rocminfo") and bash_check("rocminfo"):
        return "rocm"
    raise RuntimeError("Could not detect GPU type.")
