# Vibe code: Gemini 3
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path


def main():
    SKIP_PROJECTS = {}
    SKIP_DIRS = {"generated", "third-party", "infrastructure", "test"}
    # Capture groups: (1) Filename, (2) Line, (3) Col, (4) Message
    ERROR_PATTERN = re.compile(r"^(.*):(\d+):(\d+):(.+)$")
    ANSI_ESCAPE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    root = Path("pyproject.toml").resolve()
    if not root.exists() and Path("../pyproject.toml").exists():
        root = Path("../pyproject.toml").resolve()

    if not root.exists():
        print("❌ Error: Could not find pyproject.toml", file=sys.stderr)
        sys.exit(1)

    with root.open("rb") as f:
        members = tomllib.load(f).get("tool", {}).get("uv", {}).get("workspace", {}).get("members", [])

    workspace_root = root.parent
    env = os.environ.copy()
    env["NO_COLOR"] = "1"
    env["FORCE_COLOR"] = "0"
    any_failed = False

    for member in members:
        member_path = workspace_root / member

        if member in SKIP_PROJECTS:
            continue

        if not set(member_path.parts).isdisjoint(SKIP_DIRS):
            continue

        if not (member_path / "pyproject.toml").exists():
            continue

        print(f"🔍 Checking project: {member_path}")
        # stderr=subprocess.STDOUT merges errors into stdout so we can process them in the loop below
        result = subprocess.run(
            ["uv", "run", "deptry", "."],
            cwd=member_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
        )

        if result.returncode == 0:
            continue

        any_failed = True

        for line in result.stdout.splitlines():
            clean_line = ANSI_ESCAPE.sub("", line)
            match = ERROR_PATTERN.match(clean_line)

            if not match:
                print(clean_line)
                continue

            raw_path, line_num, col_num, msg = match.groups()

            # Remove leading slash so pathlib treats it as relative and joins correctly
            rel_path = raw_path.strip().lstrip("/")
            abs_path = (member_path / rel_path).resolve()

            print(f"{abs_path}:{line_num}:{col_num}:{msg}")

    if any_failed:
        sys.exit(1)

    print("✨ All projects verified!", file=sys.stderr)


if __name__ == "__main__":
    main()
