from typing import Literal

from litestar import Router, get
from pydantic import BaseModel

from ..settings import get_settings


class ServerInfo(BaseModel):
    auth_mode: Literal["keycloak", "disabled"]
    issuer_url: str | None = None
    auth_url: str | None = None
    token_url: str | None = None
    audience: str | None = None


@get("")
async def get_server_info() -> ServerInfo:
    settings = get_settings()
    if settings.auth_mode == "disabled":
        return ServerInfo(auth_mode="disabled")

    return ServerInfo(
        auth_mode="keycloak",
        issuer_url=str(settings.auth_issuer_url),
        auth_url=str(settings.auth_url),
        token_url=str(settings.auth_token_url),
        audience=settings.auth_audience,
    )


router = Router("/server-info", tags=["ServerInfo"], route_handlers=[get_server_info])
