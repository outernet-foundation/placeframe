from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import cast

from httpx import AsyncClient

from placeframe_api_client import ApiClient, Configuration, DefaultApi

REPO_ROOT = Path(__file__).resolve().parents[3]


@asynccontextmanager
async def authenticated_api_client(anonymous_identity: str | None = None) -> AsyncIterator[DefaultApi]:
    public_url = _read_public_url()
    async with ApiClient(Configuration(host=public_url)) as api_client:
        # The generated openapi-generator client emits empty `_auth_settings` on every method
        # and `Configuration.auth_settings()` returns `{}`, so `Configuration(access_token=...)`
        # is dead code. Inject auth as a default header so all requests authenticate: a Keycloak
        # bearer token, or an x-anonymous-identity UUID header against a disabled-auth backend.
        headers = cast(dict[str, str], api_client.default_headers)
        if anonymous_identity is not None:
            headers["x-anonymous-identity"] = anonymous_identity
        else:
            headers["Authorization"] = f"Bearer {await _fetch_keycloak_token(public_url)}"
        yield DefaultApi(api_client)


def _read_public_url() -> str:
    for line in (REPO_ROOT / ".env").read_text().splitlines():
        stripped = line.strip()
        if stripped.startswith("PUBLIC_URL=") and not stripped.startswith("#"):
            return stripped.split("=", 1)[1].strip()
    raise RuntimeError("PUBLIC_URL not found in .env")


async def _fetch_keycloak_token(public_url: str) -> str:
    async with AsyncClient() as http:
        response = await http.post(
            f"{public_url}/auth/realms/placeframe-dev/protocol/openid-connect/token",
            data={
                "grant_type": "password",
                "client_id": "placeframe-api",
                "username": "user",
                "password": "password",
            },
        )
        response.raise_for_status()
    return response.json()["access_token"]
