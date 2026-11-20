from __future__ import annotations

from asyncio import run
from typing import Annotated, Literal

import httpx
import typer
from pydantic import BaseModel

from .api_auth import read_public_url

Mode = Literal["localizer", "reconstructor"]

# Keep the timeout above the 10-30s container transition
SWITCH_TIMEOUT_S = 120.0

app = typer.Typer(add_completion=False, no_args_is_help=True)


class ModeResponse(BaseModel):
    mode: Mode


@app.command()
def switch(mode: Annotated[Mode, typer.Argument(help="GPU mode to activate")]) -> None:
    # Switch directly through the gateway's gpu-mode route, never through the API
    url = f"{read_public_url()}/gpu-mode/mode"
    try:
        result = run(_switch(url, mode))
    except httpx.HTTPError:
        typer.echo(f"Failed to reach the mode switcher at {url}", err=True)
        raise typer.Exit(1) from None

    typer.echo(result.mode)


async def _switch(url: str, mode: Mode) -> ModeResponse:
    async with httpx.AsyncClient() as http:
        response = await http.post(url, json={"mode": mode}, timeout=SWITCH_TIMEOUT_S)
        response.raise_for_status()
    return ModeResponse.model_validate(response.json())


if __name__ == "__main__":
    app()
