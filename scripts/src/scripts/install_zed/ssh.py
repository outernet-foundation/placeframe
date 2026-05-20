import tempfile
from logging import getLogger

from common.bash import bash, bash_check, bash_output
from common.ui import note

from .constants import BOX_SSH_TARGET, SSH_KEY, SSH_MUX, SUDOERS_RULE
from .messages import SUDOERS_INSTALL_PROMPT

logger = getLogger(__name__)


def ensure_ssh_key() -> None:
    if SSH_KEY.exists():
        logger.info("ssh_key_exists", extra={"path": str(SSH_KEY)})
        return
    logger.info("generating_ssh_key", extra={"path": str(SSH_KEY)})
    SSH_KEY.parent.mkdir(parents=True, exist_ok=True)
    bash(f'ssh-keygen -t ed25519 -N "" -f {SSH_KEY}')


def ensure_sudoers_on_box() -> None:
    if ssh_check('"test -f /etc/sudoers.d/install-zed"'):
        current = ssh_output('"cat /etc/sudoers.d/install-zed"').strip()
        if current == SUDOERS_RULE:
            logger.info("sudoers_rule_present")
            return
    logger.info("installing_sudoers_rule")
    note(SUDOERS_INSTALL_PROMPT)
    # `sudo install` (not pipe-into-tee) avoids a remote pipeline and
    # works before passwordless sudo exists.
    with tempfile.NamedTemporaryFile(mode="w", suffix=".sudoers") as sudoers_file:
        sudoers_file.write(SUDOERS_RULE + "\n")
        sudoers_file.flush()
        bash(f"scp {SSH_MUX} {sudoers_file.name} {BOX_SSH_TARGET}:/tmp/install-zed.sudoers")
        bash(
            f"ssh -t {SSH_MUX} {BOX_SSH_TARGET}"
            ' "sudo install -m 0440 -o root -g root /tmp/install-zed.sudoers /etc/sudoers.d/install-zed"'
        )
        ssh_run('"rm /tmp/install-zed.sudoers"')


def ssh_run(command: str, stdin_text: str | None = None) -> None:
    bash(f"ssh {SSH_MUX} {BOX_SSH_TARGET} {command}", stdin_text=stdin_text)


def ssh_check(command: str) -> bool:
    return bash_check(f"ssh {SSH_MUX} {BOX_SSH_TARGET} {command}")


def ssh_output(command: str) -> str:
    return bash_output(f"ssh {SSH_MUX} {BOX_SSH_TARGET} {command}")
