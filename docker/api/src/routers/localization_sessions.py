from typing import Annotated
from uuid import UUID, uuid4

from common.docker_compose_client import create_service, destroy_service, get_service_status
from core.axis_convention import AxisConvention
from core.camera_config import PinholeCameraConfig
from core.localization_metrics import LocalizationMetrics
from core.transform import Float3, Float4, Transform
from datamodels.public_dtos import LocalizationSessionRead, localization_session_to_dto
from datamodels.public_tables import LocalizationMap, LocalizationSession
from fastapi.exceptions import HTTPException
from litestar import Router, delete, get, post, put
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotFoundException
from litestar.params import Body, Parameter
from plerion_localizer_client import ApiClient, Configuration
from plerion_localizer_client.api.default_api import DefaultApi
from plerion_localizer_client.models.axis_convention import AxisConvention as LocalizerAxisConvention

# from plerion_localizer_client.models.camera import Camera as LocalizeCamera
from plerion_localizer_client.models.load_state_response import LoadStateResponse
from plerion_localizer_client.models.pinhole_camera_config import PinholeCameraConfig as LocalizerPinholeCameraConfig
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..settings import get_settings
from .localization_maps import fetch_localization_maps

settings = get_settings()

SESSION_PORT = 8000  # internal port exposed by the session container


@post("")
async def create_localization_session(session: AsyncSession) -> LocalizationSessionRead:
    row = LocalizationSession(id=uuid4())
    container_name = f"localizer-{row.id}"
    row.container_id = create_service(
        settings.localizer_service, container_name, environment={"SESSION_ID": str(row.id)}
    )
    row.container_url = str(f"http://{container_name}:{SESSION_PORT}")

    session.add(row)

    await session.flush()
    await session.refresh(row)

    return localization_session_to_dto(row)


@delete("/{localization_session_id:uuid}")
async def delete_localization_session(session: AsyncSession, localization_session_id: UUID) -> None:
    row = await session.get(LocalizationSession, localization_session_id)

    if row:
        destroy_service(row.container_id)
        await session.delete(row)
        await session.commit()
    else:
        raise NotFoundException(f"Localization session with id {localization_session_id} not found")


@put("/{localization_session_id:uuid}/camera")
async def set_localization_session_camera_intrinsics(
    session: AsyncSession, localization_session_id: UUID, data: PinholeCameraConfig
) -> None:
    url = await _session_base_url(session, localization_session_id)
    async with ApiClient(Configuration(host=url)) as api_client:
        try:
            await DefaultApi(api_client).set_camera_intrinsics(
                LocalizerPinholeCameraConfig.model_validate(data.model_dump())
            )
        except Exception as e:
            raise HTTPException(502, f"session backend unreachable: {e}") from e


@get("/{localization_session_id:uuid}/status")
async def get_localization_session_status(session: AsyncSession, localization_session_id: UUID) -> str:
    return get_service_status(f"localizer-{localization_session_id}", SESSION_PORT)


@post("/{localization_session_id:uuid}/maps")
async def load_localization_maps(
    session: AsyncSession,
    localization_session_id: UUID,
    map_ids: Annotated[list[UUID], Parameter(description="IDs of localization maps to load")],
) -> None:
    if map_ids == []:
        raise HTTPException(status_code=400, detail="No map_ids provided")

    reconstruction_ids: set[UUID] = set()
    for map_id in map_ids:
        map_row = await session.get(LocalizationMap, map_id)
        if not map_row:
            raise HTTPException(status_code=404, detail="Localization map not found")
        reconstruction_ids.add(map_row.reconstruction_id)

    url = await _session_base_url(session, localization_session_id)
    async with ApiClient(Configuration(host=url)) as api_client:
        for reconstruction_id in reconstruction_ids:
            try:
                await DefaultApi(api_client).load_reconstruction(id=reconstruction_id)
            except Exception as e:
                raise HTTPException(502, f"session backend unreachable: {e}") from e


