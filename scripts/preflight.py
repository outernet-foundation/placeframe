from __future__ import annotations

import os
import time
from pathlib import Path

from bashrun.bash import bash, bash_check, bash_output

from docker_devkit.build_docker import run_build
from docker_devkit.config import load_config
from docker_devkit.documents import compute_service_shas
from docker_devkit.image_refs import VersionCoupling, VersionSite, unpinned_references, version_coupling_violations

VERSION_COUPLINGS = [
    VersionCoupling(
        name="uv",
        pyproject_key="tool.uv.required-version",
        sites=(VersionSite("uv base tag", "docker-devkit.yaml", r"uv:([^@]+?)-", "UV_BASE_IMAGE"),),
    ),
    VersionCoupling(
        name="python",
        pyproject_key="project.requires-python",
        sites=(
            VersionSite("uv base python component", "docker-devkit.yaml", r"python([0-9][0-9.]*)", "UV_BASE_IMAGE"),
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
    config = load_config(Path.cwd())
    if config is None:
        raise SystemExit("docker-devkit.yaml not found at the repo root")
    os.environ.update(compute_service_shas(Path.cwd(), config))
    # Build the postgres wrapper locally so its tree-sha image tag resolves without
    # needing a registry push first (run_build also injects the SHAs it computes).
    run_build(targets_opt=["postgres"])
    # Run postgres as one throwaway container instead of a compose project: an isolated
    # bring-up cannot collide with (or tear down) a concurrently running dev stack, and
    # the container's ephemeral filesystem replaces the old down --volumes reset.
    if bash_check("docker inspect pf-preflight-postgres"):
        bash("docker rm -f pf-preflight-postgres")
    bash(
        "docker run --rm -d --name pf-preflight-postgres -p 55432:5432"
        " --entrypoint /usr/local/bin/entrypoint-wrapper.sh"
        " -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=password"
        f" ghcr.io/outernet-foundation/placeframe/postgres:{os.environ['POSTGRES_SHA']}"
    )
    ready = False
    for _ in range(30):
        if bash_check("docker exec pf-preflight-postgres pg_isready -q -h localhost -p 5432 -U postgres"):
            ready = True
            break
        time.sleep(1)
    if not ready:
        logs = bash_output("docker logs pf-preflight-postgres")
        raise SystemExit(f"preflight postgres never became ready:\n{logs}")
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
