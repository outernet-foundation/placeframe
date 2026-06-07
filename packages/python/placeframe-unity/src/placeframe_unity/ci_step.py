from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    github_step_summary: str | None = None


settings = Settings.model_validate({})
_summary_initialized = False


def _format_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = int(seconds // 60)
    remaining = seconds % 60
    return f"{minutes}m {remaining:.0f}s"


def _write_summary(label: str, duration: float, *, failed: bool) -> None:
    global _summary_initialized
    summary_path = settings.github_step_summary
    if not summary_path:
        return
    with open(summary_path, "a") as file:
        if not _summary_initialized:
            file.write("| Step | Duration |\n|---|---|\n")
            _summary_initialized = True
        status = " :x:" if failed else ""
        file.write(f"| {label}{status} | {_format_duration(duration)} |\n")


@contextmanager
def ci_step(label: str) -> Iterator[None]:
    print(f"::group::{label}", flush=True)
    start = time.monotonic()
    failed = False
    try:
        yield
    except BaseException:
        failed = True
        raise
    finally:
        duration = time.monotonic() - start
        print("::endgroup::", flush=True)
        _write_summary(label, duration, failed=failed)
