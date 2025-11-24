from pathlib import Path
from tomllib import load
from typing import Any, cast

from common.run_command import run_command


def main():
    with (Path.cwd() / "pyproject.toml").open("rb") as file:
        workspace_toml = load(file)

    for member in cast(list[str], workspace_toml.get("tool", {}).get("uv", {}).get("workspace", {}).get("members", [])):
        member_dir = Path.cwd() / member

        if not (member_dir / "Dockerfile").exists():
            continue

        with (member_dir / "pyproject.toml").open("rb") as file:
            package_toml = load(file)

        package_name = package_toml.get("project", {}).get("name").strip()

        groups = cast(dict[str, Any], package_toml.get("dependency-groups", {})).keys()

        run_command(
            f"uv export "
            f"--package {package_name} "
            f"--output-file {member_dir / 'pylock.toml'} "
            f"--no-default-groups "
            f"--no-emit-workspace "
            f"--frozen"
        )

        for group in groups:
            if group == "dev":
                continue

            run_command(
                f"uv export "
                f"--package {package_name} "
                f"--output-file {member_dir / f'pylock.{group}.toml'} "
                f"--only-group {group} "
                f"--no-default-groups "
                f"--no-emit-workspace "
                f"--frozen"
            )


if __name__ == "__main__":
    main()
