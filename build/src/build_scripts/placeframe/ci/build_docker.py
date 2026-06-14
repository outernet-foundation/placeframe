from __future__ import annotations

import shlex
from typing import Literal

import typer
from placeframe_bash import bash
from placeframe_stack.detect_gpu import Gpu
from pydantic_settings import BaseSettings

from placeframe_unity.ci_step import ci_step
from placeframe_unity.setup import configure_git, free_disk_space
from placeframe_stack.build_docker import run_build

Variant = Literal["common", "cuda", "rocm"]


class Settings(BaseSettings):
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
            "alloy",
            "api",
            "auth-initializer",
            "create-database",
            "database-migrator",
            "gateway",
            "grafana",
            "initialize-cloudbeaver",
            "lease-server",
            "loki",
            "postgres",
            "rathole-client",
        ]
    )

    with ci_step(f"Build images ({variant})"):
        run_build(mode="ci", gpu=gpu, targets_opt=targets)
