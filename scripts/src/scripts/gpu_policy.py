from __future__ import annotations

from asyncio import run
from os import environ
from re import fullmatch
from typing import Annotated

import httpx
import typer

app = typer.Typer(add_completion=False, no_args_is_help=True)

DEFAULT_BASE_URL = "http://127.0.0.1:5687"
BASE_URL_ENV = "GPU_ORCHESTRATOR_URL"
REQUEST_TIMEOUT_S = 15.0
DURATION_UNITS = {"": 1, "s": 1, "m": 60, "h": 3600}
StateValue = str | int | float | bool | list[str] | None


@app.command()
def status() -> None:
    url = base_url()
    try:
        state = run(_request("GET", url, "/state", None))
    except httpx.HTTPError:
        typer.echo(f"Failed to reach the gpu orchestrator at {url}", err=True)
        raise typer.Exit(1) from None

    for key, value in state.items():
        rendered = str(value)
        if isinstance(value, list):
            rendered = ", ".join(map(str, value)) or "(none)"
        if value is None:
            rendered = "null"
        typer.echo(f"{key}: {rendered}")


@app.command()
def set(
    idle_window: Annotated[
        str | None, typer.Option("--idle-window", help="Localization idle window: 45s, 30m, 2h, bare = seconds")
    ] = None,
    poll_interval: Annotated[
        str | None, typer.Option("--poll-interval", help="Queue poll interval: 5s, 1m, bare = seconds")
    ] = None,
) -> None:
    if idle_window is None and poll_interval is None:
        typer.echo("Nothing to set. Pass --idle-window or --poll-interval", err=True)
        raise typer.Exit(code=2)

    payload: dict[str, int] = {}
    if idle_window is not None:
        payload["idle_window_seconds"] = parse_duration(idle_window)
    if poll_interval is not None:
        payload["poll_interval_seconds"] = parse_duration(poll_interval)

    url = base_url()
    try:
        result = run(_request("PATCH", url, "/policy", payload))
    except httpx.HTTPStatusError as error:
        typer.echo(f"The orchestrator rejected the policy: {rejection_detail(error)}", err=True)
        raise typer.Exit(1) from None
    except httpx.HTTPError:
        typer.echo(f"Failed to reach the gpu orchestrator at {url}", err=True)
        raise typer.Exit(1) from None

    typer.echo(f"idle_window_seconds: {result['idle_window_seconds']}")
    typer.echo(f"poll_interval_seconds: {result['poll_interval_seconds']}")


def parse_duration(spelling: str) -> int:
    match = fullmatch(r"(\d+)([smh]?)", spelling.strip())
    if match is None:
        raise typer.BadParameter(f"not a duration spelling (45s, 30m, 2h, bare = seconds): {spelling!r}")
    value, unit = match.groups()
    return int(value) * DURATION_UNITS[unit]


def base_url() -> str:
    return environ.get(BASE_URL_ENV, DEFAULT_BASE_URL)


async def _request(method: str, url: str, path: str, payload: dict[str, int] | None) -> dict[str, StateValue]:
    async with httpx.AsyncClient() as http:
        response = await http.request(method, f"{url}{path}", json=payload, timeout=REQUEST_TIMEOUT_S)
        response.raise_for_status()
    return dict(response.json())


def rejection_detail(error: httpx.HTTPStatusError) -> str:
    body = error.response.text
    try:
        return str(error.response.json().get("detail", body))
    except ValueError:
        return body


if __name__ == "__main__":
    app()
