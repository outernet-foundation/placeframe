from __future__ import annotations

import os
import re
import shlex
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal

import typer
from common.bash import bash, bash_output
from pydantic_settings import BaseSettings

from ...shared.ci_step import ci_step
from ...shared.setup import configure_git
from ..context_sha import compute_service_shas

Variant = Literal["cuda", "rocm"]

REGISTRY = "ghcr.io/outernet-foundation/placeframe"

_VAR_PATTERN = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)(:[?\-+][^}]*)?\}")
_PLACEFRAME_IMAGE_PATTERN = re.compile(rf"{re.escape(REGISTRY)}/[a-z0-9][a-z0-9-]*:[^\s\"'@$]+")


class Settings(BaseSettings):
    github_workspace: str
    github_actor: str
    github_token: str
    github_sha: str
    branch_name: str


settings = Settings.model_validate({})

ci_app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


@ci_app.command()
def ci_main(variant: Variant = typer.Option(help="Publish variant: cuda or rocm")) -> None:
    with ci_step("Setup"):
        configure_git(settings.github_workspace)

    with ci_step("Login to ghcr"):
        bash(
            f"docker login ghcr.io -u {shlex.quote(settings.github_actor)} --password-stdin",
            stdin_text=settings.github_token,
        )

    with ci_step("Resolve interpolation env"):
        # Stub consumer-facing vars so docker compose publish's ${VAR:?err}
        # check passes. Our bake step doesn't read os.environ, so these stubs
        # never reach the baked YAML — consumer vars ship as literals.
        for key, value in _load_env_file(Path(".env.sample")).items():
            os.environ.setdefault(key, value)

    source_names = ("compose.yml", "compose.postgres.yml", f"compose.{variant}.yml")

    with TemporaryDirectory(prefix="placeframe-publish-") as baked_directory_string:
        baked_directory = Path(baked_directory_string)

        with ci_step("Bake compose YAML"):
            # Substitute placeframe-internal vars so consumer interpolation
            # can't trip on them. --resolve-image-digests applies its override
            # too late (after interpolation has already failed).
            substitutions = {
                **compute_service_shas(Path.cwd(), Path("compose.bake.yml")),
                **_load_env_file(Path(".env.lock")),
            }

            def substitute(match: re.Match[str]) -> str:
                return substitutions.get(match.group(1), match.group(0))

            for source_name in source_names:
                baked_text = _VAR_PATTERN.sub(substitute, Path(source_name).read_text(encoding="utf-8"))
                (baked_directory / source_name).write_text(baked_text, encoding="utf-8")
            compose_files = " ".join(f"-f {shlex.quote(str(baked_directory / name))}" for name in source_names)

        with ci_step("Pin placeframe service image digests"):
            digests: dict[str, str] = {}

            def resolve(match: re.Match[str]) -> str:
                reference = match.group(0)
                if reference not in digests:
                    output = bash_output(f"docker buildx imagetools inspect {shlex.quote(reference)}")
                    digest_match = re.search(r"^Digest:\s+(sha256:[a-f0-9]+)", output, re.MULTILINE)
                    if digest_match is None:
                        raise RuntimeError(
                            f"Could not parse manifest digest from `docker buildx imagetools inspect {reference}`"
                        )
                    digests[reference] = digest_match.group(1)
                repository = reference.rsplit(":", 1)[0]
                return f"{repository}@{digests[reference]}"

            for source_name in source_names:
                baked_path = baked_directory / source_name
                baked_path.write_text(
                    _PLACEFRAME_IMAGE_PATTERN.sub(resolve, baked_path.read_text(encoding="utf-8")),
                    encoding="utf-8",
                )

        sha_tag = f"{REGISTRY}/placeframe-{variant}:{settings.github_sha}"
        with ci_step(f"Publish {sha_tag}"):
            bash(f"docker compose {compose_files} publish {shlex.quote(sha_tag)} --yes")

        branch_tag = f"{REGISTRY}/placeframe-{variant}:{settings.branch_name.replace('/', '-')}"
        with ci_step(f"Publish {branch_tag}"):
            bash(f"docker compose {compose_files} publish {shlex.quote(branch_tag)} --yes")


def _load_env_file(path: Path) -> dict[str, str]:
    return {
        (parts := line.split("=", 1))[0].strip(): parts[1].strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if "=" in line and not line.lstrip().startswith("#")
    }
