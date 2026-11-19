from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated
import shlex

import typer
import yaml
from bashrun.bash import bash_handoff, bash_output
from pydantic import TypeAdapter

REPO_ROOT = Path(__file__).resolve().parents[3]
VALUES_FILE = REPO_ROOT / "boatyard.values.yaml"
STANDING_HAZARDS = "HAS_UNTRACKABLE_DEPENDENCIES"
MIGRATOR_REPOSITORY = "ghcr.io/outernet-foundation/placeframe/database-migrator"
_DICT_ADAPTER = TypeAdapter(dict[str, object])

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


@app.command()
def main(
    allow_hazard: Annotated[
        list[str] | None,
        typer.Option(
            "--allow-hazard",
            help="Hazard class to allow for this one apply, e.g. AUTHZ_UPDATE (repeatable)",
        ),
    ] = None,
) -> None:
    # Compose the standing list plus any per-incident overrides
    attended = bool(allow_hazard)
    hazards = ",".join([STANDING_HAZARDS, *(allow_hazard or [])])

    # Read the owner password from the values file, defaulting to the dev password
    document = _DICT_ADAPTER.validate_python(yaml.safe_load(VALUES_FILE.read_text(encoding="utf-8")))
    values = _DICT_ADAPTER.validate_python(document.get("values") or {})
    owner_password = str(values.get("DATABASE_OWNER_PASSWORD") or "password")

    # Find the stack network from the running postgres container
    containers = bash_output(
        "docker ps --filter label=com.docker.compose.service=pf-postgres --format {{.Names}}"
    ).split()

    # If not exactly one pf-postgres container is running
    if len(containers) != 1:
        print(f"Expected exactly one running pf-postgres container, found {len(containers)}; bring up one stack")
        raise typer.Exit(1)
    networks = bash_output(f"docker inspect {containers[0]} --format {{{{json .NetworkSettings.Networks}}}}")
    network = next(iter(json.loads(networks)), "")

    # If the container sits on no network
    if not network:
        print(f"Container {containers[0]} is attached to no docker network")
        raise typer.Exit(1)

    # Resolve the migrator tree tag
    tag = bash_output("uv run --locked boatyard tree-tags database-migrator").strip()

    # Assemble the migrator invocation
    tty_flags = " -it" if attended else ""
    command = (
        f"docker run --rm{tty_flags} --network {network}"
        " -e DB_HOST=pf-postgres -e DB_PORT=5432 -e DB_NAME=placeframe"
        " -e DB_USER=placeframe_owner"
        f" -e DB_PASSWORD={shlex.quote(owner_password)}"
        " -e DATABASE_SCHEMA_DIR=database"
        f" -e ALLOWED_HAZARDS={hazards}"
    )

    # If the run is attended
    if attended:
        # Keep the tool's y/N prompt so the consent is the printed plan
        command += " -e CONFIRM_PROMPT=1"
    command += f" {MIGRATOR_REPOSITORY}:{tag}"

    # Run the invocation attached to this terminal
    bash_handoff(command)
