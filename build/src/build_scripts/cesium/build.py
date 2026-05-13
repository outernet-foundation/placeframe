from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import typer
from common.bash import bash
from pydantic_settings import BaseSettings

from ..shared.cache import restore, save
from ..shared.ci_step import ci_step
from ..shared.setup import configure_git, free_disk_space
from ..shared.setup_oras import install_oras
from .clone import clone
from .paths import get_cesium_build_paths


class Settings(BaseSettings):
    cache_registry: str
    build_number: str
    github_workspace: str


settings = Settings.model_validate({})


class Platform(str, Enum):
    linux = "linux"
    windows = "windows"
    android_arm64 = "android-arm64"
    android_x86_64 = "android-x86_64"


ANDROID_PLATFORMS = (Platform.android_arm64, Platform.android_x86_64)


@dataclass
class PlatformConfig:
    vcpkg_triplet: str
    cmake_extra_args: str
    editor_build: bool
    strip: bool
    editor_output_name: str
    runtime_output_name: str
    standalone_plugin_directory: str
    standalone_generated_directory: str


VCPKG_TRIPLET_LINUX = """\
include("${CMAKE_CURRENT_LIST_DIR}/shared/common.cmake")
set(VCPKG_TARGET_ARCHITECTURE x64)
set(VCPKG_CRT_LINKAGE static)
set(VCPKG_LIBRARY_LINKAGE static)
set(VCPKG_CMAKE_SYSTEM_NAME Linux)
"""

# Upstream cesium-unity ships arm64-android-unity but not an x86_64 variant
# (no consumer Android device shipped on x86_64 until Magic Leap 2). We write
# our own into the overlay path so vcpkg picks it up via VCPKG_OVERLAY_TRIPLETS.
VCPKG_TRIPLET_ANDROID_X64 = """\
include("${CMAKE_CURRENT_LIST_DIR}/shared/common.cmake")
set(VCPKG_TARGET_ARCHITECTURE x64)
set(VCPKG_CRT_LINKAGE static)
set(VCPKG_LIBRARY_LINKAGE static)
set(VCPKG_CMAKE_SYSTEM_NAME Android)
set(VCPKG_CMAKE_SYSTEM_VERSION 21)
set(VCPKG_MAKE_BUILD_TRIPLET "--host=x86_64-linux-android")
set(VCPKG_CMAKE_CONFIGURE_OPTIONS -DANDROID_ABI=x86_64)
set(VCPKG_ENV_PASSTHROUGH "ANDROID_NDK_ROOT")
set(ENV{ANDROID_NDK_HOME} "$ENV{ANDROID_NDK_ROOT}")
"""

# Values below are copied from cesium-unity's own build logic. Cesium doesn't expose these
# in a structured config — they're spread across C# code and CMake files:
#   vcpkg_triplet: native~/vcpkg/triplets/*.cmake (naming convention: {arch}-{os}-unity)
#   cmake_extra_args: Editor/CompileCesiumForUnityNative.cs GetLibraryToBuild()
#   editor/runtime_output_name: Editor/CompileCesiumForUnityNative.cs GetSharedLibraryFilename()
#   standalone_plugin_directory: Editor/CompileCesiumForUnityNative.cs GetDirectoryNameForPlatform()
#   standalone_generated_directory: Runtime/ConfigureReinterop.cs CppOutputPath (#if guards)
PLATFORM_CONFIGS: dict[Platform, PlatformConfig] = {
    Platform.linux: PlatformConfig(
        vcpkg_triplet="x64-linux-unity",
        cmake_extra_args="",
        editor_build=True,
        strip=True,
        editor_output_name="libCesiumForUnityNative-Editor.so",
        runtime_output_name="libCesiumForUnityNative-Runtime.so",
        standalone_plugin_directory="Standalone",
        standalone_generated_directory="Standalone",
    ),
    Platform.windows: PlatformConfig(
        vcpkg_triplet="x64-windows-unity",
        cmake_extra_args="-G Ninja",
        editor_build=True,
        strip=False,
        editor_output_name="CesiumForUnityNative-Editor.dll",
        runtime_output_name="CesiumForUnityNative-Runtime.dll",
        standalone_plugin_directory="Standalone",
        standalone_generated_directory="Standalone",
    ),
    Platform.android_arm64: PlatformConfig(
        vcpkg_triplet="arm64-android-unity",
        # -Wl,-z,max-page-size=16384 forces 16KB ELF segment alignment so the .so
        # loads natively on Android devices with 16KB memory pages. Without it,
        # Android shows a PageSizeMismatchDialog at app launch. arm64-specific:
        # x86_64-android still uses 4KB pages.
        cmake_extra_args=(
            "-DCMAKE_TOOLCHAIN_FILE=extern/android-toolchain.cmake"
            " -DCMAKE_ANDROID_ARCH_ABI=arm64-v8a"
            " -DCMAKE_SHARED_LINKER_FLAGS_INIT=-Wl,-z,max-page-size=16384"
        ),
        editor_build=False,
        strip=False,
        editor_output_name="",
        runtime_output_name="libCesiumForUnityNative-Runtime.so",
        standalone_plugin_directory="Android/arm64",
        standalone_generated_directory="Android",
    ),
    Platform.android_x86_64: PlatformConfig(
        vcpkg_triplet="x64-android-unity",
        cmake_extra_args="-DCMAKE_TOOLCHAIN_FILE=extern/android-toolchain.cmake -DCMAKE_ANDROID_ARCH_ABI=x86_64",
        editor_build=False,
        strip=False,
        editor_output_name="",
        runtime_output_name="libCesiumForUnityNative-Runtime.so",
        standalone_plugin_directory="Android/x86_64",
        standalone_generated_directory="Android",
    ),
}


