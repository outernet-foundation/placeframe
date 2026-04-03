from __future__ import annotations

import os
import shlex
from typing import Literal

import typer
from common.bash import bash
from common.detect_gpu import Gpu
from pydantic_settings import BaseSettings

from ...shared.ci_step import ci_step
from ...shared.setup import configure_git, free_disk_space
from ..build_docker import build

Variant = Literal["common", "cuda", "rocm"]


class Settings(BaseSettings):
    github_repository: str
    github_workspace: str
    github_actor: str
    github_token: str


settings = Settings.model_validate({})

ci_app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


@ci_app.command()
def ci_main(variant: Variant = typer.Option(help="Build variant: common, cuda, or rocm")) -> None:
    with ci_step("Setup"):
        configure_git(settings.github_workspace)
        free_disk_space(large_packages=True, docker_images=True, swap_storage=True)
        os.environ["GHCR_REPO"] = settings.github_repository.lower()

    with ci_step("Create builder and login"):
        bash("docker buildx create --use --driver docker-container")
        bash(
            f"docker login ghcr.io -u {shlex.quote(settings.github_actor)} --password-stdin",
            stdin_text=settings.github_token,
        )

    gpu: Gpu = variant if variant != "common" else "cuda"
    targets = (
        [f"localizer-{variant}", f"reconstructor-{variant}"]
        if variant != "common"
        else [
            "api",
            "auth-initializer",
            "create-database",
            "gateway",
            "initialize-cloudbeaver",
            "migrate-database",
            "state-sync",
        ]
    )

    with ci_step(f"Build images ({variant})"):
        build(upgrade=False, lock_only=False, mode="ci", gpu=gpu, no_cache=False, targets_opt=targets)
