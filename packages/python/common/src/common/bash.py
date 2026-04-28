# ruff: noqa: S404, S603 — this module is the project's subprocess wrapper
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path
from subprocess import CalledProcessError, Popen, TimeoutExpired
from typing import NoReturn


def _check_no_pipe(command: str) -> None:
    stripped = re.sub(r'"[^"]*"', "", re.sub(r"'[^']*'", "", command))
    if "|" in stripped:
        msg = f"Command contains a pipe: {command!r}. Use bash_pipe() instead."
        raise ValueError(msg)


def bash_output(command: str, *, cwd: Path | None = None, stdin_text: str | None = None) -> str:
    _check_no_pipe(command)
    args = shlex.split(command, posix=(os.name != "nt"))
    shell_mode = os.name == "nt"

    with Popen(
        command if shell_mode else args,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        stdin=subprocess.PIPE if stdin_text else None,
        text=True,
        shell=shell_mode,
    ) as process:
        try:
            stdout, stderr = process.communicate(input=stdin_text)
        except KeyboardInterrupt:
            try:
                process.wait(timeout=5)
            except TimeoutExpired:
                process.kill()
            raise

        if process.returncode != 0:
            if stderr:
                print(stderr, file=sys.stderr, end="")
            raise CalledProcessError(process.returncode, command, output=stdout, stderr=stderr)

        return stdout or ""


def bash(command: str, *, cwd: Path | None = None, stdin_text: str | None = None) -> None:
    _check_no_pipe(command)
    args = shlex.split(command, posix=(os.name != "nt"))
    shell_mode = os.name == "nt"

    with Popen(
        command if shell_mode else args,
        cwd=str(cwd) if cwd else None,
        stdout=sys.stdout,
        stderr=sys.stderr,
        stdin=subprocess.PIPE if stdin_text else None,
        text=True,
        shell=shell_mode,
    ) as process:
        try:
            process.communicate(input=stdin_text)
        except KeyboardInterrupt:
            try:
                process.wait(timeout=5)
            except TimeoutExpired:
                process.kill()
            raise

        if process.returncode != 0:
            raise CalledProcessError(process.returncode, command)


def bash_pipe(*commands: str, cwd: Path | None = None) -> None:
    if len(commands) < 2:
        msg = "bash_pipe requires at least 2 commands"
        raise ValueError(msg)

    processes: list[Popen[bytes]] = []
    try:
        for i, command in enumerate(commands):
            args = shlex.split(command, posix=(os.name != "nt"))
            stdin = processes[-1].stdout if i > 0 else None
            stdout = subprocess.PIPE if i < len(commands) - 1 else sys.stdout
            stderr = sys.stderr if i == len(commands) - 1 else subprocess.DEVNULL
            processes.append(Popen(args, stdin=stdin, stdout=stdout, stderr=stderr, cwd=str(cwd) if cwd else None))
            if i > 0 and processes[-2].stdout:
                processes[-2].stdout.close()

        for process in processes:
            process.wait()
    except KeyboardInterrupt:
        for process in processes:
            try:
                process.wait(timeout=5)
            except TimeoutExpired:
                process.kill()
        raise

    for process in processes:
        if process.returncode != 0:
            raise CalledProcessError(process.returncode, process.args)


def bash_check(command: str, *, cwd: Path | None = None) -> bool:
    _check_no_pipe(command)
    args = shlex.split(command, posix=(os.name != "nt"))
    result = subprocess.run(args, cwd=str(cwd) if cwd else None, capture_output=True)
    return result.returncode == 0


def bash_check_stream(command: str, *, cwd: Path | None = None) -> bool:
    _check_no_pipe(command)
    args = shlex.split(command, posix=(os.name != "nt"))
    result = subprocess.run(args, cwd=str(cwd) if cwd else None)
    return result.returncode == 0


def bash_no_raise(command: str, *, cwd: Path | None = None) -> None:
    _check_no_pipe(command)
    args = shlex.split(command, posix=(os.name != "nt"))
    subprocess.run(args, cwd=str(cwd) if cwd else None)


def bash_handoff(command: str, *, cwd: Path | None = None) -> NoReturn:
    args = shlex.split(command, posix=(os.name != "nt"))

    if cwd:
        os.chdir(cwd)

    if sys.platform != "win32":
        os.execvpe(args[0], args, os.environ)
    else:
        try:
            subprocess.run(args, check=True)
        except subprocess.CalledProcessError as error:
            sys.exit(error.returncode)
        sys.exit(0)