def cmake_build(native_directory: Path, install_prefix: Path, config: PlatformConfig, *, editor: bool) -> None:
    name = "Editor" if editor else "Standalone"
    generated_directory = "generated-Editor" if editor else f"generated-{config.standalone_generated_directory}"
    bash(
        f"cmake -B build-{name} -S . -DCMAKE_BUILD_TYPE=RelWithDebInfo"
        f" -DCMAKE_INSTALL_PREFIX={install_prefix}"
        f" -DVCPKG_TRIPLET={config.vcpkg_triplet}"
        f" -DVCPKG_OVERLAY_TRIPLETS={native_directory / 'vcpkg' / 'triplets'}"
        f" -DEDITOR={'ON' if editor else 'OFF'}"
        f" -DREINTEROP_GENERATED_DIRECTORY={generated_directory}"
        f" {config.cmake_extra_args}",
        cwd=native_directory,
    )
    bash(f"cmake --build build-{name} --target install --parallel {os.cpu_count() or 4}", cwd=native_directory)


app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


@app.command()
def main(platform: Platform = typer.Option(help="Target platform: linux, windows, or android")) -> None:
    config = PLATFORM_CONFIGS[platform]

    # Codegen output is ABI-agnostic, so both Android ABIs share one codegen cache
    codegen_platform_label = "android" if platform in ANDROID_PLATFORMS else platform.value
    codegen_caches = [f"standalone-{codegen_platform_label}"]
    if config.editor_build:
        codegen_caches.insert(0, f"editor-{codegen_platform_label}")

    native_cache_paths: list[str] = []
    if config.editor_build:
        native_cache_paths.append(f"Editor/{config.editor_output_name}")
        native_cache_paths.append(f"Editor/{config.runtime_output_name}")
    native_cache_paths.append(f"Plugins/{config.standalone_plugin_directory}/{config.runtime_output_name}")

    with ci_step("Setup"):
        configure_git(settings.github_workspace)
        free_disk_space()
        install_oras()
        os.environ["GIT_LFS_SKIP_SMUDGE"] = "1"
        if platform == Platform.linux or platform in ANDROID_PLATFORMS:
            bash("apt-get install -y -qq cmake ninja-build nasm g++ zip unzip curl pkg-config")
        if platform in ANDROID_PLATFORMS:
            os.environ["ANDROID_NDK_ROOT"] = "/opt/unity/Editor/Data/PlaybackEngines/AndroidPlayer/NDK"
        _, package_path = get_cesium_build_paths()

    with ci_step("Restore sources and codegen"):
        clone()
        for label in codegen_caches:
            restore(
                settings.cache_registry, f"cesium-codegen-{label}", settings.build_number, package_path, required=True
            )

    with ci_step("Check native cache"):
        cache_hit = restore(
            settings.cache_registry, f"cesium-native-{platform.value}", settings.build_number, package_path
        )

    if not cache_hit:
        with ci_step("Prepare native build"):
            native_directory = package_path / "native~"
            outputs: list[Path] = []

            if platform == Platform.linux:
                triplet_directory = native_directory / "vcpkg" / "triplets"
                triplet_directory.mkdir(parents=True, exist_ok=True)
                (triplet_directory / "x64-linux-unity.cmake").write_text(VCPKG_TRIPLET_LINUX)
            elif platform == Platform.android_x86_64:
                triplet_directory = native_directory / "vcpkg" / "triplets"
                triplet_directory.mkdir(parents=True, exist_ok=True)
                (triplet_directory / "x64-android-unity.cmake").write_text(VCPKG_TRIPLET_ANDROID_X64)

        if config.editor_build:
            with ci_step("Build editor native"):
                editor_prefix = package_path / "Editor"
                cmake_build(native_directory, editor_prefix, config, editor=True)
                outputs.append(editor_prefix / config.editor_output_name)
                outputs.append(editor_prefix / config.runtime_output_name)

        with ci_step("Build standalone native"):
            standalone_prefix = package_path / "Plugins" / config.standalone_plugin_directory
            cmake_build(native_directory, standalone_prefix, config, editor=False)
            outputs.append(standalone_prefix / config.runtime_output_name)

        with ci_step("Save native cache"):
            if config.strip:
                for path in outputs:
                    bash(f"strip {path}")
            for path in outputs:
                print(f"{path.name}: {path.stat().st_size / (1024 * 1024):.1f} MB")
            save(
                settings.cache_registry,
                f"cesium-native-{platform.value}",
                settings.build_number,
                package_path,
                native_cache_paths,
            )
