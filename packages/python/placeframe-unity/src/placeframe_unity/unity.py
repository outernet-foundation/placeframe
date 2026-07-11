import shutil
import sys
from pathlib import Path
from typing import TypedDict

from bashrun import bash

from .projects import UnityProject, load_unity_projects


class PlatformConfig(TypedDict):
    build_flag: str
    module: str


PLATFORM_CONFIGS: dict[str, PlatformConfig] = {
    "android-mobile": {"build_flag": "-buildTarget Android", "module": "android"},
    "magicleap": {"build_flag": "-buildTarget Android", "module": "android"},
    "linux64": {"build_flag": "-buildTarget StandaloneLinux64", "module": "linux-il2cpp"},
    "win64": {"build_flag": "-buildTarget Win64", "module": "windows-mono"},
}

UNITYCI_IMAGE_REVISION = "3"
LICENSE_MODULE = "linux-il2cpp"


def find_unity_editor(project_path: Path) -> str:
    if shutil.which("unity-editor"):
        return "unity-editor"

    version = read_editor_version(project_path)

    if sys.platform == "win32":
        candidates = [Path(f"C:/Program Files/Unity/Hub/Editor/{version}/Editor/Unity.exe")]
    else:
        candidates = [
            Path(f"/opt/unity/{version}/Editor/Unity"),
            Path.home() / f"Unity/Hub/Editor/{version}/Editor/Unity",
        ]

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    searched = ", ".join(str(c) for c in candidates)
    raise SystemExit(f"Cannot find Unity {version} editor. Searched: {searched}")


def read_editor_version(project_path: Path) -> str:
    version_file = project_path / "ProjectSettings" / "ProjectVersion.txt"
    if not version_file.exists():
        raise SystemExit(f"Cannot find {version_file} — is this a Unity project?")

    for line in version_file.read_text().splitlines():
        if line.startswith("m_EditorVersion:"):
            return line.split(":", 1)[1].strip()

    raise SystemExit(f"Cannot parse editor version from {version_file}")


def prepare_unity_project(project_path: Path) -> None:
    stale_lockfile = project_path / "Temp" / "UnityLockfile"
    if stale_lockfile.exists():
        stale_lockfile.unlink()

    bash("dotnet tool restore")
    bash(f"dotnet nugetforunity restore {project_path}")


def unity_batchmode_command(project_path: Path, nographics: bool = True) -> str:
    editor = find_unity_editor(project_path)
    # Player builds need a real GfxDevice: Unity 6 compresses Android textures (ASTC/ETC2) on the
    # GPU, and under -nographics the Null device falls back to a path that produces corrupt textures.
    # xvfb-run (added below) supplies the display the dropped -nographics would otherwise stand in for.
    graphics_flag = " -nographics" if nographics else ""
    command = f"{editor} -batchmode{graphics_flag} -quit -projectPath {project_path.resolve()}"
    if sys.platform != "win32":
        if shutil.which("xvfb-run"):
            command = f"xvfb-run {command}"
        # Unity runs `adb kill-server` on Android build teardown; strip the
        # env var so the kill lands on a local daemon, not whatever
        # ADB_SERVER_SOCKET points at.
        command = f"env -u ADB_SERVER_SOCKET {command}"
    return command


def resolve_unity_build(project: str, build: str) -> tuple[UnityProject, str, str]:
    projects = load_unity_projects()
    if project not in projects:
        raise SystemExit(f"Unknown project '{project}'. Valid: {', '.join(projects)}")

    project_config = projects[project]
    valid_builds = project_config.builds or []
    if build not in valid_builds:
        valid = ", ".join(valid_builds) or "(none defined)"
        raise SystemExit(f"Unknown build '{build}' for project '{project}'. Valid: {valid}")

    execute_method = (project_config.execute_methods or {}).get(build)
    if not execute_method:
        raise SystemExit(f"No execute method for project '{project}' build '{build}'")

    if build not in PLATFORM_CONFIGS:
        raise SystemExit(f"No platform config for build '{build}'. Valid: {', '.join(PLATFORM_CONFIGS)}")

    return project_config, PLATFORM_CONFIGS[build]["build_flag"], execute_method
