from __future__ import annotations

import json
import os
from pathlib import Path

import typer
from bashrun import bash, bash_output

from unity_buildkit.ci_step import ci_step
from stack_lifecycle.context_sha import compute_service_shas
from stack_lifecycle.image_refs import VersionCoupling, VersionSite, unpinned_references, version_coupling_violations
from ..lock_python import lock_python

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)

VERSION_COUPLINGS = [
    VersionCoupling(
        name="uv",
        pyproject_key="tool.uv.required-version",
        sites=(VersionSite("uv base tag", "compose*.bake.yml", r"uv:([^@]+?)-", "UV_BASE_DIGEST"),),
    ),
    VersionCoupling(
        name="python",
        pyproject_key="project.requires-python",
        sites=(
            VersionSite("uv base python component", "compose*.bake.yml", r"python([0-9][0-9.]*)", "UV_BASE_DIGEST"),
            VersionSite("python base tag", "compose.zed.bake.yml", r"python:([0-9][0-9.]*)", "PYTHON_BASE_DIGEST"),
            VersionSite("uv python install", "docker/zed-capture/Dockerfile", r"uv python install ([0-9][0-9.]*)"),
        ),
    ),
]


@app.command()
def main() -> None:
    with ci_step("Check image references"):
        if unpinned := unpinned_references(Path.cwd()):
            raise SystemExit(f"Unpinned image references (need tag or digest): {', '.join(sorted(unpinned))}")

    with ci_step("Check image version couplings"):
        if violations := version_coupling_violations(Path.cwd(), VERSION_COUPLINGS):
            raise SystemExit(f"Image version coupling violations: {'; '.join(violations)}")

    with ci_step("Database setup"):
        os.environ.update(
            POSTGRES_ADMIN_USER="postgres",
            POSTGRES_ADMIN_PASSWORD="password",
            POSTGRES_HOST="localhost",
            POSTGRES_PORT="55432",
            BACKEND="docker",
            APP_DIR=".",
            DB_HOST="localhost",
            DB_PORT="55432",
            DB_NAME="placeframe",
            DB_USER="placeframe_owner",
            DB_PASSWORD="password",
            DATABASE_SCHEMA_DIR="database",
            ALLOWED_HAZARDS="HAS_UNTRACKABLE_DEPENDENCIES",
        )
        os.environ.update(compute_service_shas(Path.cwd(), Path("compose.bake.yml")))
        # Build the postgres wrapper locally so the image tag in compose.postgres.yml resolves
        # without needing a registry push first.
        bash("docker compose -f compose.bake.yml --env-file .env.lock build postgres")
        # Kill any leftover containers to avoid port collisions on shared runners
        bash("docker compose --env-file .env.lock -f compose.postgres.yml down --volumes --remove-orphans")
        bash("docker compose --env-file .env.lock -f compose.postgres.yml up -d --wait")
        gopath = bash_output("go env GOPATH").strip()
        gopath_bin = Path(gopath) / "bin"
        gopath_bin.mkdir(parents=True, exist_ok=True)
        os.environ["PATH"] = f"{gopath_bin}{os.pathsep}{os.environ['PATH']}"
        bash("go install github.com/stripe/pg-schema-diff/cmd/pg-schema-diff@latest")
        bash(
            "uv run --directory docker/database-manager python -m src.main --op create --name placeframe"
            " --owner-password password"
            " --api-user-password password"
            " --auth-user-password password"
            " --orchestration-user-password password"
        )
        bash("./docker/database-migrator/entrypoint.sh")

    for label, command in [
        ("Sync", "uv sync --all-packages --extra cpu"),
        ("Lint", "uv run ruff check ."),
        ("Format", "uv run ruff format --check ."),
        ("Type check", "uv run basedpyright"),
        ("Dependency check", "uv run deptry-check"),
        ("Test", "uv run pytest"),
    ]:
        with ci_step(label):
            bash(command)

    with ci_step("Check lock files"):
        lock_python(check=True)

    with ci_step("Check datamodel codegen"):
        bash("uv run generate-datamodels")
        staleness_output = bash_output("git status --porcelain -- packages/generated/python/datamodels/")
        if staleness_output.strip():
            bash("git diff -- packages/generated/python/datamodels/")
            raise SystemExit("Generated datamodels are stale. Run 'uv run generate-datamodels' locally.")

    with ci_step("Check client codegen"):
        spec_paths = " ".join(
            f"{project}/openapi.json"
            for project in json.loads(Path("build/openapi-projects.json").read_text(encoding="utf-8"))
        )
        bash("uv run generate-clients --config build/openapi-projects.json --no-cache")
        staleness_output = bash_output(f"git status --porcelain -- {spec_paths} packages/generated/")
        if staleness_output.strip():
            bash(f"git diff -- {spec_paths} packages/generated/")
            raise SystemExit(
                "Generated API clients are stale. Run 'uv run generate-clients --config build/openapi-projects.json' locally."
            )
