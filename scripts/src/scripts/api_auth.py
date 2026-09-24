from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from os import environ
from pathlib import Path
from typing import cast

from stack_lifecycle.modes import parse_env_file
from httpx import AsyncClient

from placeframe_api_client import ApiClient, Configuration, DefaultApi, ServerInfo


@asynccontextmanager
async def authenticated_api_client() -> AsyncGenerator[DefaultApi]:
    public_url = _read_public_url()
    async with ApiClient(Configuration(host=public_url)) as api_client:
        # The unauthenticated /server-info endpoint reports how the backend wants to be addressed:
        # a Keycloak bearer token under keycloak mode, or nothing under disabled mode (where every
        # request is the shared anonymous user and no identity header is needed). The generated
        # client emits empty `_auth_settings` and `Configuration.auth_settings()` returns `{}`, so
        # `Configuration(access_token=...)` is dead code — auth goes in as a default header instead.
        server_info = await DefaultApi(api_client).get_server_info()
        if server_info.auth_mode == "keycloak":
            headers = cast(dict[str, str], api_client.default_headers)
            headers["Authorization"] = f"Bearer {await _fetch_keycloak_token(server_info)}"

        yield DefaultApi(api_client)


# Where a client should reach the API, when that differs from how the world reaches it.
# PUBLIC_URL is the stack's public identity -- it configures the gateway's Caddyfile, the OpenAPI
# server list and the issuer URLs, and it is the address phones and the ZED box connect to. When
# the stack is reachable through a relay, a caller running on the same machine as the stack would
# otherwise send every byte out to that relay and back to a container beside it: measured at 295 ms
# against 1.5 ms for /server-info, and 51 s against 1.6 s for one localization. This names the
# short way round without changing what the stack tells the world it is.
API_URL_VAR = "PLACEFRAME_API_URL"


def _read_public_url() -> str:
    """The API's base URL: PLACEFRAME_API_URL if set, else PUBLIC_URL; environment over .env."""
    env_file: dict[str, str] | None = None
    for key in (API_URL_VAR, "PUBLIC_URL"):
        from_environment = environ.get(key)
        if from_environment:
            return from_environment
        if env_file is None:
            env_file = parse_env_file(_find_env_file())
        from_file = env_file.get(key)
        if from_file:
            return from_file

    raise RuntimeError(f"Neither {API_URL_VAR} nor PUBLIC_URL found in environment or .env")


def _find_env_file() -> Path:
    for directory in (Path.cwd(), *Path.cwd().parents):
        candidate = directory / ".env"
        if candidate.is_file():
            return candidate
    raise RuntimeError("No .env found in the current directory or any parent; run from inside the repo")


async def _fetch_keycloak_token(server_info: ServerInfo) -> str:
    if not server_info.token_url or not server_info.audience:
        raise RuntimeError("Keycloak backend did not report token_url and audience in /server-info")

    async with AsyncClient() as http:
        response = await http.post(
            server_info.token_url,
            data={
                "grant_type": "password",
                "client_id": server_info.audience,
                "username": "user",
                "password": "password",
            },
        )
        response.raise_for_status()
    return response.json()["access_token"]
