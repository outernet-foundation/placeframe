from __future__ import annotations

from httpx import AsyncClient, HTTPError
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_503_SERVICE_UNAVAILABLE
from pydantic import BaseModel

from ..settings import get_settings

UNAVAILABLE_DETAIL = "Localization unavailable"


class LocalizerAddress(BaseModel):
    address: str | None


# The managed-conditional contract: when GPU_MODE_MANAGED is true (compose — the mode
# switcher may have the localizer stopped), localizer availability is learned at request
# time by querying the router at <LOCALIZER_ROUTER_ADDRESS>/localizer-address; a null
# address and an unreachable router both collapse to 503 "Localization unavailable" (the
# status code is the client contract — the shared 5xx handler masks the detail body, and
# the client gets the "why" from the mode switcher directly). When GPU_MODE_MANAGED is
# false (k8s — the localizer is always-on), the API never queries: the router address IS
# the localizer address, and the 503 path cannot trigger. A config-driven branch on
# settings, not platform detection — the same shape as auth_mode.
async def resolve_localizer_address() -> str:
    settings = get_settings()
    if not settings.gpu_mode_managed:
        return str(settings.localizer_router_address)

    try:
        async with AsyncClient() as http:
            response = await http.get(f"{settings.localizer_router_address}/localizer-address")
            response.raise_for_status()
    except HTTPError as e:
        raise HTTPException(status_code=HTTP_503_SERVICE_UNAVAILABLE, detail=UNAVAILABLE_DETAIL) from e

    address = LocalizerAddress.model_validate(response.json()).address
    if address is None:
        raise HTTPException(status_code=HTTP_503_SERVICE_UNAVAILABLE, detail=UNAVAILABLE_DETAIL)
    return address
