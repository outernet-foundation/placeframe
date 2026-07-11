from __future__ import annotations

import os
import platform
import re
import shlex
import shutil
from pathlib import Path

from bashrun import bash, bash_no_raise, bash_output
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    github_path: str | None = None
    system_drive: str = Field("C:", validation_alias="SystemDrive")
    agent_tools_directory: str | None = Field(None, validation_alias="AGENT_TOOLSDIRECTORY")


settings = Settings.model_validate({})

CONTAINER_PATHS = ["/to_clean/android", "/to_clean/dotnet", "/to_clean/ghcup", "/to_clean/swift"]

BARE_LINUX_PATHS = ["/usr/local/lib/android", "/usr/share/dotnet", "/usr/local/.ghcup", "/usr/share/swift", "/opt/ghc"]

LARGE_PACKAGE_PATTERNS = [
    "^aspnetcore-.*",
    "^dotnet-.*",
    "^llvm-.*",
    "php.*",
    "^mongodb-.*",
    "^mysql-.*",
    "azure-cli",
    "google-chrome-stable",
    "firefox",
    "powershell",
    "mono-devel",
    "libgl1-mesa-dri",
    "google-cloud-sdk",
    "google-cloud-cli",
]


def _remove_paths(paths: list[str], sudo: bool = False) -> None:
    existing = [path for path in paths if Path(path).exists()]
    if not existing:
        return
    if sudo:
        bash_no_raise(f"sudo rm -rf {shlex.join(existing)}")
    elif platform.system() == "Windows":
        for path in existing:
            shutil.rmtree(path, ignore_errors=True)
    else:
        bash_no_raise(f"rm -rf {shlex.join(existing)}")


# actions/checkout sets safe.directory in a temporary HOME that's cleaned up
# after the step finishes (actions/checkout#766). Container jobs that run
# git later need it re-set in the real HOME.
def configure_git(workspace: str) -> None:
    bash(f"git config --global --add safe.directory {shlex.quote(workspace)}")


def free_disk_space(*, large_packages: bool = False, docker_images: bool = False, swap_storage: bool = False) -> None:
    system = platform.system()
    in_container = Path("/to_clean").is_dir()

    if system == "Windows":
        paths = [os.path.join(settings.system_drive, "Program Files", "dotnet")]
        if settings.agent_tools_directory:
            paths.append(settings.agent_tools_directory)
        print(f"Removing: {', '.join(paths)}")
        _remove_paths(paths)
    elif in_container:
        print("Removing pre-installed toolchains (container)")
        _remove_paths(CONTAINER_PATHS)
    else:
        print("Removing pre-installed toolchains")
        _remove_paths(BARE_LINUX_PATHS, sudo=True)

        if large_packages:
            print("Removing large apt packages")
            bash_no_raise(f"sudo apt-get remove -y --fix-missing {shlex.join(LARGE_PACKAGE_PATTERNS)}")
            bash_no_raise("sudo apt-get autoremove -y")
            bash_no_raise("sudo apt-get clean")

        if docker_images:
            print("Pruning Docker images")
            bash_no_raise("sudo docker image prune --all --force")

        if swap_storage:
            print("Removing swap")
            bash_no_raise("sudo swapoff -a")
            bash_no_raise("sudo rm -f /mnt/swapfile")

    bash("df -h")


def install_dotnet(channel: str) -> None:
    print(f"Installing .NET SDK {channel}")
    script = Path(__file__).parent / "third-party" / "dotnet-install.sh"
    bash(f"bash {script} --channel {channel}")
    dotnet_path = str(Path.home() / ".dotnet")
    os.environ["PATH"] = f"{dotnet_path}{os.pathsep}{os.environ['PATH']}"
    if settings.github_path:
        with open(settings.github_path, "a") as file:
            file.write(f"{dotnet_path}\n")


def install_node(version: str, registry_url: str | None = None) -> None:
    system = platform.system()
    sudo = system == "Linux" and os.geteuid() != 0

    print(f"Installing Node.js {version}")
    shasums = bash_output(f"curl -fsSL https://nodejs.org/dist/latest-v{version}.x/SHASUMS256.txt")
    match = re.search(r"(node-v[\d.]+-linux-x64\.tar\.xz)", shasums)
    if not match:
        raise SystemExit(f"Could not find Node.js v{version} linux-x64 binary")
    filename = match.group(1)
    prefix = "sudo " if sudo else ""
    bash(f"curl -fsSLO https://nodejs.org/dist/latest-v{version}.x/{filename}")
    bash(f"{prefix}rm -rf /usr/local/lib/node_modules/npm")
    bash(f"{prefix}tar -xJf {filename} -C /usr/local --strip-components=1")
    Path(filename).unlink()
    if registry_url:
        (Path.home() / ".npmrc").write_text(f"registry={registry_url}\n")
