from typing import Annotated, cast
from uuid import UUID, uuid4

from common.docker_compose_client import create_service, destroy_service, get_service_status
from common.multipart_requests import MultipartRequestModel, MultipartRequestOperation
from core.axis_convention import AxisConvention
from core.camera_config import PinholeCameraConfig
from core.localization_metrics import LocalizationMetrics
from core.transform import Float3, Float4, Transform
from datamodels.public_dtos import LocalizationSessionRead, localization_session_to_dto
from datamodels.public_tables import LocalizationSession
from fastapi.exceptions import HTTPException
from litestar import Router, delete, get, post
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.status_codes import HTTP_404_NOT_FOUND, HTTP_502_BAD_GATEWAY
from plerion_localizer_client import ApiClient, ApiException, Configuration
from plerion_localizer_client.api.default_api import DefaultApi
from plerion_localizer_client.models.axis_convention import AxisConvention as LocalizerAxisConvention
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
        raise HTTPException(HTTP_404_NOT_FOUND, f"Localization session with id {localization_session_id} not found")


@get("/{localization_session_id:uuid}/status")
async def get_localization_session_status(session: AsyncSession, localization_session_id: UUID) -> str:
    return get_service_status(f"localizer-{localization_session_id}", SESSION_PORT)


class LocalizationRequest(MultipartRequestModel):
    map_ids: list[UUID]
    camera_config: PinholeCameraConfig
    axis_convention: AxisConvention
    image: UploadFile


class MapLocalization(BaseModel):
    id: UUID
    camera_from_map_transform: Transform
    map_transform: Transform
    metrics: LocalizationMetrics


@post("/{localization_session_id:uuid}/localization", operation_class=MultipartRequestOperation)
async def localize_image(
    session: AsyncSession,
    localization_session_id: UUID,
    data: Annotated[LocalizationRequest, Body(media_type=RequestEncodingType.MULTI_PART)],
) -> list[MapLocalization]:
    map_ids = data.map_ids
    camera_config = data.camera_config
    axis_convention = data.axis_convention
    image = data.image

    reconstruction_id_to_map_id = {
        map.reconstruction_id: map
        for map in await fetch_localization_maps(reconstruction_ids=None, ids=map_ids, session=session)
    }

    url = await _session_base_url(session, localization_session_id)
    async with ApiClient(Configuration(host=url)) as api_client:
        try:
            localizations = await DefaultApi(api_client).localize_image(
                list(reconstruction_id_to_map_id.keys()),
                LocalizerPinholeCameraConfig.model_validate(camera_config.model_dump()),
                LocalizerAxisConvention(axis_convention.value),
                await image.read(),
            )

            return [
                MapLocalization(
                    id=reconstruction_id_to_map_id[localization.id].id,
                    camera_from_map_transform=Transform.model_validate(localization.transform.model_dump()),
                    map_transform=Transform(
                        translation=Float3(
                            x=reconstruction_id_to_map_id[localization.id].position_x,
                            y=reconstruction_id_to_map_id[localization.id].position_y,
                            z=reconstruction_id_to_map_id[localization.id].position_z,
                        ),
                        rotation=Float4(
                            x=reconstruction_id_to_map_id[localization.id].rotation_x,
                            y=reconstruction_id_to_map_id[localization.id].rotation_y,
                            z=reconstruction_id_to_map_id[localization.id].rotation_z,
                            w=reconstruction_id_to_map_id[localization.id].rotation_w,
                        ),
                    ),
                    metrics=LocalizationMetrics.model_validate(localization.metrics.model_dump()),
                )
                for localization in localizations
            ]

        except ApiException as e:
            status = cast(int | None, e.status)
            if status is not None and 400 <= status < 500:
                raise HTTPException(status, cast(str | None, e.reason) or "Localization session client error") from e
            raise HTTPException(HTTP_502_BAD_GATEWAY, "Localization session backend error") from e


async def _session_base_url(db: AsyncSession, session_id: UUID) -> str:
    row = (
        await db.execute(select(LocalizationSession.container_url).where(LocalizationSession.id == session_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(HTTP_404_NOT_FOUND, "Localization session not found")
    return row.rstrip("/")  # e.g., "http://localizer-<uuid>:8080"


router = Router(
    "/localization_sessions",
    tags=["Localization Sessions"],
    dependencies={"session": Provide(get_session)},
    route_handlers=[
        create_localization_session,
        delete_localization_session,
        get_localization_session_status,
        localize_image,
    ],
)
