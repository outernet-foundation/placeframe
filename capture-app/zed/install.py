import tarfile
import tempfile
from getpass import getpass
from pathlib import Path

from common.run_command import run_command
from typer import Option, run

root = Path(__file__).parent
common_root = root.parent.parent / "services/visual-localization-system/common"
core_root = root.parent.parent / "services/visual-localization-system/core"

excluded_paths = [root / ".venv", root / "__pycache__", root / "clients", root / "typings"]
common_exclude_paths = [common_root / "__pycache__", common_root / ".venv"]
core_exclude_paths = [core_root / "__pycache__", core_root / ".venv"]
remote_tarball_path = "/tmp/zed-capture.tar.gz"
install_script_path = root / "install.sh"


def cli(host: str = Option(..., help="The host address for the Zed application.")):
    print("Creating tarball")
    temporary_file = tempfile.NamedTemporaryFile(prefix="zed-app-", suffix=".tar.gz", delete=False)
    tarball_path = Path(temporary_file.name)
    temporary_file.close()
    with tarfile.open(tarball_path, "w:gz") as tar:
        for item in root.iterdir():
            if item not in excluded_paths:
                tar.add(item, arcname=Path("capture-app") / "zed" / item.name)
        for item in common_root.iterdir():
            if item not in common_exclude_paths:
                tar.add(item, arcname=Path("services/visual-localization-system/common") / item.name)
        for item in core_root.iterdir():
            if item not in core_exclude_paths:
                tar.add(item, arcname=Path("services/visual-localization-system/core") / item.name)

    print("Uploading")
    run_command(f"scp {tarball_path} {host}:{remote_tarball_path}")
    run_command(f'scp "{install_script_path}" {host}:/tmp/install.sh')

    pwd = getpass(f"sudo password for {host}: ")  # not echoed

    print("Installing")
    run_command(f'ssh -tt {host} sudo bash /tmp/install.sh "{remote_tarball_path}"', stream_log=True, stdin_text=pwd)


if __name__ == "__main__":
    run(cli)
