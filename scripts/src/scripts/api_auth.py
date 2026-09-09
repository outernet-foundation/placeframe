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


def _read_public_url() -> str:
    public_url = environ.get("PUBLIC_URL")
    if not public_url:
        public_url = parse_env_file(_find_env_file()).get("PUBLIC_URL")

    if not public_url:
        raise RuntimeError("PUBLIC_URL not found in environment or .env")
    return public_url


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
