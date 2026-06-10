from __future__ import annotations

from asyncio import Lock, Task, create_task
from logging import getLogger
from time import time
from typing import Any

from httpx import AsyncClient
from jwt import PyJWK, decode, get_unverified_header
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.middleware import AbstractAuthenticationMiddleware, AuthenticationResult
from litestar.types import ASGIApp
from pydantic import BaseModel, ConfigDict

from .settings import get_settings

settings = get_settings()
logger = getLogger(__name__)

ALGORITHM = "RS256"


class JsonWebKey(BaseModel):
    model_config = ConfigDict(extra="allow")
    kid: str
    kty: str
    use: str | None = None


class JsonWebKeySet(BaseModel):
    keys: list[JsonWebKey]


class AuthMiddleware(AbstractAuthenticationMiddleware):
    def __init__(self, app: ASGIApp, exclude: list[str]) -> None:
        super().__init__(app, exclude)

        self._time_to_live = 600
        self._failure_cooldown = 5
        self._expires_at = 0.0
        self._next_retry_at = 0.0
        self._leeway = 60
        self._refresh_lock = Lock()
        self._keys: dict[str, Any] = {}
        self._background_refresh: Task[None] | None = None

    async def authenticate_request(self, connection: ASGIConnection[Any, Any, Any, Any]) -> AuthenticationResult:
        if settings.auth_mode == "disabled":
            identity = connection.headers.get("x-anonymous-identity")
            if not identity:
                raise NotAuthorizedException("Missing x-anonymous-identity header")
            return AuthenticationResult(user=identity, auth={"sub": identity})

        authorization = connection.headers.get("authorization")
        if not authorization or not authorization.lower().startswith("bearer "):
            raise NotAuthorizedException("Missing bearer token")

        token = authorization.split(" ", 1)[1].strip()

        try:
            header = get_unverified_header(token)
        except Exception as exception:
            raise NotAuthorizedException(f"Malformed header: {exception}")

        kid = header.get("kid")
        if not isinstance(kid, str):
            raise NotAuthorizedException("Missing key id")

        if header.get("alg") != ALGORITHM:
            raise NotAuthorizedException(f"Unsupported algorithm: {header.get('alg')}")

        public_key = self._keys.get(kid)
        if public_key is None:
            # Nothing cached for this kid — block until we have one.
            await self._refresh()
            public_key = self._keys.get(kid)
            if public_key is None:
                raise NotAuthorizedException("Unknown key id")
        elif time() >= self._expires_at and time() >= self._next_retry_at and self._background_refresh is None:
            # Cached key has aged past the TTL — kick off a refresh and use the cached one for now.
            self._background_refresh = create_task(self._refresh_in_background())

        try:
            claims: dict[str, Any] = decode(
                token,
                public_key,
                algorithms=[ALGORITHM],
                audience=settings.auth_audience,
                issuer=str(settings.auth_issuer_url),
                leeway=self._leeway,
                options={"require": ["exp", "iat", "sub"]},
            )

        except ExpiredSignatureError as exception:
            raise NotAuthorizedException(f"Token expired: {exception}")

        except InvalidTokenError as exception:
            raise NotAuthorizedException(f"Invalid token: {exception}")

        return AuthenticationResult(user=claims["sub"], auth=claims)

    async def _refresh_in_background(self) -> None:
        try:
            await self._refresh()
        except Exception as exception:
            logger.warning("Background JWKS refresh failed: %s: %s", type(exception).__name__, exception)
        finally:
            self._background_refresh = None

    async def _refresh(self) -> None:
        if time() < self._next_retry_at:
            raise NotAuthorizedException("JWKS unavailable (cooldown after recent failure)")

        async with self._refresh_lock:
            # Cooldown checked twice: pre-lock fast-fails new arrivals, in-lock
            # fast-fails waiters queued before the failure. Otherwise N concurrent
            # cold-cache requests serialize through N×timeout sequential fetches.
            if time() < self._next_retry_at:
                raise NotAuthorizedException("JWKS unavailable (cooldown after recent failure)")
            if time() < self._expires_at:
                return
            try:
                async with AsyncClient() as client:
                    response = await client.get(str(settings.auth_certs_url), timeout=2)
                    response.raise_for_status()
                    json_web_key_set = JsonWebKeySet.model_validate(response.json())
            except Exception as exception:
                self._next_retry_at = time() + self._failure_cooldown
                raise NotAuthorizedException(f"JWKS fetch failed: {type(exception).__name__}: {exception}")

            # Skip encryption keys; we only need signing keys.
            self._keys = {
                key.kid: PyJWK.from_dict(key.model_dump()).key for key in json_web_key_set.keys if key.use != "enc"
            }
            self._expires_at = time() + self._time_to_live
            logger.info("JWKS refreshed: %d keys cached", len(self._keys))
