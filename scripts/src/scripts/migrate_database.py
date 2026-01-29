from os import X_OK, access, environ
from os.path import expanduser, isfile
from shutil import which

from common.run_command import run_command
from typer import Option, run

DATABASE = "placeframe"
DDL_PATH = "database"


def cli(allow_hazards: list[str] | None = Option(None)):
    pg_schema_diff_path = _find_pg_schema_diff()
    migrator_dsn = (
        f"postgresql://{DATABASE}_owner:password@localhost:55432/{DATABASE}?options=-c%20check_function_bodies%3Doff"
    )

    command = f"{pg_schema_diff_path} apply --from-dsn {migrator_dsn} --to-dir {DDL_PATH} --skip-confirm-prompt "

    if allow_hazards:
        command += f"--allow-hazards {','.join(allow_hazards)}"

    run_command(command, log=True)


def _find_pg_schema_diff() -> str:
    exe = environ.get("PG_SCHEMA_DIFF")
    if exe and which(exe):
        return exe

    exe = which("pg-schema-diff")
    if exe:
        return exe

    for p in (
        expanduser("~/go/bin/pg-schema-diff"),
        expanduser("~/.local/bin/pg-schema-diff"),
        "/usr/local/bin/pg-schema-diff",
    ):
        if isfile(p) and access(p, X_OK):
            return p

    raise FileNotFoundError("pg-schema-diff not found; add it to PATH or set $PG_SCHEMA_DIFF")


def main():
    run(cli)


if __name__ == "__main__":
    main()
