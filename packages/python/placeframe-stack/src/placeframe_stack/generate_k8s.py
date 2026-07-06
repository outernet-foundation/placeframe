import shutil
from pathlib import Path
from typing import Annotated

import typer
import yaml
from placeframe_bash import bash

type Yaml = dict[str, Yaml] | list[Yaml] | str | int | float | bool | None

ENV_FILE = Path(".env")
ENV_SHAS_FILE = Path(".env.shas")
LOCK_FILE = Path(".env.lock")
POSTGRES_FILE = Path("compose.postgres.yml")
TRANSFORM_DIR = Path("my-transform")
TRANSFORM_IMAGE = "placeframe-compose-bridge-transform:local"

app = typer.Typer(add_completion=False)


@app.command()
def generate_k8s(
    output_directory: Annotated[
        Path, typer.Option("--output", help="Directory to write the generated manifests into.")
    ] = Path("out"),
) -> None:
    for required in (ENV_FILE, ENV_SHAS_FILE, LOCK_FILE, POSTGRES_FILE, TRANSFORM_DIR):
        if not required.exists():
            raise RuntimeError(f"Missing {required}; run 'uv run build' from the repo root first.")

    bash(f"docker build -t {TRANSFORM_IMAGE} {TRANSFORM_DIR}")

    # Regenerate from scratch so services that changed shape (e.g. Deployment to Job)
    # don't leave orphaned manifests behind.
    shutil.rmtree(output_directory, ignore_errors=True)

    # .env.shas carries the exact ${*_SHA} image tags the last build produced, so every
    # referenced image resolves; .env.lock pins the external images (including the wait
    # images the transform injects).
    bash(
        f"docker compose -f compose.yml -f {POSTGRES_FILE} "
        f"--env-file {ENV_FILE} --env-file {LOCK_FILE} --env-file {ENV_SHAS_FILE} "
        f"bridge convert -t {TRANSFORM_IMAGE} -o {output_directory}"
    )

    # compose-bridge derives container/Service ports from the image's ExposedPorts, a Go
    # map whose iteration order is randomized, so the ports lists come out shuffled between
    # runs. Round-trip each manifest and sort every ports list so the output is byte-stable
    # and a clean-tree check is meaningful.
    for manifest in sorted(output_directory.rglob("*.yaml")):
        documents: list[Yaml] = [document for document in yaml.safe_load_all(manifest.read_text(encoding="utf-8"))]
        for document in documents:
            _sort_ports(document)
        manifest.write_text(
            yaml.safe_dump_all(documents, sort_keys=False, default_flow_style=False, width=1000),
            encoding="utf-8",
        )


def _sort_ports(node: Yaml) -> None:
    if isinstance(node, dict):
        ports = node.get("ports")
        if isinstance(ports, list):
            ports.sort(key=_port_number)
        for value in node.values():
            _sort_ports(value)
    elif isinstance(node, list):
        for item in node:
            _sort_ports(item)


def _port_number(entry: Yaml) -> int:
    if isinstance(entry, dict):
        value = entry.get("containerPort", entry.get("port"))
        if isinstance(value, int):
            return value
    return -1


def main() -> None:
    app()


if __name__ == "__main__":
    main()
