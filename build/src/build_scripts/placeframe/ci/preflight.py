from __future__ import annotations

import json
import os
from pathlib import Path

import typer
from bashrun import bash, bash_output

from unity_buildkit.ci_step import ci_step
from stack_lifecycle.context_sha import compute_service_shas
from ..lock_python import lock_python

# Keep in step with the prerequisites documented in score/README.md.
SCORE_K8S_VERSION = "0.15.0"
SCORE_COMPOSE_VERSION = "0.42.0"

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

    with ci_step("Check score codegen"):
        # Fetched as release binaries rather than `go install`: score-spec tags without a leading
        # v (0.15.0, not v0.15.0), which is not a resolvable Go module version. They land in the
        # GOPATH bin the database step already prepended to PATH. Both artifacts are committed,
        # so `generate-score` checks both.
        for tool, version in (("score-k8s", SCORE_K8S_VERSION), ("score-compose", SCORE_COMPOSE_VERSION)):
            archive = f"{tool}_{version}_linux_amd64.tar.gz"
            bash(f"curl -fsSLO https://github.com/score-spec/{tool}/releases/download/{version}/{archive}")
            bash(f"tar -xzf {archive} -C {gopath_bin} {tool}")
            Path(archive).unlink()

        bash("uv run generate-score")
        staleness_output = bash_output("git status --porcelain -- score/")
        if staleness_output.strip():
            bash("git diff -- score/")
            raise SystemExit("Generated Score artifacts are stale. Run 'uv run generate-score' locally.")
