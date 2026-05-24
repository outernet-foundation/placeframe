import json
from os import environ, walk
from pathlib import Path
from shutil import copyfile, copytree
from tempfile import NamedTemporaryFile, TemporaryDirectory

from common.bash import bash, bash_output
from typer import Option, Typer

from .downgrade_openapi_schema import downgrade_openapi_3_1_to_3_0

ROOT_NAME = "placeframe"
REPO_ROOT = Path(__file__).parents[4]
OPENAPI_GENERATOR_PATH = REPO_ROOT / "build" / "openapi-generator"
CONFIGS_PATH = OPENAPI_GENERATOR_PATH / "configs"
TEMPLATES_PATH = OPENAPI_GENERATOR_PATH / "templates-generated"
TEMPLATE_PATCHES_PATH = OPENAPI_GENERATOR_PATH / "templates-patches"
OVERLAYS_PATH = OPENAPI_GENERATOR_PATH / "overlays"
OPENAPI_GENERATOR_CLI_VERSION = json.loads((REPO_ROOT / "openapitools.json").read_text(encoding="utf-8"))[
    "generator-cli"
]["version"]

# Suppress verbose OpenAPI Generator logging
environ["JAVA_OPTS"] = "-Dlog.level=warn"

# Set in the environment so it reaches each `uv run ... python -m src.dump_openapi`
# subprocess before the interpreter starts. Each service's package __init__ gates heavy
# imports on CODEGEN (torch/pycolmap, ZED_BOX_ID) and runs before dump_openapi could set it.
environ["CODEGEN"] = "1"


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
        if project is not None and str(project) != project_name:
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

    openapi_spec = bash_output("uv run --project . python -m src.dump_openapi", cwd=project)

    # Downgrade OpenAPI 3.1 to 3.0 for compatibility with OpenAPI Generator (Litestar only supports generating 3.1)
    openapi_json = json.loads(openapi_spec)
    downgrade_openapi_3_1_to_3_0(openapi_json)
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

    bash(
        f"uvx --from 'openapi-generator-cli[jdk4py]=={OPENAPI_GENERATOR_CLI_VERSION}' openapi-generator-cli author template -g csharp --library httpclient -o {str(TEMPLATES_PATH / 'csharp')}",
        cwd=REPO_ROOT,
    )

    # 'git apply' directory is always relative to the repo root
    for patch_file in (TEMPLATE_PATCHES_PATH / "csharp").iterdir():
        bash(f"git apply --ignore-space-change --ignore-whitespace {str(patch_file)}")


def _generate_client(openapi_spec: str, project: str, client: str):
    client_config_json = json.loads((CONFIGS_PATH / f"{client}.json").read_text(encoding="utf-8"))
    client_package_base_name = f"{project.split('/')[-1]}-client"
    client_path = Path("packages/generated") / client / f"{client_package_base_name}"
    client_package_name_dashed = f"{ROOT_NAME}-{client_package_base_name}"
    client_package_name_underscored = client_package_name_dashed.replace("-", "_")
    client_package_name_camel = (
        f"{ROOT_NAME.capitalize()}{''.join(part.capitalize() for part in client_package_base_name.split('-'))}"
    )

    if client == "csharp":
        client_config_json["additionalProperties"]["packageName"] = client_package_name_camel
    else:
        client_config_json["additionalProperties"]["projectName"] = client_package_name_dashed
        client_config_json["additionalProperties"]["packageName"] = client_package_name_underscored

    with (
        NamedTemporaryFile("w+", encoding="utf-8", suffix=".json", delete=False) as temporary_spec_file,
        NamedTemporaryFile("w+", encoding="utf-8", suffix=".json", delete=False) as temporary_config_file,
        TemporaryDirectory() as temporary_directory_string,
    ):
        temporary_directory = Path(temporary_directory_string)

        # Change all operation tags to "Api" so code generation puts everything in one API object
        openapi_spec_json = json.loads(openapi_spec)
        for path_item in openapi_spec_json.get("paths", {}).values():
            for method in ("get", "put", "post", "delete", "patch", "options", "head", "trace"):
                op = path_item.get(method)
                if isinstance(op, dict):
                    op["tags"] = ["Default"]

        json.dump(openapi_spec_json, temporary_spec_file)
        temporary_spec_file.flush()

        json.dump(client_config_json, temporary_config_file)
        temporary_config_file.flush()

        command = (
            f"uvx --from 'openapi-generator-cli[jdk4py]=={OPENAPI_GENERATOR_CLI_VERSION}' openapi-generator-cli generate "
            f"-g {client} "
            f"-i {Path(temporary_spec_file.name).resolve().as_posix()} "
            f"-o {temporary_directory.resolve().as_posix()} "  # CHANGED: Output to temp_dir
            f"-c {str(Path(temporary_config_file.name).resolve())} "
            f"--ignore-file-override {str(OPENAPI_GENERATOR_PATH / '.openapi-generator-ignore')} "
        )

        if client == "csharp":
            command += f" -t {str(TEMPLATES_PATH / 'csharp')}"

        bash(command)

        print(f"Generated {client} client (temp) at {temporary_directory}")

        # Add Unity-specific package files for C#
        if client == "csharp":
            (temporary_directory / "src" / client_package_name_camel / "package.json").write_text(
                json.dumps(
                    {
                        "name": f"org.nuget.{client_package_name_camel.lower()}",
                        "displayName": client_package_name_camel,
                        "version": "0.0.1",
                    },
                    indent=2,
                )
            )
            (
                temporary_directory / "src" / client_package_name_camel / f"{client_package_name_camel}.asmdef"
            ).write_text(
                json.dumps(
                    {
                        "name": client_package_name_camel,
                        "references": ["Newtonsoft.Json", "Polly", "JsonSubTypes", "UniTask"],
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
            (temporary_directory / "src" / client_package_name_camel / "csc.rsp").write_text("-nullable:annotations")

            # Drop a Directory.Build.props next to the generated csproj so MSBuild
            # picks up additional <PackageReference>s the upstream csharp generator
            # doesn't emit (UniTask). Lands inside src/<package>/ so it's covered
            # by the per-client Dockerfile COPY of packages/generated/csharp/<client>/.
            for overlay_file in (OVERLAYS_PATH / "csharp").iterdir():
                copyfile(overlay_file, temporary_directory / "src" / client_package_name_camel / overlay_file.name)

        print(f"Syncing to {client_path}...")

        client_path.mkdir(parents=True, exist_ok=True)

        # Delete stale files
        for target_file in client_path.rglob("*"):
            if not target_file.is_file():
                continue

            relative_path = target_file.relative_to(client_path)

            # Special case for .meta files in Unity C# projects
            if target_file.name.endswith(".meta"):
                relative_path = relative_path.with_name(target_file.name[:-5])

            if not (temporary_directory / relative_path).exists():
                target_file.unlink()

        # Delete stale directories
        for root, dirs, _ in walk(client_path, topdown=False):
            for name in dirs:
                target_dir = Path(root) / name
                if not (temporary_directory / target_dir.relative_to(client_path)).exists():
                    target_dir.rmdir()

        # Copy new and updated files
        copytree(temporary_directory, client_path, dirs_exist_ok=True)

    if client == "python":
        bash(f"uv pip install {client_path.resolve().as_posix()}")


app = Typer(pretty_exceptions_show_locals=False)
app.command()(cli)


def main():
    app()


if __name__ == "__main__":
    main()
