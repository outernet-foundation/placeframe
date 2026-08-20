from pathlib import Path
from tomllib import load
from typing import Any, cast

import typer
from bashrun import bash, bash_check, bash_output

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


def _normalize_line_endings(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _export_pylock(check: bool, member_dir: Path, package_name: str, group: str | None) -> bool:
    if group:
        pylock = member_dir / f"pylock.{group}.toml"
        group_flags = f"--only-group {group} "
    else:
        pylock = member_dir / "pylock.toml"
        group_flags = "--no-default-groups "

    export_command = (
        f"uv export --format pylock.toml --no-header --package {package_name} {group_flags}--no-emit-local --frozen "
    )

    if check:
        print(f"Checking {pylock}...")
        exported = _normalize_line_endings(bash_output(export_command))
        committed = _normalize_line_endings(pylock.read_text(encoding="utf-8")) if pylock.exists() else ""
        if exported != committed:
            print(f"  STALE: {pylock} is out of date.")
            return True
        print("  OK")
        return False

    bash(export_command + f"--output-file {pylock} ")
    # Normalize line endings in the written file
    text = pylock.read_text(encoding="utf-8")
    with pylock.open("w", encoding="utf-8", newline="\n") as file:
        file.write(text)
    return False


@app.command()
def lock_python(
    check: bool = typer.Option(False, "--check", help="Validate locks without writing. Exit non-zero if stale."),
) -> None:
    stale = False

    # Phase 1: workspace lock
    if check:
        print("Checking uv.lock...")
        if not bash_check("uv lock --check"):
            print("  STALE: uv.lock is out of date. Run 'uv run lock-python' to update.")
            stale = True
        else:
            print("  OK")
    else:
        bash("uv lock")

    # Phase 2: per-service pylock exports
    nn_base_dir = Path.cwd() / "docker" / "neural-networks-base"
    seen_nn_groups: set[str] = set()

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

        stale |= _export_pylock(check, member_dir, package_name, group=None)

        for group in groups:
            if group == "dev":
                continue
            if group.startswith("neural-networks-"):
                if group not in seen_nn_groups:
                    stale |= _export_pylock(check, nn_base_dir, package_name, group=group)
                    seen_nn_groups.add(group)
                continue
            stale |= _export_pylock(check, member_dir, package_name, group=group)

    if check and stale:
        raise SystemExit(1)

    if check:
        print("\nAll Python lock files are up to date.")
