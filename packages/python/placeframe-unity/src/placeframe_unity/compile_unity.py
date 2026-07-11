from pathlib import Path
from typing import Annotated

import typer
from bashrun import bash_check_stream

from .unity import prepare_unity_project, resolve_unity_build, unity_batchmode_command

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


def build_unity_project(project: str, build: str) -> list[Path]:
    project_config, build_flag, execute_method = resolve_unity_build(project, build)
    project_path = project_config.path
    prepare_unity_project(project_path)

    build_directory = project_path / "Build"
    before = snapshot_artifacts(build_directory)

    command = (
        f"{unity_batchmode_command(project_path, nographics=False)} {build_flag} "
        f"-executeMethod {execute_method} -logFile /dev/stdout"
    )
    if not bash_check_stream(command):
        raise SystemExit(1)

    after = snapshot_artifacts(build_directory)
    produced = sorted(path for path, modification_time in after.items() if before.get(path) != modification_time)
    if not produced:
        raise SystemExit(
            "Unity exited 0 but no .apk/.exe under Build/ was produced or updated — "
            "the incremental build served a stale artifact. Delete the existing "
            "output under Build/ and the project's Library/Bee/.../build/ tree, then retry."
        )
    return produced


@app.command()
def compile_unity(
    project: Annotated[str, typer.Option(help="Unity project name (directory containing unity-build.json)")],
    build: Annotated[str, typer.Option(help="Build target from the project's builds list (e.g. android-mobile)")],
) -> None:
    for artifact in build_unity_project(project, build):
        print(f"Built: {artifact}")


def snapshot_artifacts(build_directory: Path) -> dict[Path, int]:
    if not build_directory.is_dir():
        return {}
    return {
        path: path.stat().st_mtime_ns for suffix in (".apk", ".exe") for path in build_directory.rglob(f"*{suffix}")
    }
