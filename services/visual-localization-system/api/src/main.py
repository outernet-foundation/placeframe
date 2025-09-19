from __future__ import annotations

from os import environ

from common.fastapi import create_fastapi_app
from fastapi.applications import get_openapi

from src.settings import get_settings

from .auth import AuthMiddleware
from .routers.captures import router as captures_router
from .routers.reconstructions import router as reconstructions_router

settings = get_settings()

if environ.get("CODEGEN"):
    app = create_fastapi_app(title="Plerion")
else:
    app = create_fastapi_app(title="Plerion", client_id=settings.keycloak_client_id)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=getattr(app, "version", "0.1.0"),
        routes=app.routes,
        description=getattr(app, "description", None),
    )

    components = openapi_schema.setdefault("components", {})
    security_schemes = components.setdefault("securitySchemes", {})

    if not environ.get("CODEGEN"):
        security_schemes["oauth2"] = {
            "type": "oauth2",
            "flows": {
                "authorizationCode": {
                    "authorizationUrl": f"{settings.keycloak_public_host}realms/{settings.keycloak_realm}/protocol/openid-connect/auth",
                    "tokenUrl": f"{settings.keycloak_public_host}realms/{settings.keycloak_realm}/protocol/openid-connect/token",
                    "scopes": {"openid": "OpenID scope", "email": "Email", "profile": "Profile"},
                }
            },
        }

        security_schemes["bearerAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Paste a raw access token (e.g., from Keycloak).",
        }

    openapi_schema["security"] = [{"oauth2": ["openid"]}, {"bearerAuth": []}]
    app.openapi_schema = openapi_schema

    return app.openapi_schema


app.openapi = custom_openapi

app.add_middleware(
    AuthMiddleware,
    exclude_paths={"/", "/docs", "/docs/oauth2-redirect", "/openapi.json", "/health"},
    exclude_prefixes=("/_dev",),
)

app.include_router(captures_router)
app.include_router(reconstructions_router)
