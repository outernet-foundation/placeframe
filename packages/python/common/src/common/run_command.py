# Vibe code - Opus 4.5
import os
import shlex
import subprocess
import sys
from pathlib import Path
from subprocess import CalledProcessError, Popen, TimeoutExpired


def _parse_command(command: str | list[str]) -> list[str]:
    """Parse a command string into an args list."""
    if isinstance(command, list):
        return command
    return shlex.split(command, posix=(os.name != "nt"))


def exec_command(command: str | list[str], cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
    """Replace the current process with the given command (Unix) or run it (Windows).

    This function only returns on Windows. On Unix, the current process is replaced entirely.
    """
    args = _parse_command(command)

    full_env = {**os.environ, **(env or {})}

    if cwd:
        os.chdir(cwd)

    if sys.platform != "win32":
        os.execvpe(args[0], args, full_env)
    else:
        # Windows fallback - no execvp equivalent
        try:
            subprocess.run(args, env=full_env, check=True)
        except subprocess.CalledProcessError as e:
            sys.exit(e.returncode)


def run_command(
    command: str | list[str],
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    log: bool = False,
    stream_log: bool = False,
    stdin_text: str | None = None,
    verbose_errors: bool = True,
) -> str:
    args = _parse_command(command)

    # Windows needs shell=True for string commands to handle quoting properly
    shell_mode = isinstance(command, str) and os.name == "nt"
    if shell_mode:
        args = command  # Pass original string to shell

    if stream_log:
        print(f"Running (streaming): {command}")
        stdout_target = sys.stdout
        stderr_target = sys.stderr
    else:
        if log:
            print(f"Running command: {command}")
        stdout_target = subprocess.PIPE
        stderr_target = subprocess.PIPE

    try:
        with Popen(
            args,
            cwd=str(cwd) if cwd else None,
            env=env,
            stdout=stdout_target,
            stderr=stderr_target,
            stdin=subprocess.PIPE if stdin_text else None,
            text=True,
            shell=shell_mode,
        ) as process:
            try:
                stdout, stderr = process.communicate(input=stdin_text)
            except KeyboardInterrupt:
                print("\n[User Interrupted] Waiting for build to stop gracefully...")
                try:
                    process.wait(timeout=5)
                except TimeoutExpired:
                    print("[Timeout] Forcing exit...")
                    process.kill()
                raise

            if process.returncode != 0:
                err = CalledProcessError(process.returncode, command)
                err.stdout = stdout
                err.stderr = stderr
                raise err

            return stdout if stdout else ""

    except CalledProcessError as e:
        if verbose_errors:
            print(f"Command failed with exit code {e.returncode}")
            if not stream_log:
                if e.stdout:
                    print(e.stdout)
                if e.stderr:
                    print(e.stderr)
        raise
