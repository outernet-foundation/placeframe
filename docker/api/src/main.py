from __future__ import annotations

from os import environ

from common.fastapi import create_fastapi_app
from common.fix_openapi_schema import fix_inline_schemas, rewrite_nullable_to_union
from fastapi.openapi.utils import get_openapi

from .auth import AuthMiddleware
from .routers.capture_sessions import router as capture_sessions_router
from .routers.groups import router as groups_router
from .routers.layers import router as layers_router
from .routers.localization_maps import router as localization_maps_router
from .routers.localization_sessions import router as localization_sessions_router
from .routers.nodes import router as nodes_router
from .routers.reconstructions import router as reconstructions_router
from .settings import get_settings

settings = get_settings()

if environ.get("CODEGEN"):
    app = create_fastapi_app(title="Plerion")
else:
    app = create_fastapi_app(title="Plerion", client_id=settings.auth_audience)


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
                    "authorizationUrl": str(settings.auth_url),
                    "tokenUrl": str(settings.auth_token_url),
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

    fix_inline_schemas(openapi_schema)
    rewrite_nullable_to_union(openapi_schema)

    app.openapi_schema = openapi_schema

    return app.openapi_schema


app.openapi = custom_openapi

app.add_middleware(
    AuthMiddleware,
    exclude_paths={"/", "/docs", "/docs/oauth2-redirect", "/openapi.json", "/health"},
    exclude_prefixes=("/_dev",),
)

app.include_router(capture_sessions_router)
app.include_router(reconstructions_router)
app.include_router(localization_maps_router)
app.include_router(localization_sessions_router)
app.include_router(groups_router)
app.include_router(layers_router)
app.include_router(nodes_router)
