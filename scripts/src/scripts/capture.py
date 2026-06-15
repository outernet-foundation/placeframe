from asyncio import run
from pathlib import Path
from typing import Annotated, NamedTuple, NoReturn
from uuid import UUID

import typer
from placeframe_api_client import ApiException, CaptureSessionRead

from .api_auth import authenticated_api_client

app = typer.Typer(add_completion=False, no_args_is_help=True)

# Generous timeout: a capture tar is 500 MB-2 GB and the transfer is a single request.
REQUEST_TIMEOUT = 600.0


class CaptureRow(NamedTuple):
    id: str
    name: str
    device: str
    recorded: str
    size: str


@app.command()
def export(
    capture_session_id: Annotated[UUID, typer.Argument(help="Capture session to export")],
    output: Annotated[Path, typer.Argument(help="Path to write the .tar to")],
) -> None:
    tar_bytes = run(_export(capture_session_id))
    output.write_bytes(tar_bytes)
    typer.echo(f"Exported capture session {capture_session_id} to {output} ({len(tar_bytes)} bytes)")


@app.command(name="import")
def import_tar(
    tar_path: Annotated[Path, typer.Argument(help="Path to a .tar produced by export")],
) -> None:
    capture_session_id = run(_import(tar_path.read_bytes(), tar_path.name))
    typer.echo(f"Imported capture session {capture_session_id} from {tar_path}")


@app.command(name="list")
def list_captures() -> None:
    rows = run(_list())
    typer.echo(_render_table(rows))


async def _export(capture_session_id: UUID) -> bytes:
    async with authenticated_api_client() as api:
        try:
            return await api.export_capture_session(id=capture_session_id, _request_timeout=REQUEST_TIMEOUT)
        except ApiException as exception:
            _fail(exception)


async def _import(tar_bytes: bytes, tar_name: str) -> UUID:
    async with authenticated_api_client() as api:
        try:
            capture = await api.import_capture_session(data=(tar_name, tar_bytes), _request_timeout=REQUEST_TIMEOUT)
            return capture.id
        except ApiException as exception:
            _fail(exception)


async def _list() -> list[CaptureRow]:
    async with authenticated_api_client() as api:
        try:
            captures = await api.get_capture_sessions(_request_timeout=REQUEST_TIMEOUT)
        except ApiException as exception:
            _fail(exception)

    ordered = sorted(captures, key=lambda capture: capture.recorded_at, reverse=True)
    return [_to_row(capture) for capture in ordered]


def _to_row(capture: CaptureSessionRead) -> CaptureRow:
    return CaptureRow(
        id=str(capture.id),
        name=capture.name,
        device=capture.device_type.value,
        recorded=capture.recorded_at.date().isoformat(),
        size=_format_size(capture.size_bytes),
    )


def _format_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _render_table(rows: list[CaptureRow]) -> str:
    if not rows:
        return "No capture sessions found."

    header = CaptureRow("ID", "Name", "Device", "Recorded", "Size")
    widths = [max(len(cell) for cell in column) for column in zip(header, *rows)]
    separator = CaptureRow(*("-" * width for width in widths))
    return "\n".join(
        "  ".join(cell.ljust(width) for cell, width in zip(row, widths)) for row in (header, separator, *rows)
    )


def _fail(exception: ApiException) -> NoReturn:
    typer.echo(f"Request failed: {exception}", err=True)
    raise typer.Exit(1)


if __name__ == "__main__":
    app()
