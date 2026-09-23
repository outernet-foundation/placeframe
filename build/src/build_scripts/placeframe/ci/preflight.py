from __future__ import annotations

import json
import os
from pathlib import Path

import typer
from bashrun.bash import bash, bash_output

from ci_devkit.ci_step import ci_step
from docker_devkit.context_sha import compute_service_shas
from docker_devkit.image_refs import VersionCoupling, VersionSite, unpinned_references, version_coupling_violations
from python_devkit.preflight import preflight as run_battery

# Keep in step with the prerequisites documented in score/README.md.
SCORE_K8S_VERSION = "0.15.0"
SCORE_COMPOSE_VERSION = "0.42.0"

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

    run_battery(Path())

    spec_paths = " ".join(
        f"{project}/openapi.json"
        for project in json.loads(Path("build/openapi-projects.json").read_text(encoding="utf-8"))["projects"]
    )
    _check_generated("datamodels", "uv run generate-datamodels", "packages/generated/python/datamodels/")
    _check_generated(
        "API clients",
        "uv run generate-clients --config build/openapi-projects.json --no-cache",
        f"{spec_paths} packages/generated/",
        "uv run generate-clients --config build/openapi-projects.json",
    )

    with ci_step("Fetch score tools"):
        # Fetched as release binaries rather than `go install`: score-spec tags without a leading
        # v (0.15.0, not v0.15.0), which is not a resolvable Go module version. They land in the
        # GOPATH bin the database step already prepended to PATH. Both artifacts are committed,
        # so `generate-score` checks both.
        for tool, version in (("score-k8s", SCORE_K8S_VERSION), ("score-compose", SCORE_COMPOSE_VERSION)):
            archive = f"{tool}_{version}_linux_amd64.tar.gz"
            bash(f"curl -fsSLO https://github.com/score-spec/{tool}/releases/download/{version}/{archive}")
            bash(f"tar -xzf {archive} -C {gopath_bin} {tool}")
            Path(archive).unlink()

    _check_generated("Score", "uv run generate-score", "score/")


def _check_generated(label: str, generate_command: str, pathspec: str, fix_command: str | None = None) -> None:
    with ci_step(f"Check {label}"):
        bash(generate_command)
        staleness_output = bash_output(f"git status --porcelain -- {pathspec}")
        if staleness_output.strip():
            bash(f"git diff -- {pathspec}")
            raise SystemExit(
                f"{label} output is stale. Run '{fix_command or generate_command}' locally and commit the result."
            )
