from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path

import typer
from pydantic_settings import BaseSettings

from .cache import restore


# LICENSE_CACHE_TAG env pins the tag for a whole CI run; without it, each call
# re-reads "now UTC" and a run straddling midnight save/restore-misses itself.
def license_cache_tag() -> str:
    override = os.environ.get("LICENSE_CACHE_TAG")
    if override:
        return override
    return f"v-{datetime.now(UTC).strftime('%Y-%m-%d')}"


class Settings(BaseSettings):
    cache_registry: str


tag_app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


@tag_app.command()
def tag_main() -> None:
    print(license_cache_tag())


def restore_license() -> None:
    settings = Settings.model_validate({})
    license_directory = Path.home() / ".local" / "share" / "unity3d" / "Unity"
    license_directory.mkdir(parents=True, exist_ok=True)
    restore(settings.cache_registry, "unity-license", license_cache_tag(), license_directory, required=True)
