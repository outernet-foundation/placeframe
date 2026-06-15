from __future__ import annotations

import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from functools import lru_cache
from os import environ
from pathlib import Path
from typing import cast

from placeframe_stack.modes import parse_env_file
from httpx import AsyncClient, TransportError

from placeframe_api_client import ApiClient, Configuration, DefaultApi, ServerInfo

# Bounds the wait when the local gateway port isn't answering (e.g. the script is run from a different
# machine than the backend), so the fall-back to PUBLIC_URL is prompt rather than hanging on a connect.
LOCAL_PROBE_TIMEOUT = 2.0


@asynccontextmanager
async def authenticated_api_client() -> AsyncIterator[DefaultApi]:
    host = await _resolve_host()
    print(f"placeframe API host: {host}", file=sys.stderr)
    async with ApiClient(Configuration(host=host)) as api_client:
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


# Prefer the gateway's locally-published port when it answers, so a script run on the backend's own
# machine talks to it directly instead of routing the (often large) request out through the public
# tunnel relay and back. PLACEFRAME_API_URL forces a specific host (e.g. a container IP); otherwise
# the local gateway is probed and PUBLIC_URL is the fall-back for a remote run.
async def _resolve_host() -> str:
    override = environ.get("PLACEFRAME_API_URL")
    if override:
        return override

    public_url = _env_value("PUBLIC_URL")
    if not public_url:
        raise RuntimeError("PUBLIC_URL not found in environment or .env")

    local_url = _local_gateway_url()
    if local_url is not None and await _is_reachable(local_url):
        return local_url

    return public_url


# The gateway publishes its cleartext h2c listener on GATEWAY_PORT, so on the backend host it is always
# reachable over plain http at the loopback regardless of PUBLIC_URL's scheme or tunnelled hostname.
def _local_gateway_url() -> str | None:
    port = _env_value("GATEWAY_PORT")
    if not port:
        return None
    return f"http://127.0.0.1:{port}"


async def _is_reachable(base_url: str) -> bool:
    try:
        async with AsyncClient(timeout=LOCAL_PROBE_TIMEOUT) as http:
            response = await http.get(f"{base_url}/server-info")
    except TransportError:
        return False
    return response.status_code == 200


def _env_value(key: str) -> str | None:
    value = environ.get(key)
    if value:
        return value
    return _env_file_values().get(key)


@lru_cache(maxsize=1)
def _env_file_values() -> dict[str, str]:
    try:
        return parse_env_file(_find_env_file())
    except RuntimeError:
        return {}


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
