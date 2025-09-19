import os
import shlex
from pathlib import Path
from subprocess import PIPE, STDOUT, CalledProcessError, Popen, run


def run_command(
    command: str,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    log: bool = False,
    stream_log: bool = False,
) -> str:
    if stream_log:
        print(f"Running (streaming): {command}")
        proc = Popen(
            shlex.split(command, posix=True),
            cwd=str(cwd) if cwd else None,
            stdout=PIPE,
            stderr=STDOUT,
            text=True,
            bufsize=1,
            env=env,
        )
        assert proc.stdout is not None
        try:
            for line in proc.stdout:
                print(line, end="", flush=True)
        finally:
            rc = proc.wait()
            if rc != 0:
                raise CalledProcessError(rc, command)
        return ""
    else:
        try:
            if log:
                print(f"Running command: {command}")

            if os.name == "nt":
                # Let cmd.exe remove the grouping quotes
                process = run(command, shell=True, cwd=cwd, env=env, check=True, text=True, capture_output=True)
            else:
                argv = shlex.split(command, posix=True)
                if log:
                    print("argv:", argv)
                process = run(argv, cwd=cwd, env=env, check=True, text=True, capture_output=True)

            if process.stdout and log:
                print(process.stdout)
            if process.stderr and log:
                print(process.stderr)
            return process.stdout
        except CalledProcessError as e:
            print(f"Command failed with exit code {e.returncode}")
            if e.output:
                print(e.output)
            if e.stderr:
                print(e.stderr)
            raise


# def run_streaming(command: str, cwd: Path | None = None, env: dict[str, str] | None = None) -> None:
#     print(f"Running (streaming): {command}")
#     proc = Popen(
#         shlex.split(command, posix=True),
#         cwd=str(cwd) if cwd else None,
#         stdout=PIPE,
#         stderr=STDOUT,
#         text=True,
#         bufsize=1,
#         env=env,
#     )
#     assert proc.stdout is not None
#     try:
#         for line in proc.stdout:
#             print(line, end="", flush=True)
#     finally:
#         rc = proc.wait()
#         if rc != 0:
#             raise CalledProcessError(rc, command)
