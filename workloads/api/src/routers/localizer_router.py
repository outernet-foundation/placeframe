from __future__ import annotations

from httpx import AsyncClient, HTTPError
from litestar.exceptions import HTTPException
from litestar.status_codes import HTTP_503_SERVICE_UNAVAILABLE
from pydantic import BaseModel

from ..settings import get_settings

UNAVAILABLE_DETAIL = "Localization unavailable"


class LocalizerAddress(BaseModel):
    address: str | None


async def resolve_localizer_address() -> str:
    # Query the router for the localizer address only when GPU modes are managed
    settings = get_settings()
    if not settings.gpu_mode_managed:
        # Return the router address unchanged, since unmanaged modes keep the localizer always on
        return str(settings.localizer_router_address)

    try:
        async with AsyncClient() as http:
            response = await http.get(f"{settings.localizer_router_address}/localizer-address")
            response.raise_for_status()
    except HTTPError as e:
        raise HTTPException(status_code=HTTP_503_SERVICE_UNAVAILABLE, detail=UNAVAILABLE_DETAIL) from e

    address = LocalizerAddress.model_validate(response.json()).address

    # If the address is null, reconstruction mode holds the GPU and no localizer runs
    if address is None:
        raise HTTPException(status_code=HTTP_503_SERVICE_UNAVAILABLE, detail=UNAVAILABLE_DETAIL)
    return address
