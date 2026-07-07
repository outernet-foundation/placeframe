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
COMPOSE_FILE = Path("compose.yml")
POSTGRES_FILE = Path("compose.postgres.yml")
TRANSFORM_DIR = Path("my-transform")
TRANSFORM_IMAGE = "placeframe-compose-bridge-transform:local"
SECRETS_SUBDIR = ".secrets"

app = typer.Typer(add_completion=False)


@app.command()
def generate_k3s(
    output_directory: Annotated[
        Path, typer.Option("--output", help="Directory to write the generated manifests into.")
    ] = Path("out"),
) -> None:
    for required in (ENV_FILE, ENV_SHAS_FILE, LOCK_FILE, COMPOSE_FILE, POSTGRES_FILE, TRANSFORM_DIR):
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
            _normalize_run_as_user(document)
        manifest.write_text(
            yaml.safe_dump_all(documents, sort_keys=False, default_flow_style=False, width=1000),
            encoding="utf-8",
        )

    # compose-bridge never renders environment-sourced secrets (its secret template only
    # emits inline `content`), so the Deployments reference Secrets that nothing creates.
    # Materialise the values into a gitignored dir and drive them through a kustomize
    # secretGenerator, mirroring how the compose stack sources the same values from .env.
    _generate_secrets(output_directory)


def _generate_secrets(output_directory: Path) -> None:
    base = output_directory / "base"
    namespace = _project_namespace(base)
    environment = _merged_environment()

    secrets_directory = base / SECRETS_SUBDIR
    secrets_directory.mkdir(parents=True, exist_ok=True)

    generators: list[Yaml] = []
    for source, variable in sorted(_environment_secrets().items()):
        if variable not in environment:
            raise RuntimeError(f"Secret '{source}' references ${variable}, which is absent from the env files.")

        (secrets_directory / source).write_text(environment[variable], encoding="utf-8")
        generators.append({
            "name": source.replace("_", "-"),
            "namespace": namespace,
            "files": [f"{source}={SECRETS_SUBDIR}/{source}"],
        })

    kustomization_file = base / "kustomization.yaml"
    kustomization: Yaml = yaml.safe_load(kustomization_file.read_text(encoding="utf-8"))
    if not isinstance(kustomization, dict):
        raise TypeError(f"{kustomization_file} did not parse to a mapping.")

    kustomization["secretGenerator"] = generators
    kustomization["generatorOptions"] = {"disableNameSuffixHash": True}
    kustomization_file.write_text(
        yaml.safe_dump(kustomization, sort_keys=False, default_flow_style=False, width=1000),
        encoding="utf-8",
    )


def _project_namespace(base: Path) -> str:
    namespace_files = sorted(base.glob("*-namespace.yaml"))
    if not namespace_files:
        raise RuntimeError(f"No namespace manifest found under {base}.")

    document: Yaml = yaml.safe_load(namespace_files[0].read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise TypeError(f"{namespace_files[0]} did not parse to a mapping.")

    metadata = document.get("metadata")
    if not isinstance(metadata, dict):
        raise TypeError(f"{namespace_files[0]} has no metadata mapping.")

    name = metadata.get("name")
    if not isinstance(name, str):
        raise TypeError(f"{namespace_files[0]} has no string metadata.name.")

    return name


def _environment_secrets() -> dict[str, str]:
    compose: Yaml = yaml.safe_load(COMPOSE_FILE.read_text(encoding="utf-8"))
    secrets = compose.get("secrets") if isinstance(compose, dict) else None
    if not isinstance(secrets, dict):
        return {}

    environment_secrets: dict[str, str] = {}
    for source, definition in secrets.items():
        variable = definition.get("environment") if isinstance(definition, dict) else None
        if isinstance(variable, str):
            environment_secrets[source] = variable

    return environment_secrets


def _merged_environment() -> dict[str, str]:
    environment: dict[str, str] = {}
    for env_file in (ENV_FILE, LOCK_FILE, ENV_SHAS_FILE):
        environment.update(_parse_env_file(env_file))
    return environment


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, _, value = line.removeprefix("export ").partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")

    return values


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


def _normalize_run_as_user(node: Yaml) -> None:
    # compose `user: "uid:gid"` reaches the template as one string, which it emits verbatim
    # as runAsUser. Kubernetes requires integer runAsUser/runAsGroup, so split the pair here.
    if isinstance(node, dict):
        run_as_user = node.get("runAsUser")
        if isinstance(run_as_user, str):
            user, _, group = run_as_user.partition(":")
            node["runAsUser"] = int(user)
            if group:
                node["runAsGroup"] = int(group)

        for value in node.values():
            _normalize_run_as_user(value)
    elif isinstance(node, list):
        for item in node:
            _normalize_run_as_user(item)


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
