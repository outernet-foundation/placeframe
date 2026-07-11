from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import typer
from bashrun import bash
from pydantic_settings import BaseSettings

from .cache import restore, save
from .ci_step import ci_step
from .license_restore import restore_license
from .setup import configure_git, install_dotnet
from .setup_oras import install_oras
from .unity import prepare_unity_project, resolve_unity_build, unity_batchmode_command
from .git_tags import get_latest_tag_version


class Settings(BaseSettings):
    github_workspace: str


settings = Settings.model_validate({})

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


@app.command()
def main(
    project: str = typer.Option(help="Project name"),
    project_path: Path = typer.Option(help="Path to Unity project"),
    platform: str = typer.Option(help="Target platform"),
    cache_key: str = typer.Option(help="Cache key prefix"),
    run_number: int = typer.Option(0, help="CI run number"),
    branch: str = typer.Option("dev", help="Git branch name"),
    registry: str = typer.Option(help="OCI registry path"),
    build_env: str = typer.Option(
        "", help="Newline-separated KEY=VALUE pairs injected into the Unity build process environment"
    ),
) -> None:
    for line in build_env.splitlines():
        entry = line.strip()
        if not entry:
            continue
        key, separator, value = entry.partition("=")
        if not separator:
            raise SystemExit(f"Invalid --build-env entry (expected KEY=VALUE): {entry!r}")
        os.environ[key.strip()] = value.strip()

    with ci_step("Setup"):
        configure_git(settings.github_workspace)
        install_dotnet("8.0")
        install_oras()
        restore_license()

    branch_slug = branch.replace("/", "-")
    tag = f"{cache_key}-{platform}-{branch_slug}"
    fallback_branch = "dev"
    fallback_tags = [f"{cache_key}-{platform}-{fallback_branch}"] if branch_slug != fallback_branch else None

    with ci_step("Restore library cache"):
        restore(registry, "unity-library", tag, Path("."), fallback_tags=fallback_tags)

    with ci_step("Prepare build"):
        project_config, build_flag, execute_method = resolve_unity_build(project, platform)
        unity_project_path = project_config.path

    with ci_step("Prepare project"):
        prepare_unity_project(unity_project_path)

    with ci_step(f"Build {unity_project_path.name} [{platform}]"):
        command = (
            f"{unity_batchmode_command(unity_project_path, nographics=False)} "
            f"{build_flag} -executeMethod {execute_method}"
        )

        tag_prefix = project_config.tag_prefix
        if tag_prefix:
            version = get_latest_tag_version(f"{tag_prefix}-v") or "0.0.0"
            full_version = f"{version}-dev+{run_number}" if branch != "main" else f"{version}+{run_number}"
            version_file = unity_project_path / ".build-version.json"
            version_file.write_text(json.dumps({"version": full_version, "runNumber": run_number}))
            print(f"Wrote version {full_version} (bundleVersionCode={run_number}) to {version_file}")

        bash(f"{command} -logFile /dev/stdout")

    with ci_step("Save library cache"):
        # PackageCache (~1.6 GiB) is redundant with the shared UPM cache at ~/.cache/Unity/upm/
        package_cache = project_path / "Library" / "PackageCache"
        if package_cache.exists():
            shutil.rmtree(package_cache)

        save(registry, "unity-library", tag, Path("."), [f"{project_path}/Library/"])

    with ci_step("Collect build artifacts"):
        build_directory = project_path / "Build"
        if build_directory.is_dir():
            artifact_directory = Path("/tmp/unity-builds")
            artifact_directory.mkdir(parents=True, exist_ok=True)
            if platform == "linux64":
                shutil.copytree(build_directory, artifact_directory, dirs_exist_ok=True)
            else:
                for file in build_directory.rglob("*"):
                    if file.suffix in {".apk", ".exe"}:
                        shutil.copy2(file, artifact_directory / file.name)
