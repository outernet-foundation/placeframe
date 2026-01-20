import shutil
import subprocess
from typing import Literal, get_args

from .run_command import run_command

Gpu = Literal["auto", "cuda", "rocm"]
GPU_TYPES = tuple(g for g in get_args(Gpu) if g != "auto")


def detect_gpu() -> Gpu:
    if shutil.which("nvidia-smi"):
        try:
            run_command("nvidia-smi", stream_log=False, log=False, verbose_errors=False)
            return "cuda"
        except subprocess.CalledProcessError:
            pass
    if shutil.which("rocminfo"):
        try:
            run_command("rocminfo", stream_log=False, log=False, verbose_errors=False)
            return "rocm"
        except subprocess.CalledProcessError:
            pass
    raise RuntimeError("Could not detect GPU type.")
