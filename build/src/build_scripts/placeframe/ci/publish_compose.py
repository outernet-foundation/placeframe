from __future__ import annotations

import os
import re
import shlex
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Literal

import typer
import yaml
from bashrun.bash import bash
from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings

from ci_devkit.ci_step import ci_step
from ci_devkit.setup import configure_git
from docker_devkit.context_sha import compute_service_shas
from docker_devkit.documents import parse_bake
from docker_devkit.image_refs import resolve_remote_digest
from docker_devkit.lifecycle import require_manifest

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


class ComposeConfig(BaseModel):
    model_config = ConfigDict(extra="allow")

    file: str | None = None


class ComposeDocument(BaseModel):
    model_config = ConfigDict(extra="allow")

    configs: dict[str, ComposeConfig] | None = None


ci_app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


@ci_app.command()
def ci_main(variant: Variant = typer.Option(help="Publish variant: cuda or rocm")) -> None:
    settings = Settings.model_validate({})
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
                **compute_service_shas(Path.cwd(), parse_bake(require_manifest(Path.cwd()))),
                **_load_env_file(Path("workloads/images.lock")),
            }

            def substitute(match: re.Match[str]) -> str:
                return substitutions.get(match.group(1), match.group(0))

            for source_name in source_names:
                baked_text = _VAR_PATTERN.sub(substitute, Path(source_name).read_text(encoding="utf-8"))
                (baked_directory / source_name).write_text(baked_text, encoding="utf-8")
            compose_files = " ".join(f"-f {shlex.quote(str(baked_directory / name))}" for name in source_names)

        with ci_step("Inline configs content"):
            # The published artifact is YAML-only: file-sourced configs dangle in
            # the include consumer's materialization cache, so they ride as inline
            # content. Literal $ doubles to $$ so the consumer's compose parse
            # leaves env expansion to the container (loki -config.expand-env)
            # instead of interpolating values at include time.
            for source_name in source_names:
                _inline_configs(baked_directory / source_name)

        with ci_step("Pin placeframe service image digests"):
            digests: dict[str, str] = {}
            for source_name in source_names:
                baked_path = baked_directory / source_name
                baked_path.write_text(
                    _pin_references(baked_path.read_text(encoding="utf-8"), digests), encoding="utf-8"
                )

        sha_tag = f"{REGISTRY}/placeframe-{variant}:{settings.github_sha}"
        with ci_step(f"Publish {sha_tag}"):
            bash(f"docker compose {compose_files} publish {shlex.quote(sha_tag)} --yes")

        branch_tag = f"{REGISTRY}/placeframe-{variant}:{settings.branch_name.replace('/', '-')}"
        with ci_step(f"Publish {branch_tag}"):
            bash(f"docker compose {compose_files} publish {shlex.quote(branch_tag)} --yes")


def _pin_references(text: str, digests: dict[str, str]) -> str:
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


def _inline_configs(baked_path: Path) -> None:
    document = yaml.safe_load(baked_path.read_text(encoding="utf-8"))
    parsed = ComposeDocument.model_validate(document)
    if parsed.configs is None:
        return
    inlined: dict[str, dict[str, Any]] = {}
    for name, config in parsed.configs.items():
        if config.file is None:
            continue
        entry = config.model_dump(exclude_defaults=True)
        entry.pop("file", None)
        entry["content"] = Path(config.file).read_text(encoding="utf-8").replace("$", "$$")
        inlined[name] = entry
    document["configs"] = inlined
    baked_path.write_text(
        yaml.dump(document, default_flow_style=False, sort_keys=False, width=1_000_000),
        encoding="utf-8",
    )
