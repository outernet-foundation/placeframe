from __future__ import annotations

from pathlib import Path

import typer
from bashrun import bash
from pydantic_settings import BaseSettings

from .cache import restore, save
from .license_restore import license_cache_tag
from .setup import configure_git
from .setup_oras import install_oras


class Settings(BaseSettings):
    cache_registry: str
    github_workspace: str
    unity_email: str
    unity_password: str
    unity_serial: str


settings = Settings.model_validate({})
activate_app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


def activate(oras_push: bool) -> None:
    configure_git(settings.github_workspace)
    install_oras()

    license_directory = Path.home() / ".local" / "share" / "unity3d" / "Unity"
    license_directory.mkdir(parents=True, exist_ok=True)

    tag = license_cache_tag()
    cache_hit = False
    if oras_push:
        cache_hit = restore(settings.cache_registry, "unity-license", tag, license_directory)

    if not cache_hit:
        bash(
            f'unity-editor -batchmode -nographics -quit -serial "{settings.unity_serial}"'
            f' -username "{settings.unity_email}" -password "{settings.unity_password}" -logFile /dev/stdout'
        )

    if oras_push and not cache_hit:
        save(settings.cache_registry, "unity-license", tag, license_directory, ["Unity_lic.ulf"])


@activate_app.command()
def activate_main(oras_push: bool = typer.Option(False, help="Push activated ULF to ORAS cache")) -> None:
    activate(oras_push)
