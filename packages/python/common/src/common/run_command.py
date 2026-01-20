import os
import shlex
import subprocess
import sys
from pathlib import Path
from subprocess import CalledProcessError, Popen, TimeoutExpired


def run_command(
    command: str | list[str],
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    log: bool = False,
    stream_log: bool = False,
    stdin_text: str | None = None,
    verbose_errors: bool = True,
) -> str:
    # Prepare args based on OS
    if isinstance(command, str):
        if os.name == "nt":
            # On Windows, strictly let cmd.exe handle the string if possible
            args = command
            shell_mode = True
        else:
            args = shlex.split(command, posix=True)
            shell_mode = False
    else:
        args = command
        shell_mode = False

    if stream_log:
        print(f"Running (streaming): {command}")
        stdout_target = sys.stdout
        stderr_target = sys.stderr
    else:
        if log:
            print(f"Running command: {command}")
        stdout_target = subprocess.PIPE
        stderr_target = subprocess.PIPE

    # START: Smart Process Management
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
                # communicate() blocks until the process exits
                stdout, stderr = process.communicate(input=stdin_text)
            except KeyboardInterrupt:
                # KEY FIX: Catch Ctrl+C and wait for Docker to cancel gracefully
                print("\n[User Interrupted] Waiting for build to stop gracefully...")
                try:
                    # Give Docker 5 seconds to rollback/cleanup
                    process.wait(timeout=5)
                except TimeoutExpired:
                    print("[Timeout] Forcing exit...")
                    process.kill()
                raise  # Re-raise to stop the script

            if process.returncode != 0:
                # Construct a CalledProcessError to match original behavior
                err = CalledProcessError(process.returncode, command)
                # Attach output manually since Popen doesn't do it automatically like run()
                err.stdout = stdout
                err.stderr = stderr
                raise err

            return stdout if stdout else ""

    except CalledProcessError as e:
        if verbose_errors:
            print(f"Command failed with exit code {e.returncode}")
            if stream_log:
                pass  # Logs were already streamed to console
            else:
                if e.stdout:
                    print(e.stdout)
                if e.stderr:
                    print(e.stderr)
        raise
