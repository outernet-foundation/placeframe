#!/usr/bin/env python3
import json
import os
import re
import subprocess
import sys
from pathlib import Path

from ..db.tool import LOCAL_CONF

os.environ["PICCOLO_CONF"] = LOCAL_CONF
from ..main import app

script_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(script_dir))


def dump_openapi(spec_path: Path):
    spec = app.openapi()
    spec_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    print(f"OpenAPI spec written to {spec_path}")


def generate_client(config_path: Path, spec_uri: Path, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            "uv",
            "run",
            "openapi-generator-cli",
            "generate",
            "-i",
            spec_uri.resolve().as_posix(),
            "-o",
            out_dir.resolve().as_posix(),
            "--config",
            str(config_path.resolve()),
        ],
        check=True,
    )


def patch_commas(output_dir: Path):
    pattern = re.compile(r"(?m)^(\s*public partial class \w+\s*:\s*[^,\{]+),\s*$")
    for cs_file in output_dir.rglob("*.cs"):
        text = cs_file.read_text(encoding="utf-8")
        fixed = pattern.sub(lambda m: m.group(1), text)
        if fixed != text:
            cs_file.write_text(fixed, encoding="utf-8")
            print(f"Patched stray comma in {cs_file}")


def main():
    cwd = Path.cwd()
    sys.path.insert(0, str(cwd))

    script_dir = Path(__file__).resolve().parent
    config_path = script_dir / "config.json"
    spec_path = script_dir / "openapi.json"
    output_dir = script_dir.parent.parent.parent / "clients" / "csharp"
    dump_openapi(spec_path)
    generate_client(config_path, spec_path, output_dir)
    patch_commas(output_dir)

    print("Client generation complete.")


if __name__ == "__main__":
    main()
