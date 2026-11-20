from typing import Literal

from litestar import Router, get
from pydantic import BaseModel

from ..settings import get_settings


class ServerInfo(BaseModel):
    auth_mode: Literal["keycloak", "disabled"]
    gpu_mode_managed: bool
    issuer_url: str | None = None
    auth_url: str | None = None
    token_url: str | None = None
    audience: str | None = None


@get("")
async def get_server_info() -> ServerInfo:
    settings = get_settings()
    if settings.auth_issuer_url is None:
        return ServerInfo(auth_mode="disabled", gpu_mode_managed=settings.gpu_mode_managed)

    return ServerInfo(
        auth_mode="keycloak",
        gpu_mode_managed=settings.gpu_mode_managed,
        issuer_url=str(settings.auth_issuer_url),
        auth_url=str(settings.auth_authorization_endpoint),
        token_url=str(settings.auth_token_endpoint),
        audience=settings.auth_audience,
    )


router = Router("/server-info", tags=["ServerInfo"], route_handlers=[get_server_info])
