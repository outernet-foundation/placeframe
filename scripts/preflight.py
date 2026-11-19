from __future__ import annotations

import os
import time

from bashrun.bash import bash, bash_check, bash_output


def main() -> None:
    bash("uv run --locked preflight-python")

    print("Database setup")
    os.environ.update(
        POSTGRES_ADMIN_USER="postgres",
        POSTGRES_ADMIN_PASSWORD="password",
        POSTGRES_HOST="localhost",
        POSTGRES_PORT="55432",
    )
    # Build the migration-path images so their tree tags resolve without a registry push
    bash("uv run --locked boatyard build --targets 'postgres database-manager database-migrator'")
    postgres_tag = bash_output("uv run --locked boatyard tree-tags postgres").strip()
    # Run postgres as one throwaway container instead of a compose project: an isolated
    # bring-up cannot collide with (or tear down) a concurrently running dev stack, and
    # the container's ephemeral filesystem replaces the old down --volumes reset.
    if bash_check("docker inspect pf-preflight-postgres"):
        bash("docker rm -f pf-preflight-postgres")
    bash(
        "docker run --rm -d --name pf-preflight-postgres -p 55432:5432"
        " --entrypoint /usr/local/bin/entrypoint-wrapper.sh"
        " -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=password"
        f" ghcr.io/outernet-foundation/placeframe/postgres:{postgres_tag}"
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
    # Run the same database-manager invocation the compose provisioner runs
    database_manager_tag = bash_output("uv run --locked boatyard tree-tags database-manager").strip()
    bash(
        "docker run --rm --network host"
        " -e POSTGRES_HOST=localhost -e POSTGRES_PORT=55432"
        " -e POSTGRES_ADMIN_USER=postgres -e POSTGRES_ADMIN_PASSWORD=password"
        " --entrypoint uv"
        f" ghcr.io/outernet-foundation/placeframe/database-manager:{database_manager_tag}"
        " run --no-sync python -m src.main --op create --name placeframe"
        " --owner-password password"
        " --api-user-password password"
        " --auth-user-password password"
        " --orchestration-user-password password"
    )
    migrator_tag = bash_output("uv run --locked boatyard tree-tags database-migrator").strip()
    # Prove the standing hazard gate passes a no-op re-up
    bash(
        "docker run --rm --network host"
        " -e DB_HOST=localhost -e DB_PORT=55432 -e DB_NAME=placeframe"
        " -e DB_USER=placeframe_owner -e DB_PASSWORD=password"
        " -e DATABASE_SCHEMA_DIR=database"
        " -e ALLOWED_HAZARDS=HAS_UNTRACKABLE_DEPENDENCIES"
        f" ghcr.io/outernet-foundation/placeframe/database-migrator:{migrator_tag}"
    )

    # Score staleness gate disabled: generated stack/ output embeds per-service tree-tag image
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
