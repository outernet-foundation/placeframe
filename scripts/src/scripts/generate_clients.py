import json
import re
from pathlib import Path
from re import Pattern
from tempfile import NamedTemporaryFile

from common.run_command import run_command
from typer import Option, run

MUSTACHE_TEMPLATES_PATH = Path(__file__).parents[2] / "mustache-templates"
OPENAPI_GENERATOR_IGNORE_PATH = Path(__file__).parents[2] / ".openapi-generator-ignore"
OPENAPI_GENERATOR_CONFIGS_PATH = Path(__file__).parents[2] / "openapi-generator-configs"


def cli(
    config: str = Option(...),
    project: Path | None = Option(None),
    client: str | None = Option(None),
    no_cache: bool = Option(False),
):
    with Path(config).open("r", encoding="utf-8") as file:
        config_json: dict[str, list[str]] = json.load(file)

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

    spec_path = project / "openapi.json"

    if spec_path.exists():
        with spec_path.open("r", encoding="utf-8") as f:
            old_spec = f.read()

        if openapi_spec == old_spec and not no_cache:
            print("OpenAPI spec unchanged, skipping client generation")
            return None

    spec_path.write_text(openapi_spec, encoding="utf-8")

    return openapi_spec


def _generate_client(openapi_spec: str, project: str, client: str):
    client_config_json = json.loads((OPENAPI_GENERATOR_CONFIGS_PATH / f"{client}.json").read_text(encoding="utf-8"))
    client_package_base_name = f"{project.split('/')[-1]}-client"
    client_path = Path("packages/generated") / client / f"{client_package_base_name}"
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

        run_command(
            f"uv run --no_workspace openapi-generator-cli generate "
            f"-g {client} "
            f"-i {Path(temp_spec_file.name).resolve().as_posix()} "
            f"-o {client_path.resolve().as_posix()} "
            f"-c {str(Path(temp_config_file.name).resolve())} "
            f"-t {str(MUSTACHE_TEMPLATES_PATH.resolve())} "
            f"--ignore-file-override {str(OPENAPI_GENERATOR_IGNORE_PATH.resolve())}",
            log=True,
        )

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
                    "references": [],
                    "includePlatforms": [],
                    "excludePlatforms": [],
                    "allowUnsafeCode": False,
                    "overrideReferences": False,
                    "precompiledReferences": ["Newtonsoft.Json.dll", "Polly.dll", "JsonSubTypes.dll"],
                    "autoReferenced": True,
                    "defineConstraints": [],
                    "versionDefines": [],
                    "noEngineReferences": False,
                },
                indent=2,
            )
        )
    elif client == "python":
        run_command(f"uv pip install {client_path.resolve().as_posix()}", log=True)

    # This is a workaround for a bug in one of the openapi jinja templates for C# that results in stray commas in generated code
    print("Checking for stray commas")

    pat_next: Pattern[str] = re.compile(
        r"(?m)^(\s*(?:public|internal)(?:\s+(?:abstract|sealed))?(?:\s+partial)?\s+class\s+\w+\s*:[^{\r\n]+),\s*\r?\n(\s*)\{"
    )

    pat_same: Pattern[str] = re.compile(
        r"(?m)^(\s*(?:public|internal)(?:\s+(?:abstract|sealed))?(?:\s+partial)?\s+class\s+\w+\s*:[^{\r\n]+),\s*\{"
    )

    for cs_file in client_path.rglob("*.cs"):
        text: str = cs_file.read_text(encoding="utf-8")
        fixed: str = pat_next.sub(r"\1\n\2{", text)
        fixed = pat_same.sub(r"\1 {", fixed)

        if fixed != text:
            cs_file.write_text(fixed, encoding="utf-8")
            print(f"Patched stray comma in {cs_file}")


def main():
    run(cli)


if __name__ == "__main__":
    main()
