from __future__ import annotations

from os import environ
from typing import Any, Dict, TypeAlias, cast

from common.fastapi import create_fastapi_app
from fastapi.applications import get_openapi

from src.settings import get_settings

from .auth import AuthMiddleware
from .routers.captures import router as captures_router
from .routers.groups import router as groups_router
from .routers.layers import router as layers_router
from .routers.localization_maps import router as localization_maps_router
from .routers.localization_sessions import router as localization_sessions_router
from .routers.nodes import router as nodes_router
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

    _fix_inline_schemas(openapi_schema)

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
app.include_router(localization_maps_router)
app.include_router(localization_sessions_router)
app.include_router(groups_router)
app.include_router(layers_router)
app.include_router(nodes_router)


JSON: TypeAlias = Dict[str, Any]


def _collapse_anyof_null(s: JSON) -> None:
    """If schema is anyOf [X, null], replace with X and mark nullable."""
    anyof = s.get("anyOf")
    if isinstance(anyof, list) and len(anyof) == 2:
        non_null = next((b for b in anyof if not (isinstance(b, dict) and b.get("type") == "null")), None)
        nullish = any(b.get("type") == "null" for b in anyof if isinstance(b, dict))
        if isinstance(non_null, dict) and nullish:
            s.clear()
            s.update(non_null)
            s["nullable"] = True  # openapi-generator understands this hint


def _name_array_items(op_id: str, where: str, s: JSON) -> None:
    _collapse_anyof_null(s)
    if s.get("type") == "array":
        s.pop("title", None)
        items = cast(JSON, s.get("items") or {})
        if isinstance(items, dict):
            items.pop("title", None)
            _collapse_anyof_null(items)
            items.setdefault("nullable", False)
            items.setdefault("x-schema-name", f"{op_id}_{where}_item")
            s["items"] = items


def _fix_inline_schemas(spec: JSON) -> None:
    paths = cast(JSON, spec.get("paths", {}))
    for path, ops in paths.items():
        if not isinstance(ops, dict):
            continue
        for method, op in ops.items():
            if not isinstance(op, dict):
                continue
            op_id = cast(str, op.get("operationId") or f"{method}_{str(path).replace('/', '_')}")
            # parameters
            for p in cast(list[JSON], op.get("parameters", [])):
                if isinstance(p, dict):
                    sch = cast(JSON, p.get("schema") or {})
                    _name_array_items(op_id, f"param_{p.get('name', '_')}", sch)
                    if sch:
                        p["schema"] = sch
            # requestBody
            rb = cast(JSON, op.get("requestBody") or {})
            content = cast(JSON, rb.get("content") or {})
            for ctype, media in content.items():
                if isinstance(media, dict):
                    sch = cast(JSON, media.get("schema") or {})
                    _name_array_items(op_id, f"body_{ctype.replace('/', '_')}", sch)
                    if sch:
                        media["schema"] = sch
            # responses
            resps = cast(JSON, op.get("responses") or {})
            for code, resp in cast(JSON, resps).items():
                if isinstance(resp, dict):
                    content = cast(JSON, resp.get("content") or {})
                    for ctype, media in content.items():
                        if isinstance(media, dict):
                            sch = cast(JSON, media.get("schema") or {})
                            _name_array_items(op_id, f"resp_{code}_{ctype.replace('/', '_')}", sch)
                            if sch:
                                media["schema"] = sch
