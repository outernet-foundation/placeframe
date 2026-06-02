from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Annotated, Any

import typer
from build_scripts.placeframe.compile_unity import build_unity_project
from build_scripts.placeframe.projects import UnityProjectConfig, load_unity_projects
from common.bash import bash, bash_check, bash_handoff, bash_output

INSTALLABLE_TARGETS = {"android-mobile", "magicleap", "linux64"}
ADB_TARGETS = {"android-mobile", "magicleap"}
CACHE_ROOT = Path.home() / ".placeframe" / "builds"

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


def _resolve_project(projects: dict[str, UnityProjectConfig], name: str) -> str:
    for project_name in projects:
        if project_name.lower() == name.lower():
            return project_name
    valid = ", ".join(projects.keys())
    raise typer.BadParameter(f"Unknown project '{name}'. Valid projects: {valid}")


def _resolve_target(project_config: UnityProjectConfig, project_name: str, target: str | None) -> str:
    installable = [build for build in (project_config.builds or []) if build in INSTALLABLE_TARGETS]
    if target is None:
        if len(installable) == 1:
            return installable[0]
        valid = ", ".join(installable) if installable else "(none)"
        raise typer.BadParameter(
            f"--target is required for {project_name} (multiple installable targets). Valid targets: {valid}"
        )
    for build in installable:
        if build.lower() == target.lower():
            return build
    valid = ", ".join(installable)
    raise typer.BadParameter(f"No installable target '{target}' for {project_name}. Valid targets: {valid}")


def _current_git_branch() -> str:
    branch = bash_output("git rev-parse --abbrev-ref HEAD").strip()
    if branch == "HEAD":
        raise typer.BadParameter("HEAD is detached; pass --branch explicitly")
    return branch


def _find_run_id(artifact_name: str, branch: str) -> str:
    owner_repo = bash_output("gh repo view --json nameWithOwner --jq .nameWithOwner").strip()
    output = bash_output(
        f"gh api repos/{owner_repo}/actions/artifacts?name={artifact_name}&per_page=10 --jq .artifacts"
    )
    artifacts: list[dict[str, Any]] = json.loads(output)
    for artifact in artifacts:
        if artifact["workflow_run"]["head_branch"] == branch:
            return str(artifact["workflow_run"]["id"])
    print(f"No artifact '{artifact_name}' found on branch '{branch}'")
    raise SystemExit(1)


def _download_artifact(run_id: str, artifact_name: str) -> Path:
    cache_path = CACHE_ROOT / run_id / artifact_name
    if cache_path.is_dir() and any(cache_path.iterdir()):
        print(f"Using cached artifact: {cache_path}")
        return cache_path
    cache_path.mkdir(parents=True, exist_ok=True)
    bash(f"gh run download {run_id} --name {artifact_name} --dir {cache_path}")
    return cache_path


def _find_linux_executable(artifact_path: Path) -> Path:
    for item in artifact_path.iterdir():
        if item.is_file() and (artifact_path / f"{item.stem}_Data").is_dir():
            return item
    print("No linux64 executable found in artifact (expected a file with a matching _Data/ directory)")
    raise SystemExit(1)


@app.command()
def main(
    project: Annotated[str, typer.Option("--project", "-p", help="Unity project name")],
    target: Annotated[
        str | None,
        typer.Option("--target", "-t", help="Device target (android-mobile, magicleap, linux64)"),
    ] = None,
    branch: Annotated[
        str | None,
        typer.Option("--branch", "-b", help="Branch to find latest successful run (default: current git branch)"),
    ] = None,
    run: Annotated[int | None, typer.Option("--run", "-r", help="Specific GitHub Actions run ID")] = None,
    serial: Annotated[str | None, typer.Option("--serial", "-s", help="adb device serial")] = None,
    no_grant_permissions: Annotated[
        bool,
        typer.Option(
            "--no-grant-permissions",
            help=(
                "Skip the post-install `adb shell pm grant` calls listed under `grant_permissions` "
                "for the project in unity-projects.json. Permissions are granted by default."
            ),
        ),
    ] = False,
    build_locally: Annotated[
        bool,
        typer.Option(
            "--build",
            "-B",
            help=(
                "Compile the project locally via `compile-unity` and install the produced APK / "
                "linux executable. Skips the GitHub Actions artifact lookup; --branch / --run are ignored."
            ),
        ),
    ] = False,
) -> None:
    projects = load_unity_projects().projects
    project_name = _resolve_project(projects, project)
    target_name = _resolve_target(projects[project_name], project_name, target)

    if serial and target_name not in ADB_TARGETS:
        print(f"Warning: --serial is ignored for target '{target_name}'")

    if build_locally:
        if branch or run:
            print("Warning: --branch / --run are ignored when --build is set")
        produced = build_unity_project(project_name, target_name)
        apks = [path for path in produced if path.suffix == ".apk"]
        executables = [path for path in produced if path.suffix == ".exe"]
    else:
        artifact_name = f"{project_name}-{target_name}"
        resolved_branch = branch or _current_git_branch()
        run_id = str(run) if run else _find_run_id(artifact_name, resolved_branch)
        print(f"Run: {run_id}")
        print(f"Artifact: {artifact_name}")
        download_path = _download_artifact(run_id, artifact_name)
        apks = sorted(download_path.rglob("*.apk"))
        executables = [_find_linux_executable(download_path)] if target_name == "linux64" else []

    if target_name in ADB_TARGETS:
        if not apks:
            print("No .apk found in install source")
            raise SystemExit(1)

        print(f"Installing: {apks[0].name}")
        adb_prefix = f"adb -s {serial}" if serial else "adb"
        package = projects[project_name].package
        if package:
            bash_check(f"{adb_prefix} uninstall {package}")
        bash(f"{adb_prefix} install {apks[0]}")
        permissions = projects[project_name].grant_permissions
        if permissions and not no_grant_permissions:
            if not package:
                raise typer.BadParameter(
                    f"{project_name} has grant_permissions but no 'package' field in unity-projects.json"
                )
            for permission in permissions:
                print(f"Granting {permission} to {package}")
                bash(f"{adb_prefix} shell pm grant {package} {permission}")
        print("Done.")
    else:
        if not executables:
            print("No linux executable found in install source")
            raise SystemExit(1)
        executable = executables[0]
        os.chmod(executable, executable.stat().st_mode | 0o755)
        print(f"Launching: {executable.name}")
        bash_handoff(str(executable))
