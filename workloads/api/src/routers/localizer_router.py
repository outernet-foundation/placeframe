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
