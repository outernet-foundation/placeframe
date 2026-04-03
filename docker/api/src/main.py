from functools import partial
from os import environ

from common.litestar import create_litestar_app
from litestar.middleware.base import DefineMiddleware
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from litestar.openapi.spec import Components, OAuthFlow, OAuthFlows, SecurityScheme, Server
from litestar.plugins.prometheus import PrometheusConfig, PrometheusController

from .auth import AuthMiddleware
from .routers.capture_sessions import router as capture_sessions_router
from .routers.graph import router as graph_router
from .routers.groups import router as groups_router
from .routers.layers import router as layers_router
from .routers.leases import router as leases_router
from .routers.localization import router as localization_router
from .routers.localization_maps import router as localization_maps_router
from .routers.nodes import router as nodes_router
from .routers.reconstructions import router as reconstructions_router
from .settings import get_settings


class _MetricsController(PrometheusController):
    include_in_schema = False


#####
if environ.get("CODEGEN"):
    middleware: list[partial[AuthMiddleware] | DefineMiddleware] = []

    openapi_config = OpenAPIConfig("Placeframe", "0.1.0", servers=[Server(url="http://localhost:8000")])

else:
    settings = get_settings()

    _prometheus_config = PrometheusConfig(
        app_name="placeframe-api",
        prefix="placeframe",
        group_path=True,
        exclude=[r"^/$", r"^/health/?$", r"^/metrics/?$", r"^/schema(?:/.*)?$"],
    )

    middleware = [
        partial(AuthMiddleware, exclude=[r"^/$", r"^/health/?$", r"^/metrics/?$", r"^/schema(?:/.*)?$"]),
        _prometheus_config.middleware,
    ]

    openapi_config = OpenAPIConfig(
        "Placeframe",
        "0.1.0",
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


app = create_litestar_app(
    [
        capture_sessions_router,
        leases_router,
        reconstructions_router,
        localization_maps_router,
        localization_router,
        groups_router,
        layers_router,
        nodes_router,
        graph_router,
        _MetricsController,
    ],
    openapi_config,
    middleware,
)
