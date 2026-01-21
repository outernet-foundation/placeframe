from __future__ import annotations

from asyncio import Lock
from time import time
from typing import Any

from httpx import AsyncClient
from jwt import PyJWK, decode, get_unverified_header
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.middleware import AbstractAuthenticationMiddleware, AuthenticationResult
from litestar.types import ASGIApp

from .settings import get_settings

settings = get_settings()


class AuthMiddleware(AbstractAuthenticationMiddleware):
    def __init__(self, app: ASGIApp, exclude: list[str]) -> None:
        super().__init__(app, exclude)

        self._time_to_live = 600
        self._expires_at = 0.0
        self._leeway = 60
        self._lock = Lock()
        self._keys: dict[str, dict[str, Any]] = {}

    async def authenticate_request(self, connection: ASGIConnection[Any, Any, Any, Any]) -> AuthenticationResult:
        authorization = connection.headers.get("authorization")
        if not authorization or not authorization.lower().startswith("bearer "):
            raise NotAuthorizedException("Missing bearer token")

        token = authorization.split(" ", 1)[1].strip()

        try:
            # Parse header
            try:
                header = get_unverified_header(token)
            except Exception:
                raise NotAuthorizedException("Malformed header")

            # Get key ID
            kid = header.get("kid")
            if not isinstance(kid, str):
                raise NotAuthorizedException("Missing key id")

            # Get key algorithm (default to RS256 if missing)
            alg = header.get("alg")
            if not isinstance(alg, str):
                alg = "RS256"

            # Prevent concurrent refreshes
            async with self._lock:
                # Get json web key by ID
                json_web_key = self._keys.get(kid)

                # Refresh if missing or expired
                if not json_web_key or time() >= self._expires_at:
                    async with AsyncClient() as client:
                        resp = await client.get(str(settings.auth_certs_url), timeout=5)
                        resp.raise_for_status()
                        json_web_key_set = resp.json()

                    self._keys = {key["kid"]: key for key in json_web_key_set.get("keys", []) if "kid" in key}
                    self._expires_at = time() + self._time_to_live

                    json_web_key = self._keys.get(kid)

                if json_web_key is None:
                    raise NotAuthorizedException("Unknown key id")

                # Get public key
                public_key = PyJWK.from_dict(json_web_key).key

            # Decode and validate json web token
            claims: dict[str, Any] = decode(
                token,
                public_key,
                algorithms=[alg],
                audience=settings.auth_audience,
                issuer=str(settings.auth_issuer_url),
                leeway=self._leeway,
                options={"require": ["exp", "iat"]},  # keep 'nbf' optional
            )

        except ExpiredSignatureError as exception:
            raise NotAuthorizedException(f"Token expired: {str(exception)}" if exception else "Token expired")

        except InvalidTokenError as exception:
            raise NotAuthorizedException(f"Invalid token: {str(exception)}" if exception else "Invalid token")

        except Exception as exception:
            raise NotAuthorizedException(
                f"Unknown exception: {str(exception)}" if exception else "Authentication error"
            )

        if "sub" not in claims:
            raise NotAuthorizedException("Missing subject claim")

        return AuthenticationResult(user=claims["sub"], auth=claims)
