import json
from pathlib import Path
from tempfile import TemporaryDirectory

from bashrun import bash_output
from openapi_clientgen import (
    DefaultNamingPolicy,
    downgrade_openapi_3_1_to_3_0,
    generate_client,
    regenerate_templates,
)
from typer import Option, Typer

ROOT_NAME = "placeframe"
REPO_ROOT = Path(__file__).parents[4]
GENERATED_ROOT = REPO_ROOT / "packages" / "generated"


def cli(
    config: str = Option(...),
    project: Path | None = Option(None),
    client: str | None = Option(None),
    no_cache: bool = Option(False),
):
    naming = DefaultNamingPolicy(ROOT_NAME)
    config_json: dict[str, list[str]] = json.loads(Path(config).read_text(encoding="utf-8"))

    with TemporaryDirectory() as templates_directory_string:
        templates_directory = Path(templates_directory_string)
        regenerate_templates(templates_directory)

        for project_name, clients in config_json.items():
            if project is not None and str(project) != project_name:
                continue

            openapi_spec = _dump_openapi_spec(Path(project_name), no_cache)

            if openapi_spec is None:
                continue

            names = naming(project_name)

            for client_name in clients:
                if client is not None and client_name != client:
                    continue

                output_dir = GENERATED_ROOT / client_name / names.base
                generate_client(openapi_spec, client_name, output_dir, names, templates_dir=templates_directory)


def _dump_openapi_spec(project: Path, no_cache: bool) -> str | None:
    print(f"Dumping OpenAPI spec for project: {project}")

    # CODEGEN=1 gates each service package's heavy imports (torch/pycolmap, ZED_BOX_ID) so the app
    # imports cleanly for the spec dump; it reaches the child through bashrun's per-call env overlay.
    raw_spec = bash_output("uv run --project . python -m src.dump_openapi", cwd=project, env={"CODEGEN": "1"})

    # Downgrade OpenAPI 3.1 to 3.0 for compatibility with OpenAPI Generator (Litestar only emits 3.1)
    openapi_json = json.loads(raw_spec)
    downgrade_openapi_3_1_to_3_0(openapi_json)
    openapi_spec = json.dumps(openapi_json, indent=2)

    spec_path = project / "openapi.json"

    if spec_path.exists():
        old_spec = spec_path.read_text(encoding="utf-8")

        if openapi_spec == old_spec and not no_cache:
            print("OpenAPI spec unchanged, skipping client generation")
            return None

    spec_path.write_text(openapi_spec, encoding="utf-8")

    return openapi_spec


app = Typer(pretty_exceptions_show_locals=False)
app.command()(cli)


def main():
    app()


if __name__ == "__main__":
    main()
