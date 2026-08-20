from __future__ import annotations

import shutil

from bashrun import bash

from .paths import get_cesium_build_paths

CESIUM_TAG = "v1.15.3"


def clone() -> None:
    build_directory, package_path = get_cesium_build_paths()
    project_path = build_directory / "CesiumForUnityBuildProject"

    if (package_path / ".git").is_dir():
        print(f"Already cloned: {package_path}")
    else:
        if package_path.exists():
            print(f"Removing non-git directory: {package_path}")
            shutil.rmtree(package_path)
        project_path.mkdir(parents=True, exist_ok=True)
        bash(
            f"git clone --recurse-submodules -b {CESIUM_TAG}"
            f" https://github.com/CesiumGS/cesium-unity.git {package_path}"
        )
    print("Clone complete")
