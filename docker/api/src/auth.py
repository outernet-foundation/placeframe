# auth.py
from __future__ import annotations

import json
import threading
import time
from typing import Any, Awaitable, Callable
from urllib.request import urlopen

import jwt
from fastapi import Request
from jwt import PyJWK
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN
from starlette.types import ASGIApp

from .settings import get_settings

settings = get_settings()


class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, exclude_paths: set[str], exclude_prefixes: tuple[str, ...]) -> None:
        super().__init__(app)

        self._time_to_live = 600
        self._expires_at = 0.0
        self._leeway = 60
        self._lock = threading.Lock()
        self._keys: dict[str, dict[str, Any]] = {}
        self.exclude_paths = exclude_paths
        self.exclude_prefixes = exclude_prefixes

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.url.path in self.exclude_paths or request.url.path.startswith(self.exclude_prefixes):
            return await call_next(request)

        authorization = request.headers.get("authorization")
        if not authorization or not authorization.lower().startswith("bearer "):
            return JSONResponse({"detail": "Missing bearer token"}, status_code=HTTP_401_UNAUTHORIZED)

        token = authorization.split(" ", 1)[1].strip()

        try:
            # Parse header
            try:
                header = jwt.get_unverified_header(token)
            except Exception:
                return JSONResponse({"detail": "unauthorized: malformed header"}, status_code=HTTP_401_UNAUTHORIZED)

            # Get key ID
            kid = header.get("kid")
            if not isinstance(kid, str):
                return JSONResponse({"detail": "unauthorized: missing kid"}, status_code=HTTP_401_UNAUTHORIZED)

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
                    return JSONResponse({"detail": "unauthorized: unknown key id"}, status_code=HTTP_401_UNAUTHORIZED)

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

        except ExpiredSignatureError:
            return JSONResponse({"detail": "unauthorized: token expired"}, status_code=HTTP_401_UNAUTHORIZED)

        except InvalidTokenError as exception:
            return JSONResponse(
                {"detail": f"unauthorized: {str(exception) or 'invalid token'}"}, status_code=HTTP_401_UNAUTHORIZED
            )

        if "sub" not in claims:
            return JSONResponse({"detail": "forbidden: missing sub"}, status_code=HTTP_403_FORBIDDEN)

        # 5) Stash for downstream (DB dep will SET LOCAL GUCs from these)
        request.state.claims = claims
        return await call_next(request)
