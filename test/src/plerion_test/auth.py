#!/usr/bin/env python3
from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

import requests  # used only for the token endpoint

KEYCLOAK_REALM = "placeframe-dev"
OIDC_TOKEN_URL = (
    "https://unshared-shawana-hypereutectic.ngrok-free.dev//auth//realms/placeframe-dev/protocol/openid-connect/token"
)
OIDC_CLIENT_ID = "placeframe-api"
OIDC_USERNAME = "user"
OIDC_PASSWORD = "password"

# Expiry skew (seconds), same idea as C# (90s)
TOKEN_SKEW_SECONDS = int(os.getenv("TOKEN_SKEW_SECONDS", "90"))


def password_login() -> str:
    """
    Do a password grant to obtain access + refresh tokens.
    """
    global _token
    data = {"grant_type": "password", "client_id": OIDC_CLIENT_ID, "username": OIDC_USERNAME, "password": OIDC_PASSWORD}
    resp = requests.post(OIDC_TOKEN_URL, data=data, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"Login failed: {resp.status_code} {resp.text[:500]}")
    _token = resp.json()
    _stamp_expiry(_token)
    return _token["access_token"]


def get_or_refresh_token() -> str:
    """
    Mirrors Auth.GetOrRefreshToken() from C#:
    - If access token valid (with skew), use it
    - Else if refresh token valid (with skew), refresh
    - Else do a full password login
    """
    global _token
    now_with_skew = time.time() + TOKEN_SKEW_SECONDS

    # Use current access token if still valid
    if _token and _token.get("access_token") and now_with_skew < _access_exp:
        return _token["access_token"]

    # Try refresh if refresh token still valid
    if _token and _token.get("refresh_token") and now_with_skew < _refresh_exp:
        new_access = _refresh_login()
        if new_access:
            return new_access

    # Otherwise, full login
    return password_login()


def _stamp_expiry(tr: Dict[str, Any]) -> None:
    global _access_exp, _refresh_exp
    now = time.time()
    _access_exp = now + max(0, int(tr.get("expires_in", 0)))
    _refresh_exp = now + max(0, int(tr.get("refresh_expires_in", 0)))


def _refresh_login() -> Optional[str]:
    """
    Try to refresh the access token using the refresh token.
    Returns the new access token or None if refresh failed.
    """
    global _token
    if not _token or not _token.get("refresh_token"):
        return None

    data = {"grant_type": "refresh_token", "client_id": OIDC_CLIENT_ID, "refresh_token": _token["refresh_token"]}
    resp = requests.post(OIDC_TOKEN_URL, data=data, timeout=30)
    if not resp.ok:
        # refresh failed; let caller fall back to full login
        return None

    refreshed = resp.json()
    # Keycloak may rotate refresh tokens—replace the whole payload
    _token = refreshed
    _stamp_expiry(_token)
    return _token.get("access_token")
