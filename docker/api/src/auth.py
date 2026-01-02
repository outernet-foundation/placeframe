from __future__ import annotations

import json
import threading
import time
from typing import Any
from urllib.request import urlopen

import jwt
from jwt import PyJWK
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from litestar.connection import ASGIConnection
from litestar.exceptions import HTTPException
from litestar.middleware import AbstractAuthenticationMiddleware, AuthenticationResult
from litestar.status_codes import HTTP_401_UNAUTHORIZED
from litestar.types import ASGIApp

from .settings import get_settings

settings = get_settings()


class AuthMiddleware(AbstractAuthenticationMiddleware):
    def __init__(self, app: ASGIApp, exclude: list[str]) -> None:
        super().__init__(app, exclude)

        self._time_to_live = 600
        self._expires_at = 0.0
        self._leeway = 60
        self._lock = threading.Lock()
        self._keys: dict[str, dict[str, Any]] = {}

    async def authenticate_request(self, connection: ASGIConnection[Any, Any, Any, Any]) -> AuthenticationResult:
        authorization = connection.headers.get("authorization")
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(HTTP_401_UNAUTHORIZED, "Missing bearer token")

        token = authorization.split(" ", 1)[1].strip()

        try:
            # Parse header
            try:
                header = jwt.get_unverified_header(token)
            except Exception:
                raise HTTPException(HTTP_401_UNAUTHORIZED, "Malformed header")

            # Get key ID
            kid = header.get("kid")
            if not isinstance(kid, str):
                raise HTTPException(HTTP_401_UNAUTHORIZED, "Missing key id")

            # Get key algorithm (default to RS256 if missing)
            alg = header.get("alg")
            if not isinstance(alg, str):
                alg = "RS256"

            # Prevent concurrent refreshes
            with self._lock:
                # Get json web key by ID
                json_web_key = self._keys.get(kid)

                # Refresh if missing or expired
                if not json_web_key or time.time() >= self._expires_at:
                    with urlopen(f"{settings.auth_certs_url}", timeout=5) as resp:
                        json_web_key_set = json.load(resp)

                    self._keys = {key["kid"]: key for key in json_web_key_set.get("keys", []) if "kid" in key}
                    self._expires_at = time.time() + self._time_to_live

                    json_web_key = self._keys.get(kid)

                if json_web_key is None:
                    raise HTTPException(HTTP_401_UNAUTHORIZED, "Unknown key id")

                # Get public key
                public_key = PyJWK.from_dict(json_web_key).key

            # Decode and validate json web token
            claims: dict[str, Any] = jwt.decode(
                token,
                public_key,
                algorithms=[alg],
                audience=settings.auth_audience,
                issuer=str(settings.auth_issuer_url),
                leeway=self._leeway,
                options={"require": ["exp", "iat"]},  # keep 'nbf' optional
            )

        except ExpiredSignatureError as exception:
            raise HTTPException(
                HTTP_401_UNAUTHORIZED, f"Token expired: {str(exception)}" if exception else "Token expired"
            )

        except InvalidTokenError as exception:
            raise HTTPException(
                HTTP_401_UNAUTHORIZED, f"Invalid token: {str(exception)}" if exception else "Invalid token"
            )

        except Exception as exception:
            raise HTTPException(
                HTTP_401_UNAUTHORIZED, f"Unknown exception: {str(exception)}" if exception else "Authentication error"
            )

        if "sub" not in claims:
            raise HTTPException(HTTP_401_UNAUTHORIZED, "Missing subject claim")

        return AuthenticationResult(user=claims["sub"], auth=claims)
