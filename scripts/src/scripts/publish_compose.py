from __future__ import annotations

import os
import re
import shlex
from pathlib import Path
from tempfile import TemporaryDirectory

import typer
from bashrun.bash import bash
from pydantic_settings import BaseSettings

from docker_devkit.config import load_config
from docker_devkit.documents import compute_service_shas, parse_bake
from docker_devkit.image_refs import resolve_remote_digest
from docker_devkit.lifecycle import require_manifest
from docker_devkit.score_generate import compose_seams

REGISTRY = "ghcr.io/outernet-foundation/placeframe"

_VAR_PATTERN = re.compile(r"\$\{([A-Z_][A-Z0-9_]*)(:[?\-+][^}]*)?\}")
_PLACEFRAME_IMAGE_PATTERN = re.compile(rf"{re.escape(REGISTRY)}/[a-z0-9][a-z0-9-]*:[^\s\"'@$]+")

ci_app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


class Settings(BaseSettings):
    github_actor: str
    github_token: str
    github_sha: str
    branch_name: str


@ci_app.command()
def ci_main() -> None:
    settings = Settings.model_validate({})
    print("Login to ghcr")
    bash(
        f"docker login ghcr.io -u {shlex.quote(settings.github_actor)} --password-stdin",
        stdin_text=settings.github_token,
    )

    print("Resolve interpolation env")
    # Stub consumer-facing vars so docker compose publish's ${VAR:?err}
    # check passes. Our bake step doesn't read os.environ, so these stubs
    # never reach the baked YAML — consumer vars ship as holes.
    for key, value in _load_env_file(Path(".env.sample")).items():
        os.environ.setdefault(key, value)

    config = load_config(Path.cwd())
    if config is None or config.generate_score is None:
        raise RuntimeError("publish-compose needs a generate-score section in docker-devkit.yaml")

    substitutions = {
        **compute_service_shas(Path.cwd(), parse_bake(require_manifest(Path.cwd()))),
        **_load_env_file(Path("workloads/images.lock")),
    }
    digests: dict[str, str] = {}

    for seam in compose_seams(config.generate_score):
        source = Path.cwd() / seam.output
        with TemporaryDirectory(prefix="placeframe-publish-") as baked_directory_string:
            print(f"Bake {source.as_posix()} as placeframe-{seam.name}")
            baked = Path(baked_directory_string) / source.name
            baked.write_text(
                pin_references(substitute_holes(source.read_text(encoding="utf-8"), substitutions), digests),
                encoding="utf-8",
            )

            tags = (settings.github_sha, settings.branch_name.replace("/", "-"))
            for tag in tags:
                reference = f"{REGISTRY}/placeframe-{seam.name}:{tag}"
                print(f"Publish {reference}")
                bash(f"docker compose -f {shlex.quote(baked.as_posix())} publish {shlex.quote(reference)} --yes")


def substitute_holes(text: str, substitutions: dict[str, str]) -> str:
    # Substitute placeframe-internal vars so consumer interpolation can't trip on
    # them; --resolve-image-digests applies its override too late (after
    # interpolation has already failed). Consumer passthroughs stay unmatched and
    # ride through as holes.
    def substitute(match: re.Match[str]) -> str:
        return substitutions.get(match.group(1), match.group(0))

    return _VAR_PATTERN.sub(substitute, text)


def pin_references(text: str, digests: dict[str, str]) -> str:
    matches = list(_PLACEFRAME_IMAGE_PATTERN.finditer(text))
    if not matches:
        return text
    parts: list[str] = []
    cursor = 0
    for match in matches:
        parts.append(text[cursor : match.start()])
        parts.append(_pin_reference(match.group(0), digests))
        cursor = match.end()
    parts.append(text[cursor:])
    return "".join(parts)


def _pin_reference(reference: str, digests: dict[str, str]) -> str:
    if reference not in digests:
        digests[reference] = resolve_remote_digest(reference)
    repository = reference.rsplit(":", 1)[0]
    return f"{repository}@{digests[reference]}"


def _load_env_file(path: Path) -> dict[str, str]:
    return {
        (parts := line.split("=", 1))[0].strip(): parts[1].strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if "=" in line and not line.lstrip().startswith("#")
    }
