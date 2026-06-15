from asyncio import run
from json import JSONDecodeError, loads
from pathlib import Path
from typing import Annotated, NamedTuple, NoReturn
from uuid import UUID

import typer
from placeframe_api_client import (
    ApiException,
    CaptureSessionRead,
    DefaultApi,
    ReconstructionCreate,
    ReconstructionCreateWithOptions,
    ReconstructionOptions,
    ReconstructionReadWithQueue,
)
from pydantic import ValidationError

from .api_auth import authenticated_api_client
from .tar_naming import export_destination

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
        Path | None, typer.Argument(help="Path to write the .tar to (default: ./<name>.tar in cwd)")
    ] = None,
    no_capture: Annotated[
        bool,
        typer.Option(
            "--no-capture", help="Emit a reconstruction-only (v1) tar instead of bundling the source capture and map"
        ),
    ] = False,
) -> None:
    tar_bytes, name = run(_export(reconstruction_id, include_capture=not no_capture, need_name=output is None))
    destination = output or export_destination(name or str(reconstruction_id), reconstruction_id, Path.cwd())
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


@app.command()
def create(
    capture: Annotated[str, typer.Argument(help="Capture session name or UUID to reconstruct")],
    options_json: Annotated[
        str | None,
        typer.Option(
            "--options-json",
            help="JSON object of ReconstructionOptions overrides; omitted keys keep server defaults",
        ),
    ] = None,
) -> None:
    options = _parse_options(options_json)
    reconstruction_id, queue_position = run(_create(capture, options))
    typer.echo(f"Queued reconstruction {reconstruction_id} for {capture} (queue position {queue_position})")


async def _export(reconstruction_id: UUID, include_capture: bool, need_name: bool) -> tuple[bytes, str | None]:
    async with authenticated_api_client() as api:
        try:
            tar_bytes = await api.export_reconstruction_tar(
                id=reconstruction_id, include_capture=include_capture, _request_timeout=REQUEST_TIMEOUT
            )
            name = await _capture_name(api, reconstruction_id) if need_name else None
            return tar_bytes, name
        except ApiException as exception:
            _fail(f"Request failed: {exception}")


async def _capture_name(api: DefaultApi, reconstruction_id: UUID) -> str | None:
    reconstructions = await api.get_reconstructions(ids=[reconstruction_id], _request_timeout=REQUEST_TIMEOUT)
    capture_session_id = reconstructions[0].capture_session_id if reconstructions else None
    if capture_session_id is None:
        return None

    captures = await api.get_capture_sessions(ids=[capture_session_id], _request_timeout=REQUEST_TIMEOUT)
    return captures[0].name if captures else None


async def _import(tar_bytes: bytes, tar_name: str) -> UUID:
    async with authenticated_api_client() as api:
        try:
            reconstruction = await api.import_reconstruction_tar(
                data=(tar_name, tar_bytes), _request_timeout=REQUEST_TIMEOUT
            )
            return reconstruction.id
        except ApiException as exception:
            _fail(f"Request failed: {exception}")


async def _list() -> list[ReconstructionRow]:
    async with authenticated_api_client() as api:
        try:
            reconstructions = await api.get_reconstructions(_request_timeout=REQUEST_TIMEOUT)
            capture_sessions = await api.get_capture_sessions(_request_timeout=REQUEST_TIMEOUT)
        except ApiException as exception:
            _fail(f"Request failed: {exception}")

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


async def _create(capture: str, options: ReconstructionOptions) -> tuple[UUID, int | None]:
    async with authenticated_api_client() as api:
        try:
            capture_session_id = await _resolve_capture_session(api, capture)
            reconstruction = await api.create_reconstruction(
                ReconstructionCreateWithOptions(
                    create=ReconstructionCreate(capture_session_id=capture_session_id),
                    options=options,
                ),
                _request_timeout=REQUEST_TIMEOUT,
            )
            return reconstruction.id, reconstruction.queue_position
        except ApiException as exception:
            _fail(f"Request failed: {exception}")


async def _resolve_capture_session(api: DefaultApi, capture: str) -> UUID:
    explicit_id = _as_uuid(capture)
    if explicit_id is not None:
        return explicit_id

    sessions = await api.get_capture_sessions(_request_timeout=REQUEST_TIMEOUT)
    matches = [session for session in sessions if session.name == capture]
    if not matches:
        _fail(f"No capture session named {capture!r}")
    if len(matches) > 1:
        _fail(f"Multiple capture sessions named {capture!r}; pass a UUID instead")
    return matches[0].id


def _as_uuid(value: str) -> UUID | None:
    try:
        return UUID(value)
    except ValueError:
        return None


def _parse_options(options_json: str | None) -> ReconstructionOptions:
    if options_json is None:
        return ReconstructionOptions()

    try:
        return ReconstructionOptions.model_validate(loads(options_json))
    except (JSONDecodeError, ValidationError) as exception:
        _fail(f"Invalid --options-json: {exception}")


def _fail(message: str) -> NoReturn:
    typer.echo(message, err=True)
    raise typer.Exit(1)


if __name__ == "__main__":
    app()
