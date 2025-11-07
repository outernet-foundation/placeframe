from __future__ import annotations

import json
import re
from pathlib import Path
from re import Pattern
from shutil import rmtree

from ..run_command import run_command

templates_path = Path(__file__).parent / "templates"


def sync_client(project_path: Path, no_cache: bool, log: bool):
    clients_path = project_path / "clients"
    spec_path = clients_path / "openapi.json"

    print(f"Dumping OpenAPI spec for project: {project_path}")

    openapi_spec = run_command("uv run -m src.dump_openapi", cwd=project_path, log=log)

    if spec_path.exists():
        with spec_path.open("r", encoding="utf-8") as f:
            old_spec = f.read()

        if openapi_spec == old_spec and not no_cache:
            print("OpenAPI spec unchanged, skipping client generation")
            return False

    spec_path.write_text(openapi_spec, encoding="utf-8")

    for config_path in clients_path.glob("config_*.json"):
        client_name = config_path.stem[len("config_") :]
        client_path = clients_path / client_name

        client_path.mkdir(parents=True, exist_ok=True)

        print(f"Removing existing client at {client_path}")

        # Remove existing Api, Models, and Client folders
        config = json.loads(config_path.read_text(encoding="utf-8"))
        if config["generatorName"] == "csharp":
            packageName: str = config["additionalProperties"]["packageName"]
            for subdir in ["Api", "Model", "Client"]:
                dir = client_path / "src" / packageName / subdir
                if dir.exists():
                    rmtree(dir)

        print(f"Generating client {client_name} using config {config_path}")

        # Change all operation tags to "Api" so code generation puts everything in one API object
        openapi_spec_json = json.loads(openapi_spec)
        for path_item in openapi_spec_json.get("paths", {}).values():
            for method in ("get", "put", "post", "delete", "patch", "options", "head", "trace"):
                op = path_item.get(method)
                if isinstance(op, dict):
                    op["tags"] = ["Default"]

        stripped_spec_path = spec_path.parent / f"stripped_{spec_path.name}"
        stripped_spec_path.write_text(json.dumps(openapi_spec_json), encoding="utf-8")

        run_command(
            f"uv run openapi-generator-cli generate "
            f"-g {config['generatorName']} "
            f"-i {stripped_spec_path.resolve().as_posix()} "
            f"-o {client_path.resolve().as_posix()} "
            f"-c {str(config_path.resolve())} "
            f"-t {str(templates_path.resolve())} "
            f"--ignore-file-override {Path(__file__).parent / '.openapi-generator-ignore'}",
            cwd=project_path,
            log=True,
        )

        stripped_spec_path.unlink(missing_ok=True)

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
