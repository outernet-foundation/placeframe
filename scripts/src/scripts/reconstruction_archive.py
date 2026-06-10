from asyncio import run
from pathlib import Path
from typing import Annotated, NoReturn
from uuid import UUID

import typer
from placeframe_api_client import ApiException

from .api_auth import authenticated_api_client

app = typer.Typer(add_completion=False, no_args_is_help=True)

# Generous timeout: a reconstruction tar is 100-300 MB and the transfer is a single request.
REQUEST_TIMEOUT = 600.0


@app.command()
def export(
    reconstruction_id: Annotated[UUID, typer.Argument(help="Reconstruction to export")],
    output: Annotated[Path, typer.Argument(help="Path to write the .tar to")],
    anonymous_identity: Annotated[
        str | None, typer.Option(help="x-anonymous-identity UUID for a disabled-auth backend")
    ] = None,
) -> None:
    tar_bytes = run(_export(reconstruction_id, anonymous_identity))
    output.write_bytes(tar_bytes)
    typer.echo(f"Exported reconstruction {reconstruction_id} to {output} ({len(tar_bytes)} bytes)")


@app.command(name="import")
def import_tar(
    tar_path: Annotated[Path, typer.Argument(help="Path to a .tar produced by export")],
    anonymous_identity: Annotated[
        str | None, typer.Option(help="x-anonymous-identity UUID for a disabled-auth backend")
    ] = None,
) -> None:
    reconstruction_id = run(_import(tar_path.read_bytes(), tar_path.name, anonymous_identity))
    typer.echo(f"Imported reconstruction {reconstruction_id} from {tar_path}")


async def _export(reconstruction_id: UUID, anonymous_identity: str | None) -> bytes:
    async with authenticated_api_client(anonymous_identity) as api:
        try:
            return await api.export_reconstruction_tar(id=reconstruction_id, _request_timeout=REQUEST_TIMEOUT)
        except ApiException as exception:
            _fail(exception)


async def _import(tar_bytes: bytes, tar_name: str, anonymous_identity: str | None) -> UUID:
    async with authenticated_api_client(anonymous_identity) as api:
        try:
            reconstruction = await api.import_reconstruction_tar(
                data=(tar_name, tar_bytes), _request_timeout=REQUEST_TIMEOUT
            )
            return reconstruction.id
        except ApiException as exception:
            _fail(exception)


def _fail(exception: ApiException) -> NoReturn:
    typer.echo(f"Request failed: {exception}", err=True)
    raise typer.Exit(1)


if __name__ == "__main__":
    app()
