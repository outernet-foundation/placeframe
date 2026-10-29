from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.settings import Settings

REQUIRED_ENV = {
    "PUBLIC_URL": "https://stack.example.com",
    "POSTGRES_HOST": "postgres",
    "DATABASE_NAME": "placeframe",
    "DATABASE_API_USER": "placeframe_api_user",
    "DATABASE_API_USER_PASSWORD": "password",
    "DATABASE_AUTH_USER": "placeframe_auth_user",
    "DATABASE_AUTH_USER_PASSWORD": "password",
    "DATABASE_ORCHESTRATION_USER": "placeframe_orchestration_user",
    "DATABASE_ORCHESTRATION_USER_PASSWORD": "password",
    "LOCALIZER_CONTAINER_URL": "http://localizer:8000",
    "LOKI_URL": "http://loki:3100",
    "RECONSTRUCTIONS_BUCKET": "dev-reconstructions",
    "CAPTURES_BUCKET": "captures",
}

AUTH_ENV = ("AUTH_ISSUER_URL", "AUTH_JWKS_URL", "AUTH_AUTHORIZATION_ENDPOINT", "AUTH_TOKEN_ENDPOINT", "AUTH_AUDIENCE")

KEYCLOAK_ENV = {
    "AUTH_ISSUER_URL": "https://stack.example.com/auth/realms/placeframe-dev",
    "AUTH_JWKS_URL": "http://keycloak:8080/realms/placeframe-dev/protocol/openid-connect/certs",
    "AUTH_AUTHORIZATION_ENDPOINT": "https://stack.example.com/auth/realms/placeframe-dev/protocol/openid-connect/auth",
    "AUTH_TOKEN_ENDPOINT": "https://stack.example.com/auth/realms/placeframe-dev/protocol/openid-connect/token",
}


@pytest.fixture(autouse=True)
def isolated_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name, value in REQUIRED_ENV.items():
        monkeypatch.setenv(name, value)
    for name in AUTH_ENV:
        monkeypatch.delenv(name, raising=False)
    for name in ("S3_ENDPOINT_URL", "S3_ACCESS_KEY", "S3_SECRET_KEY"):
        monkeypatch.delenv(name, raising=False)


def build_settings() -> Settings:
    return Settings.model_validate({})


def apply_env(monkeypatch: pytest.MonkeyPatch, values: dict[str, str]) -> None:
    for name, value in values.items():
        monkeypatch.setenv(name, value)


def test_issuer_unset_selects_anonymous() -> None:
    settings = build_settings()

    assert settings.auth_issuer_url is None
    assert settings.auth_jwks_url is None
    assert settings.auth_audience is None


def test_issuer_with_all_urls_selects_keycloak_and_defaults_audience(monkeypatch: pytest.MonkeyPatch) -> None:
    apply_env(monkeypatch, KEYCLOAK_ENV)

    settings = build_settings()

    assert settings.auth_issuer_url is not None
    assert str(settings.auth_issuer_url) == KEYCLOAK_ENV["AUTH_ISSUER_URL"]
    assert settings.auth_audience == "placeframe-api"


def test_empty_string_env_is_treated_as_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in AUTH_ENV:
        monkeypatch.setenv(name, "")

    settings = build_settings()

    assert settings.auth_issuer_url is None
    assert settings.auth_jwks_url is None
    assert settings.auth_audience is None


def test_empty_string_audience_falls_back_to_default(monkeypatch: pytest.MonkeyPatch) -> None:
    apply_env(monkeypatch, KEYCLOAK_ENV)
    monkeypatch.setenv("AUTH_AUDIENCE", "")

    settings = build_settings()

    assert settings.auth_audience == "placeframe-api"


def test_issuer_with_missing_url_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    apply_env(monkeypatch, KEYCLOAK_ENV)
    monkeypatch.delenv("AUTH_TOKEN_ENDPOINT", raising=False)

    with pytest.raises(ValidationError):
        build_settings()


def test_endpoint_without_issuer_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTH_JWKS_URL", KEYCLOAK_ENV["AUTH_JWKS_URL"])

    with pytest.raises(ValidationError):
        build_settings()


def test_cleartext_public_url_with_issuer_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    apply_env(monkeypatch, KEYCLOAK_ENV)
    monkeypatch.setenv("PUBLIC_URL", "http://192.168.1.100:58080")

    with pytest.raises(ValidationError):
        build_settings()


def test_audience_override_is_kept(monkeypatch: pytest.MonkeyPatch) -> None:
    apply_env(monkeypatch, KEYCLOAK_ENV)
    monkeypatch.setenv("AUTH_AUDIENCE", "https://api.example.com")

    settings = build_settings()

    assert settings.auth_audience == "https://api.example.com"
