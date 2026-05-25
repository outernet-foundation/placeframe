import shlex

from common.bash import bash, bash_check, bash_output

from .constants import BOX_SSH_TARGET, SSH_MUX


def ssh_run(command: str, stdin_text: str | None = None) -> None:
    bash(f"ssh {SSH_MUX} {BOX_SSH_TARGET} {shlex.quote(command)}", stdin_text=stdin_text)


def ssh_check(command: str) -> bool:
    return bash_check(f"ssh {SSH_MUX} {BOX_SSH_TARGET} {shlex.quote(command)}")


def ssh_output(command: str) -> str:
    return bash_output(f"ssh {SSH_MUX} {BOX_SSH_TARGET} {shlex.quote(command)}")
