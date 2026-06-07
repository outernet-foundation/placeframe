from __future__ import annotations

import json
import shutil
import sys
import tempfile
from pathlib import Path

import typer
from placeframe_bash import bash, bash_check
from pydantic_settings import BaseSettings

from ..shared.cache import restore
from ..shared.ci_step import ci_step
from ..shared.license_restore import restore_license
from ..shared.setup import configure_git, free_disk_space, install_dotnet, install_node
from ..shared.setup_oras import install_oras
from .clone import clone
from .paths import get_cesium_build_paths


class Settings(BaseSettings):
    cache_registry: str
    build_number: str
    cesium_version: str
    github_workspace: str


settings = Settings.model_validate({})

NATIVE_FILES = [
    # Linux
    "Editor/libCesiumForUnityNative-Editor.so",
    "Editor/libCesiumForUnityNative-Runtime.so",
    "Plugins/Standalone/libCesiumForUnityNative-Runtime.so",
    # Windows
    "Editor/CesiumForUnityNative-Editor.dll",
    "Editor/CesiumForUnityNative-Runtime.dll",
    "Plugins/Standalone/CesiumForUnityNative-Runtime.dll",
    # Android
    "Plugins/Android/arm64/libCesiumForUnityNative-Runtime.so",
    "Plugins/Android/x86_64/libCesiumForUnityNative-Runtime.so",
]

PLATFORM_CODEGEN = [
    ("codegen-csharp-editor-linux", "#if UNITY_EDITOR_LINUX"),
    ("codegen-csharp-editor-windows", "#if UNITY_EDITOR_WIN"),
    ("codegen-csharp-standalone-linux", "#if !UNITY_EDITOR && UNITY_STANDALONE_LINUX"),
    ("codegen-csharp-standalone-windows", "#if !UNITY_EDITOR && UNITY_STANDALONE_WIN"),
    ("codegen-csharp-standalone-android", "#if !UNITY_EDITOR && UNITY_ANDROID"),
]

CODEGEN_LABELS = ["editor-linux", "editor-windows", "standalone-linux", "standalone-windows", "standalone-android"]

NATIVE_PLATFORMS = ["linux", "windows", "android-arm64", "android-x86_64"]

# Mirrors CopyPackageContents in Cesium's own CI:
# https://github.com/CesiumGS/cesium-unity/blob/v1.15.3/Build~/Package.cs#L374-L436
FILES_TO_COPY = [
    "Editor.meta",
    "LICENSE",
    "LICENSE.meta",
    "package.json",
    "package.json.meta",
    "Plugins.meta",
    "README.md",
    "README.md.meta",
    "CHANGES.md",
    "CHANGES.md.meta",
    "Runtime.meta",
    "ThirdParty.json",
    "ThirdParty.json.meta",
]

DIRECTORIES_TO_COPY = ["Editor", "Runtime", "Plugins"]

# https://github.com/CesiumGS/cesium-unity/blob/v1.15.3/Build~/Package.cs#L414-L428
FILES_TO_DELETE = [
    "Editor/CompileCesiumForUnityNative.cs",
    "Editor/CompileCesiumForUnityNative.cs.meta",
    "Editor/BuildCesiumForUnity.cs",
    "Editor/BuildCesiumForUnity.cs.meta",
    "Editor/ConfigureReinterop.cs",
    "Editor/ConfigureReinterop.cs.meta",
    "Editor/csc.rsp",
    "Editor/csc.rsp.meta",
    "Runtime/ConfigureReinterop.cs",
    "Runtime/ConfigureReinterop.cs.meta",
    "Runtime/csc.rsp",
    "Runtime/csc.rsp.meta",
]

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