@delete("/{localization_session_id:uuid}/maps/{map_id:uuid}")
async def unload_map(session: AsyncSession, localization_session_id: UUID, map_id: UUID) -> None:
    map_row = await session.get(LocalizationMap, map_id)
    if not map_row:
        raise HTTPException(status_code=404, detail="Localization map not found")

    url = await _session_base_url(session, localization_session_id)
    async with ApiClient(Configuration(host=url)) as api_client:
        try:
            await DefaultApi(api_client).unload_reconstruction(id=map_row.reconstruction_id)
        except Exception as e:
            raise HTTPException(502, f"session backend unreachable: {e}") from e


@get("/{localization_session_id:uuid}/maps/{map_id:uuid}/status")
async def get_map_load_status(session: AsyncSession, localization_session_id: UUID, map_id: UUID) -> LoadStateResponse:
    map_row = await session.get(LocalizationMap, map_id)
    if not map_row:
        raise HTTPException(status_code=404, detail="Localization map not found")

    url = await _session_base_url(session, localization_session_id)
    async with ApiClient(Configuration(host=url)) as api_client:
        try:
            return await DefaultApi(api_client).get_reconstruction_load_status(id=map_row.reconstruction_id)
        except Exception as e:
            raise HTTPException(502, f"session backend unreachable: {e}") from e


class MapLocalization(BaseModel):
    id: UUID
    camera_from_map_transform: Transform
    map_transform: Transform
    metrics: LocalizationMetrics


@post("/{localization_session_id:uuid}/localization")
async def localize_image(
    session: AsyncSession,
    localization_session_id: UUID,
    axis_convention: AxisConvention,
    data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
) -> list[MapLocalization]:
    url = await _session_base_url(session, localization_session_id)
    async with ApiClient(Configuration(host=url)) as api_client:
        try:
            localizations = await DefaultApi(api_client).localize_image(
                LocalizerAxisConvention(axis_convention.value), await data.read()
            )
            reconstruction_id_to_map = {
                map.reconstruction_id: map
                for map in await fetch_localization_maps(
                    reconstruction_ids=[response.id for response in localizations], ids=None, session=session
                )
            }

            return [
                MapLocalization(
                    id=reconstruction_id_to_map[localization.id].id,
                    camera_from_map_transform=Transform.model_validate(localization.transform.model_dump()),
                    map_transform=Transform(
                        translation=Float3(
                            x=reconstruction_id_to_map[localization.id].position_x,
                            y=reconstruction_id_to_map[localization.id].position_y,
                            z=reconstruction_id_to_map[localization.id].position_z,
                        ),
                        rotation=Float4(
                            x=reconstruction_id_to_map[localization.id].rotation_x,
                            y=reconstruction_id_to_map[localization.id].rotation_y,
                            z=reconstruction_id_to_map[localization.id].rotation_z,
                            w=reconstruction_id_to_map[localization.id].rotation_w,
                        ),
                    ),
                    metrics=LocalizationMetrics.model_validate(localization.metrics.model_dump()),
                )
                for localization in localizations
            ]

        except Exception as e:
            raise HTTPException(502, f"session backend unreachable: {e}") from e


async def _session_base_url(db: AsyncSession, session_id: UUID) -> str:
    row = (
        await db.execute(select(LocalizationSession.container_url).where(LocalizationSession.id == session_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Localization session not found")
    return row.rstrip("/")  # e.g., "http://localizer-<uuid>:8080"


router = Router(
    "/localization_sessions",
    tags=["Localization Sessions"],
    dependencies={"session": Provide(get_session)},
    route_handlers=[
        create_localization_session,
        delete_localization_session,
        set_localization_session_camera_intrinsics,
        get_localization_session_status,
        load_localization_maps,
        unload_map,
        get_map_load_status,
        localize_image,
    ],
)
