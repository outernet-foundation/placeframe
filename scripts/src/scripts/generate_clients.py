import json
from pathlib import Path
from shutil import rmtree
from tempfile import NamedTemporaryFile

from common.fix_openapi_schema import convert_openapi_3_1_to_3_0
from common.run_command import run_command
from typer import Option, Typer

REPO_ROOT = Path(__file__).parents[3]
OPENAPI_GENERATOR_PATH = Path(__file__).parents[2] / "openapi-generator"
CONFIGS_PATH = OPENAPI_GENERATOR_PATH / "configs"
TEMPLATES_PATH = OPENAPI_GENERATOR_PATH / "templates-generated"
TEMPLATE_PATCHES_PATH = OPENAPI_GENERATOR_PATH / "templates-patches"


def cli(
    config: str = Option(...),
    project: Path | None = Option(None),
    client: str | None = Option(None),
    no_cache: bool = Option(False),
):
    with Path(config).open("r", encoding="utf-8") as file:
        config_json: dict[str, list[str]] = json.load(file)

    _generate_templates()

    for project_name, clients in config_json.items():
        if project is not None and project.name != project_name:
            continue

        openapi_spec = _dump_openapi_spec(Path(project_name), no_cache)

        if openapi_spec is None:
            continue

        for client_name in clients:
            if client is not None and client_name != client:
                continue

            _generate_client(openapi_spec, project_name, client_name)


def _dump_openapi_spec(project: Path, no_cache: bool) -> str | None:
    print(f"Dumping OpenAPI spec for project: {project}")

    openapi_spec = run_command("uv run --project . --no_workspace python -m src.dump_openapi", cwd=project)
    openapi_json = json.loads(openapi_spec)
    convert_openapi_3_1_to_3_0(openapi_json)
    openapi_spec = json.dumps(openapi_json, indent=2)

    spec_path = project / "openapi.json"

    if spec_path.exists():
        with spec_path.open("r", encoding="utf-8") as f:
            old_spec = f.read()

        if openapi_spec == old_spec and not no_cache:
            print("OpenAPI spec unchanged, skipping client generation")
            return None

    spec_path.write_text(openapi_spec, encoding="utf-8")

    return openapi_spec


def _generate_templates():
    (TEMPLATES_PATH).mkdir(parents=True, exist_ok=True)

    run_command(
        f"uv run --no_workspace openapi-generator-cli author template -g csharp --library httpclient -o {str(TEMPLATES_PATH / 'csharp')}",
        log=True,
        cwd=REPO_ROOT,
    )

    # git apply directory is always relative to the repo root
    for patch_file in (TEMPLATE_PATCHES_PATH / "csharp").iterdir():
        run_command(f"git apply {str(patch_file)}", log=True)


def _generate_client(openapi_spec: str, project: str, client: str):
    client_config_json = json.loads((CONFIGS_PATH / f"{client}.json").read_text(encoding="utf-8"))
    client_package_base_name = f"{project.split('/')[-1]}-client"
    client_path = Path("packages/generated") / client / f"{client_package_base_name}"

    # Clear existing client directory
    rmtree(client_path, ignore_errors=True)
    client_path.mkdir(parents=True, exist_ok=True)

    client_package_name_dashed = f"plerion-{client_package_base_name}"
    client_package_name_underscored = client_package_name_dashed.replace("-", "_")
    client_package_name_camel = f"Plerion{''.join(part.capitalize() for part in client_package_base_name.split('-'))}"

    if client == "csharp":
        client_config_json["additionalProperties"]["packageName"] = client_package_name_camel
    else:
        client_config_json["additionalProperties"]["projectName"] = client_package_name_dashed
        client_config_json["additionalProperties"]["packageName"] = client_package_name_underscored

    with (
        NamedTemporaryFile("w+", encoding="utf-8", suffix=".json", delete=False) as temp_spec_file,
        NamedTemporaryFile("w+", encoding="utf-8", suffix=".json", delete=False) as temp_config_file,
    ):
        # Change all operation tags to "Api" so code generation puts everything in one API object
        openapi_spec_json = json.loads(openapi_spec)
        for path_item in openapi_spec_json.get("paths", {}).values():
            for method in ("get", "put", "post", "delete", "patch", "options", "head", "trace"):
                op = path_item.get(method)
                if isinstance(op, dict):
                    op["tags"] = ["Default"]

        json.dump(openapi_spec_json, temp_spec_file)
        temp_spec_file.flush()

        json.dump(client_config_json, temp_config_file)
        temp_config_file.flush()

        command = (
            f"uv run --no_workspace openapi-generator-cli generate "
            f"-g {client} "
            f"-i {Path(temp_spec_file.name).resolve().as_posix()} "
            f"-o {client_path.resolve().as_posix()} "
            f"-c {str(Path(temp_config_file.name).resolve())} "
            f"--ignore-file-override {str(OPENAPI_GENERATOR_PATH / '.openapi-generator-ignore')}"
        )

        if client == "csharp":
            command += f" -t {str(TEMPLATES_PATH / 'csharp')}"

        run_command(command, log=True)

        print(f"Generated {client} client at {client_path}")

    if client == "csharp":
        (client_path / "src" / client_package_name_camel / "package.json").write_text(
            json.dumps(
                {
                    "name": f"com.plerion.{client_package_base_name}",
                    "displayName": client_package_name_camel,
                    "version": "0.0.1",
                },
                indent=2,
            )
        )
        (client_path / "src" / client_package_name_camel / f"{client_package_name_camel}.asmdef").write_text(
            json.dumps(
                {
                    "name": client_package_name_camel,
                    "references": ["Newtonsoft.Json", "Polly", "JsonSubTypes"],
                    "includePlatforms": [],
                    "excludePlatforms": [],
                    "allowUnsafeCode": False,
                    "overrideReferences": False,
                    "precompiledReferences": [],
                    "autoReferenced": True,
                    "defineConstraints": [],
                    "versionDefines": [],
                    "noEngineReferences": False,
                },
                indent=2,
            )
        )
        # Tell the C# compiler to enable nullable annotations
        (client_path / "src" / client_package_name_camel / "csc.rsp").write_text("-nullable:annotations")

    elif client == "python":
        run_command(f"uv pip install {client_path.resolve().as_posix()}", log=True)


app = Typer(pretty_exceptions_show_locals=False)
app.command()(cli)


def main():
    app()


if __name__ == "__main__":
    main()
