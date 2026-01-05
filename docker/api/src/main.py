from functools import partial
from logging import getLogger
from os import environ
from typing import Any

from litestar import Litestar, Request, Response, get
from litestar.exceptions import HTTPException
from litestar.handlers import HTTPRouteHandler
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from litestar.openapi.spec import Components, OAuthFlow, OAuthFlows, SecurityScheme, Server
from litestar.response import Redirect
from litestar.types import Method
from litestar.types.internal_types import PathParameterDefinition

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
logger = getLogger("uvicorn.error")


# Make codegened client functions use the same name as their corresponding server functions
def use_handler_name(
    route_handler: HTTPRouteHandler, http_method: Method, path_components: list[str | PathParameterDefinition]
) -> str:
    return route_handler.handler_name


def log_http_exception(request: Request[Any, Any, Any], exc: HTTPException) -> Response[dict[str, Any]]:
    logger.exception(
        "HTTPException %s on %s %s: %r", exc.status_code, request.method, request.url.path, exc.detail, exc_info=exc
    )
    logger.warning("HTTPException %s on %s %s: %r", exc.status_code, request.method, request.url.path, exc.detail)
    return Response(content={"detail": exc.detail}, status_code=exc.status_code)


def log_unhandled_exception(request: Request[Any, Any, Any], exc: Exception) -> Response[dict[str, Any]]:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return Response(content={"detail": "Internal Server Error"}, status_code=500)


if environ.get("CODEGEN"):
    openapi_config = OpenAPIConfig("Plerion", "0.1.0", operation_id_creator=use_handler_name)
else:
    openapi_config = OpenAPIConfig(
        "Plerion",
        "0.1.0",
        operation_id_creator=use_handler_name,
        servers=[Server(url=str(settings.public_url))],
        security=[{"oauth2": ["openid"]}, {"bearerAuth": []}],
        render_plugins=[
            ScalarRenderPlugin(
                options={
                    "authentication": {
                        "preferredSecurityScheme": "oauth2",
                        "securitySchemes": {
                            "oauth2": {
                                "flows": {
                                    "authorizationCode": {
                                        "x-scalar-client-id": settings.auth_audience,
                                        "x-usePkce": "SHA-256",
                                        "selectedScopes": ["openid", "email", "profile"],
                                    }
                                }
                            }
                        },
                    }
                }
            )
        ],
        components=Components(
            security_schemes={
                "oauth2": SecurityScheme(
                    type="oauth2",
                    flows=OAuthFlows(
                        authorization_code=OAuthFlow(
                            authorization_url=str(settings.auth_url),
                            token_url=str(settings.auth_token_url),
                            scopes={"openid": "OpenID scope", "email": "Email", "profile": "Profile"},
                        )
                    ),
                ),
                "bearerAuth": SecurityScheme(
                    type="http",
                    scheme="bearer",
                    bearer_format="JWT",
                    description="Paste a raw access token (e.g., from Keycloak).",
                ),
            }
        ),
    )


middleware: list[partial[AuthMiddleware]] = []
if not environ.get("CODEGEN"):
    middleware.append(partial(AuthMiddleware, exclude=[r"^/$", r"^/health/?$", r"^/schema(?:/.*)?$"]))


@get("/", include_in_schema=False)
async def root() -> Redirect:
    return Redirect(path="/schema")


app = Litestar(
    [
        root,
        capture_sessions_router,
        reconstructions_router,
        localization_maps_router,
        localization_sessions_router,
        groups_router,
        layers_router,
        nodes_router,
    ],
    openapi_config=openapi_config,
    middleware=middleware,
    exception_handlers={HTTPException: log_http_exception, Exception: log_unhandled_exception},
)
