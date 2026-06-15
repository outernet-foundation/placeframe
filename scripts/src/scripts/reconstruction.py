from asyncio import run
from pathlib import Path
from typing import Annotated, NamedTuple, NoReturn
from uuid import UUID

import typer
from placeframe_api_client import (
    ApiException,
    CaptureSessionRead,
    ReconstructionReadWithQueue,
)

from .api_auth import authenticated_api_client

app = typer.Typer(add_completion=False, no_args_is_help=True)

# Generous timeout: a reconstruction tar is 100-300 MB and the transfer is a single request.
REQUEST_TIMEOUT = 600.0


# Reconstructions carry no name or size of their own; both come from the capture session that
# produced them. A row pairs the reconstruction with its session (absent when a reconstruction has
# no capture session, or the session row is gone) into pre-rendered cells for table output.
class ReconstructionRow(NamedTuple):
    id: str
    name: str
    status: str
    created: str
    size: str


@app.command()
def export(
    reconstruction_id: Annotated[UUID, typer.Argument(help="Reconstruction to export")],
    output: Annotated[
        Path | None, typer.Argument(help="Path to write the .tar to (default: ./reconstruction-<id>.tar)")
    ] = None,
    no_capture: Annotated[
        bool,
        typer.Option(
            "--no-capture", help="Emit a reconstruction-only (v1) tar instead of bundling the source capture and map"
        ),
    ] = False,
) -> None:
    tar_bytes = run(_export(reconstruction_id, include_capture=not no_capture))
    destination = output or Path.cwd() / f"reconstruction-{reconstruction_id}.tar"
    destination.write_bytes(tar_bytes)
    typer.echo(f"Exported reconstruction {reconstruction_id} to {destination} ({len(tar_bytes)} bytes)")


@app.command(name="import")
def import_tar(
    tar_path: Annotated[Path, typer.Argument(help="Path to a .tar produced by export")],
) -> None:
    reconstruction_id = run(_import(tar_path.read_bytes(), tar_path.name))
    typer.echo(f"Imported reconstruction {reconstruction_id} from {tar_path}")


@app.command(name="list")
def list_reconstructions() -> None:
    rows = run(_list())
    typer.echo(_render_table(rows))


async def _export(reconstruction_id: UUID, include_capture: bool) -> bytes:
    async with authenticated_api_client() as api:
        try:
            return await api.export_reconstruction_tar(
                id=reconstruction_id, include_capture=include_capture, _request_timeout=REQUEST_TIMEOUT
            )
        except ApiException as exception:
            _fail(exception)


async def _import(tar_bytes: bytes, tar_name: str) -> UUID:
    async with authenticated_api_client() as api:
        try:
            reconstruction = await api.import_reconstruction_tar(
                data=(tar_name, tar_bytes), _request_timeout=REQUEST_TIMEOUT
            )
            return reconstruction.id
        except ApiException as exception:
            _fail(exception)


async def _list() -> list[ReconstructionRow]:
    async with authenticated_api_client() as api:
        try:
            reconstructions = await api.get_reconstructions(_request_timeout=REQUEST_TIMEOUT)
            capture_sessions = await api.get_capture_sessions(_request_timeout=REQUEST_TIMEOUT)
        except ApiException as exception:
            _fail(exception)

    sessions_by_id = {session.id: session for session in capture_sessions}
    ordered = sorted(reconstructions, key=lambda reconstruction: reconstruction.created_at, reverse=True)
    return [
        _to_row(row, sessions_by_id.get(row.capture_session_id) if row.capture_session_id else None) for row in ordered
    ]


def _to_row(reconstruction: ReconstructionReadWithQueue, session: CaptureSessionRead | None) -> ReconstructionRow:
    return ReconstructionRow(
        id=str(reconstruction.id),
        name=session.name if session else "—",
        status=reconstruction.status.value,
        created=reconstruction.created_at.date().isoformat(),
        size=_format_size(session.size_bytes) if session else "—",
    )


def _format_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def _render_table(rows: list[ReconstructionRow]) -> str:
    if not rows:
        return "No reconstructions found."

    header = ReconstructionRow("ID", "Name", "Status", "Created", "Size")
    widths = [max(len(cell) for cell in column) for column in zip(header, *rows)]
    separator = ReconstructionRow(*("-" * width for width in widths))
    return "\n".join(
        "  ".join(cell.ljust(width) for cell, width in zip(row, widths)) for row in (header, separator, *rows)
    )


def _fail(exception: ApiException) -> NoReturn:
    typer.echo(f"Request failed: {exception}", err=True)
    raise typer.Exit(1)


if __name__ == "__main__":
    app()
