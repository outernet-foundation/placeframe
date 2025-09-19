from __future__ import annotations

import json
import re
from pathlib import Path
from re import Pattern
from shutil import rmtree

from common.run_command import run_command

templates_path = Path(__file__).parent / "templates"


def sync_client(project_path: Path, log: bool = False):
    clients_path = project_path / "clients"
    spec_path = clients_path / "openapi.json"

    print(f"Dumping OpenAPI spec for project: {project_path}")

    openapi_spec = run_command("uv run -m src.dump_openapi", cwd=project_path, log=log)

    if spec_path.exists():
        with spec_path.open("r", encoding="utf-8") as f:
            old_spec = f.read()

        if openapi_spec == old_spec:
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

        run_command(
            f"uv run openapi-generator-cli generate "
            f"-g csharp "
            f"-i {spec_path.resolve().as_posix()} "
            f"-o {client_path.resolve().as_posix()} "
            f"-c {str(config_path.resolve())} "
            f"-t {str(templates_path.resolve())}",
            cwd=project_path,
            log=True,
        )

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
