from __future__ import annotations

from asyncio import to_thread

from litestar import Router, get, post
from litestar.datastructures import State
from pydantic import BaseModel

from ..docker_lifecycle import ModeSwitcher
from ..settings import Mode


class ModeResponse(BaseModel):
    mode: Mode


class ModeRequest(BaseModel):
    mode: Mode


class LocalizerAddressResponse(BaseModel):
    address: str | None


@get("/mode")
async def get_mode(state: State) -> ModeResponse:
    switcher: ModeSwitcher = state.mode_switcher
    return ModeResponse(mode=switcher.mode)


@post("/mode")
async def set_mode(data: ModeRequest, state: State) -> ModeResponse:
    switcher: ModeSwitcher = state.mode_switcher
    mode = await to_thread(switcher.switch, data.mode)
    return ModeResponse(mode=mode)


@get("/localizer-address")
async def get_localizer_address(state: State) -> LocalizerAddressResponse:
    switcher: ModeSwitcher = state.mode_switcher
    address = await to_thread(switcher.localizer_address)
    return LocalizerAddressResponse(address=address)


router = Router("/", route_handlers=[get_mode, set_mode, get_localizer_address])
