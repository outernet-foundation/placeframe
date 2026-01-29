from functools import partial
from os import environ

from common.litestar import create_litestar_app
from litestar.openapi.config import OpenAPIConfig
from litestar.openapi.plugins import ScalarRenderPlugin
from litestar.openapi.spec import Components, OAuthFlow, OAuthFlows, SecurityScheme, Server

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

if environ.get("CODEGEN"):
    middleware: list[partial[AuthMiddleware]] = []

    openapi_config = OpenAPIConfig("Placeframe", "0.1.0", servers=[Server(url="http://localhost:8000")])

else:
    settings = get_settings()

    middleware = [partial(AuthMiddleware, exclude=[r"^/$", r"^/health/?$", r"^/schema(?:/.*)?$"])]

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
    ],
    openapi_config,
    middleware,
)
