from __future__ import annotations

import os
from pathlib import Path

import typer
from placeframe_bash import bash, bash_output

from placeframe_unity.ci_step import ci_step
from ..context_sha import compute_service_shas
from ..lock_python import lock_python

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


@app.command()
def main() -> None:
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
        bash("uv run generate-clients --config build/openapi-projects.json --project docker/api --no-cache")
        staleness_output = bash_output("git status --porcelain -- docker/api/openapi.json packages/generated/")
        if staleness_output.strip():
            bash("git diff -- docker/api/openapi.json packages/generated/")
            raise SystemExit(
                "Generated API clients are stale. Run 'uv run generate-clients --config build/openapi-projects.json' locally."
            )
