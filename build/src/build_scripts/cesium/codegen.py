from __future__ import annotations

import shutil
import tempfile
from enum import Enum
from pathlib import Path

import typer
from placeframe_bash import bash, bash_check_stream
from pydantic_settings import BaseSettings

from ..shared.cache import restore, save
from ..shared.ci_step import ci_step
from ..shared.license_restore import restore_license
from ..shared.setup import configure_git, free_disk_space, install_dotnet
from ..shared.setup_oras import install_oras
from .clone import clone
from .paths import get_cesium_build_paths


class Settings(BaseSettings):
    cache_registry: str
    build_number: str
    github_workspace: str


settings = Settings.model_validate({})

UNITY = "xvfb-run unity-editor -batchmode -nographics"


class Mode(str, Enum):
    editor = "editor"
    standalone = "standalone"


class Platform(str, Enum):
    linux = "linux"
    windows = "windows"
    android = "android"


app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


@app.command()
def main(
    mode: Mode = typer.Option(help="Codegen mode: editor or standalone"),
    platform: Platform = typer.Option(help="Target platform: linux, windows, or android"),
) -> None:
    with ci_step("Setup"):
        configure_git(settings.github_workspace)
        free_disk_space()
        install_dotnet("8.0")
        install_oras()
        restore_license()
        _, package_path = get_cesium_build_paths()
        label = f"{mode.value}-{platform.value}"

    with ci_step("Restore sources and cache"):
        clone()
        cache_hit = restore(settings.cache_registry, f"cesium-codegen-{label}", settings.build_number, package_path)

    if not cache_hit:
        with ci_step("Build Reinterop"):
            project_path = package_path.parent.parent
            codegen_output_directory = package_path / f"codegen-csharp-{label}"

            if mode == Mode.editor:
                assemblies = ["Runtime", "Editor"]
                command = (
                    f"{UNITY} -projectPath {project_path}"
                    " -executeMethod CesiumForUnity.BuildCesiumForUnity.CompileForEditorAndExit -logFile /dev/stdout"
                )
                generated_suffix = "Editor"
                tolerate_failure = False
            else:
                assemblies = ["Runtime"]
                standalone_build_flags = {
                    Platform.linux: "-buildLinux64Player /tmp/throwaway",
                    Platform.windows: "-buildWindows64Player /tmp/throwaway",
                    Platform.android: "-buildTarget Android -executeMethod CompileForAndroidMono.Run",
                }
                standalone_generated_suffixes = {
                    Platform.linux: "Standalone",
                    Platform.windows: "Standalone",
                    Platform.android: "Android",
                }
                command = f"{UNITY} {standalone_build_flags[platform]} -projectPath {project_path} -logFile /dev/stdout"
                generated_suffix = standalone_generated_suffixes[platform]
                tolerate_failure = True
            bash("dotnet publish Reinterop~ -o .", cwd=package_path)
            bash("git restore Reinterop.dll.meta", cwd=package_path)

            if platform == Platform.linux:
                asmdef = package_path / "Runtime" / "CesiumRuntime.asmdef"
                asmdef.write_text(
                    asmdef.read_text().replace(
                        '"WindowsStandalone64"', '"WindowsStandalone64",\n        "LinuxStandalone64"'
                    )
                )

            # Output to a temp directory OUTSIDE the Unity project so the written files
            # don't get picked up as source files during Unity's domain-reload recompilation
            # (which causes duplicate-symbol errors in editor mode).
            temp_codegen_directory = Path(tempfile.gettempdir()) / "cesium-codegen-output" / label
            for assembly in assemblies:
                rsp_path = package_path / assembly / "csc.rsp"
                temp_output = temp_codegen_directory / assembly
                temp_output.mkdir(parents=True, exist_ok=True)
                rsp_path.write_text(rsp_path.read_text().rstrip("\n") + f"\n-generatedfilesout:{temp_output}\n")

            scene_directory = project_path / "Assets" / "Scenes"
            scene_directory.mkdir(parents=True, exist_ok=True)
            (scene_directory / "Empty.unity").write_text("%YAML 1.1\n%TAG !u! tag:unity3d.com,2011:\n")

            if platform == Platform.android:
                editor_directory = project_path / "Assets" / "Editor"
                editor_directory.mkdir(parents=True, exist_ok=True)
                shutil.copy(Path(__file__).parent / "data" / "CompileForAndroidMono.cs", editor_directory)

        with ci_step(f"Run codegen ({label})"):
            if tolerate_failure:
                bash_check_stream(command)
            else:
                bash(command)

        with ci_step("Validate and save cache"):
            if codegen_output_directory.exists():
                shutil.rmtree(codegen_output_directory)
            shutil.copytree(temp_codegen_directory, codegen_output_directory)

            sentinel = (
                package_path
                / "native~"
                / "Runtime"
                / f"generated-{generated_suffix}"
                / "include"
                / "DotNet"
                / "System"
                / "Action1.h"
            )
            if not sentinel.exists():
                raise SystemExit(f"Codegen failed: sentinel header not found at {sentinel}")
            if not any(codegen_output_directory.rglob("*.cs")):
                raise SystemExit("Codegen failed: no C# files generated")
            print("Codegen complete")

            save(
                settings.cache_registry,
                f"cesium-codegen-{label}",
                settings.build_number,
                package_path,
                [f"codegen-csharp-{label}", "native~/*/generated-*"],
            )
