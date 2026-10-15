from __future__ import annotations

import os
from pathlib import Path

from bashrun.bash import bash, bash_output

from docker_devkit.context_sha import compute_service_shas
from docker_devkit.documents import parse_bake
from docker_devkit.image_refs import VersionCoupling, VersionSite, unpinned_references, version_coupling_violations
from docker_devkit.lifecycle import require_manifest

VERSION_COUPLINGS = [
    VersionCoupling(
        name="uv",
        pyproject_key="tool.uv.required-version",
        sites=(VersionSite("uv base tag", "workloads/images.yml", r"uv:([^@]+?)-", "UV_BASE_IMAGE"),),
    ),
    VersionCoupling(
        name="python",
        pyproject_key="project.requires-python",
        sites=(
            VersionSite("uv base python component", "workloads/images.yml", r"python([0-9][0-9.]*)", "UV_BASE_IMAGE"),
        ),
    ),
]


def main() -> None:
    bash("uv run --locked preflight-python")

    print("Check image references")
    if unpinned := unpinned_references(Path.cwd()):
        raise SystemExit(f"Unpinned image references (need tag or digest): {', '.join(sorted(unpinned))}")

    print("Check image version couplings")
    if violations := version_coupling_violations(Path.cwd(), VERSION_COUPLINGS):
        raise SystemExit(f"Image version coupling violations: {'; '.join(violations)}")

    print("Database setup")
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
    os.environ.update(compute_service_shas(Path.cwd(), parse_bake(require_manifest(Path.cwd()))))
    # Build the postgres wrapper locally so the image tag in compose.postgres.yml resolves
    # without needing a registry push first. --project-directory anchors the manifest's
    # relative paths at the repo root; compose would otherwise resolve them against the
    # manifest's own directory.
    bash("docker compose --project-directory . -f workloads/images.yml --env-file workloads/images.lock build postgres")
    # Kill any leftover containers to avoid port collisions on shared runners
    bash("docker compose --env-file workloads/images.lock -f compose.postgres.yml down --volumes --remove-orphans")
    bash("docker compose --env-file workloads/images.lock -f compose.postgres.yml up -d --wait")
    gopath = bash_output("go env GOPATH").strip()
    gopath_bin = Path(gopath) / "bin"
    gopath_bin.mkdir(parents=True, exist_ok=True)
    os.environ["PATH"] = f"{gopath_bin}{os.pathsep}{os.environ['PATH']}"
    bash("go install github.com/stripe/pg-schema-diff/cmd/pg-schema-diff@latest")
    bash(
        "uv run --directory workloads/database-manager python -m src.main --op create --name placeframe"
        " --owner-password password"
        " --api-user-password password"
        " --auth-user-password password"
        " --orchestration-user-password password"
    )
    bash("./workloads/database-migrator/entrypoint.sh")

    # Score staleness gate disabled: generated stack/ output embeds per-service tree-SHA image
    # tags, so every dependency-lock bump re-stales it (see stack/AGENTS.md).
    _check_generated("datamodels", "uv run generate-datamodels", "packages/generated/python/datamodels/")

    bash("uv run --locked generate-clients --config openapi-client-codegen.yaml --check")


def _check_generated(label: str, generate_command: str, pathspec: str, fix_command: str | None = None) -> None:
    print(f"Check {label}")
    bash(generate_command)
    staleness_output = bash_output(f"git status --porcelain -- {pathspec}")
    if staleness_output.strip():
        bash(f"git diff -- {pathspec}")
        raise SystemExit(
            f"{label} output is stale. Run '{fix_command or generate_command}' locally and commit the result."
        )


if __name__ == "__main__":
    main()
