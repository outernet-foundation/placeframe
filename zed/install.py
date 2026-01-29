import tarfile
import tempfile
from getpass import getpass
from pathlib import Path

from common.run_command import run_command
from typer import Option, run

zed_project = Path(__file__).parent
repo_root = zed_project.parent.parent
common_root = repo_root / "packages/common"
core_root = repo_root / "packages/core"

excluded_paths = [zed_project / ".venv", zed_project / "__pycache__", zed_project / "clients", zed_project / "typings"]
common_exclude_paths = [common_root / "__pycache__", common_root / ".venv"]
core_exclude_paths = [core_root / "__pycache__", core_root / ".venv"]
remote_tarball_path = "/tmp/zed-capture.tar.gz"
install_script_path = zed_project / "install.sh"


# uv run python capture-app/zed/install.py --host tyler@jetson.local
def cli(host: str = Option(..., help="The host address for the Zed application.")):
    print("Creating tarball")
    temporary_file = tempfile.NamedTemporaryFile(prefix="zed-app-", suffix=".tar.gz", delete=False)
    tarball_path = Path(temporary_file.name)
    temporary_file.close()
    with tarfile.open(tarball_path, "w:gz") as tar:
        tar.add(repo_root / "pyproject.toml", arcname=Path("pyproject.toml"))
        tar.add(repo_root / "uv.lock", arcname=Path("uv.lock"))
        for item in zed_project.iterdir():
            if item not in excluded_paths:
                tar.add(item, arcname=Path("capture-app") / "zed" / item.name)
        for item in common_root.iterdir():
            if item not in common_exclude_paths:
                tar.add(item, arcname=Path("packages/common") / item.name)
        for item in core_root.iterdir():
            if item not in core_exclude_paths:
                tar.add(item, arcname=Path("packages/core") / item.name)

    print("Uploading")
    run_command(f"scp {tarball_path} {host}:{remote_tarball_path}")
    run_command(f'scp "{install_script_path}" {host}:/tmp/install.sh')

    pwd = getpass(f"sudo password for {host}: ")  # not echoed

    print("Installing")
    run_command(f'ssh -tt {host} sudo bash /tmp/install.sh "{remote_tarball_path}"', stream_log=True, stdin_text=pwd)


if __name__ == "__main__":
    run(cli)
