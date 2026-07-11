from __future__ import annotations

import os
import platform
import shlex
import shutil
from pathlib import Path

from bashrun import bash
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    github_token: str
    github_actor: str = ""
    github_path: str | None = None
    runner_temp: str = "."


def install_oras(version: str = "1.2.2") -> None:
    settings = Settings.model_validate({})
    system = platform.system()
    sudo = system == "Linux" and os.geteuid() != 0
    prefix = "sudo " if sudo else ""

    if system == "Linux":
        bash(f"{prefix}apt-get update -qq")
        bash(f"{prefix}apt-get install -y -qq zstd")
    elif system == "Windows":
        bash("choco install zstandard -y --no-progress")

    if system == "Linux":
        archive = f"oras_{version}_linux_amd64.tar.gz"
        bash(f"curl -fsSLO https://github.com/oras-project/oras/releases/download/v{version}/{archive}")
        bash(f"{prefix}tar -xzf {archive} -C /usr/local/bin/ oras")
        Path(archive).unlink()
    elif system == "Windows":
        archive = f"oras_{version}_windows_amd64.zip"
        oras_directory = Path(settings.runner_temp) / "oras"
        bash(f"curl -fsSLO https://github.com/oras-project/oras/releases/download/v{version}/{archive}")
        shutil.unpack_archive(archive, oras_directory)
        Path(archive).unlink()
        os.environ["PATH"] = f"{oras_directory}{os.pathsep}{os.environ['PATH']}"
        if settings.github_path:
            with open(settings.github_path, "a") as file:
                file.write(f"{oras_directory}\n")

    bash(
        f"oras login ghcr.io --username {shlex.quote(settings.github_actor)} --password-stdin",
        stdin_text=settings.github_token,
    )