@app.command()
def main() -> None:
    with ci_step("Setup"):
        configure_git(settings.github_workspace)
        free_disk_space()
        install_dotnet("8.0")
        install_oras()
        install_node("24", "https://registry.npmjs.org")
        restore_license()
        _, package_path = get_cesium_build_paths()
        project_path = package_path.parent.parent

    with ci_step("Restore caches"):
        clone()
        for label in CODEGEN_LABELS:
            restore(
                settings.cache_registry, f"cesium-codegen-{label}", settings.build_number, package_path, required=True
            )
        for platform in NATIVE_PLATFORMS:
            restore(
                settings.cache_registry, f"cesium-native-{platform}", settings.build_number, package_path, required=True
            )

    with ci_step("Combine codegen"):
        for assembly in ["Runtime", "Editor"]:
            generated_directory = package_path / assembly / "generated"
            if generated_directory.exists():
                shutil.rmtree(generated_directory)

        for codegen_directory_name, guard in PLATFORM_CODEGEN:
            codegen_directory = package_path / codegen_directory_name
            if not codegen_directory.exists():
                raise SystemExit(f"Codegen directory not found: {codegen_directory}")
            for assembly_directory in codegen_directory.iterdir():
                if not assembly_directory.is_dir():
                    continue
                reinterop_output = assembly_directory / "Reinterop" / "Reinterop.RoslynSourceGenerator"
                if not reinterop_output.is_dir():
                    print(f"WARNING: Reinterop output not found for {assembly_directory.name}, skipping")
                    continue
                generated_directory = package_path / assembly_directory.name / "generated"
                for source_file in reinterop_output.rglob("*.cs"):
                    relative = source_file.relative_to(reinterop_output.parent)
                    destination = generated_directory / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    content = source_file.read_text().rstrip()
                    with destination.open("a") as file:
                        file.write(f"{guard}\n{content}\n#endif\n")

        for assembly in ["Runtime", "Editor"]:
            reinterop_directory = package_path / assembly / "generated" / "Reinterop.RoslynSourceGenerator"
            if not any(reinterop_directory.rglob("*.cs")):
                raise SystemExit(f"No Reinterop output for {assembly} assembly — codegen cache may be stale")

        # Upstream asmdef only lists Windows; add Linux since we build for both
        asmdef = package_path / "Runtime" / "CesiumRuntime.asmdef"
        asmdef.write_text(
            asmdef.read_text().replace('"WindowsStandalone64"', '"WindowsStandalone64",\n        "LinuxStandalone64"')
        )

        # Must delete before Unity batchmode opens the project, otherwise it compiles
        # both the per-platform sources and the combined output, causing duplicate errors
        for codegen_directory_name, _ in PLATFORM_CODEGEN:
            codegen_directory = package_path / codegen_directory_name
            if codegen_directory.exists():
                shutil.rmtree(codegen_directory)

    with ci_step("Configure native plugins"):
        # Temporarily inject a script that sets PluginImporter platform targeting on
        # native libraries, then remove it so it doesn't ship in the package
        injected_script = project_path / "Assets" / "Editor" / "ConfigureNativePlugins.cs"
        injected_script.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(Path(__file__).resolve().parent / "data" / "ConfigureNativePlugins.cs", injected_script)

        try:
            bash(
                f"xvfb-run unity-editor -batchmode -nographics -quit -projectPath {project_path}"
                f" -executeMethod ConfigureNativePlugins.Configure -logFile /dev/stdout"
            )
        finally:
            if injected_script.exists():
                injected_script.unlink()
            injected_meta = Path(f"{injected_script}.meta")
            if injected_meta.exists():
                injected_meta.unlink()

    with ci_step("Validate .meta files"):
        for relative_path in NATIVE_FILES:
            path = package_path / relative_path
            meta = path.with_suffix(path.suffix + ".meta")
            if not meta.exists():
                raise SystemExit(f".meta file missing: {meta}")
            meta_content = meta.read_text()
            if "PluginImporter" not in meta_content:
                raise SystemExit(f".meta file does not contain PluginImporter: {meta}")
            print(f"\n--- {meta.name} ---")
            print(meta_content)

    with ci_step("Publish package"):
        output_path = Path(tempfile.mkdtemp(prefix="cesium-package-"))

        for filename in FILES_TO_COPY:
            source = package_path / filename
            if source.exists():
                shutil.copy2(source, output_path / filename)

        for directory in DIRECTORIES_TO_COPY:
            source = package_path / directory
            if source.exists():
                shutil.copytree(source, output_path / directory)

        for filename in FILES_TO_DELETE:
            target = output_path / filename
            if target.exists():
                target.unlink()

        package_json = output_path / "package.json"
        package = json.loads(package_json.read_text())
        package["name"] = "org.outernet.cesium-unity"
        package["version"] = f"{settings.cesium_version}-{settings.build_number}"
        package["displayName"] = package["displayName"] + " (Placeframe Fork)"
        package["repository"] = {
            "url": "https://github.com/outernet-foundation/placeframe.git",
            "directory": "packages/unity/com.cesium.unity",
        }
        package_json.write_text(json.dumps(package, indent=2) + "\n")
        print(f"Patched {package_json}: {package['name']}@{package['version']}")

        name = package["name"]
        version = package["version"]
        if bash_check(f"npm view {name}@{version} version", cwd=output_path):
            print(f"FATAL: {name}@{version} already published — bump the package-version input")
            sys.exit(1)
        bash("npm publish --access public --provenance --tag latest", cwd=output_path)
        print(f"Published {name}@{version}")
