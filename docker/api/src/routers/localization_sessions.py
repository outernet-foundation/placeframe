from uuid import UUID, uuid4

from common.session_client_docker import DockerSessionClient
from core.classes import Quaternion, Transform, Vector3
from core.localization_metrics import LocalizationMetrics
from core.rig import CameraConfig
from datamodels.public_dtos import LocalizationSessionRead, localization_session_to_dto
from datamodels.public_tables import LocalizationMap, LocalizationSession
from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile, status
from plerion_localizer_client import ApiClient, Configuration
from plerion_localizer_client.api.default_api import DefaultApi
from plerion_localizer_client.models.camera import Camera as LocalizeCamera
from plerion_localizer_client.models.load_state_response import LoadStateResponse
from plerion_localizer_client.models.pinhole_camera_config import PinholeCameraConfig
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..settings import get_settings
from .localization_maps import get_localization_maps

router = APIRouter(prefix="/localization_sessions", tags=["localization_sessions"])

settings = get_settings()


@router.post("")
async def create_localization_session(session: AsyncSession = Depends(get_session)) -> LocalizationSessionRead:
    id = uuid4()
    row = LocalizationSession(id=id)
    container_id, container_url = DockerSessionClient().create_session(
        session_id=str(row.id),
        image=settings.localization_session_image,
        environment={
            "S3_ENDPOINT_URL": str(settings.s3_endpoint_url) or "",
            "S3_ACCESS_KEY": settings.s3_access_key or "",
            "S3_SECRET_KEY": settings.s3_secret_key or "",
            "RECONSTRUCTIONS_BUCKET": settings.reconstructions_bucket,
        },
        gpus=True,
    )

    row.container_id = container_id
    row.container_url = str(container_url)

    session.add(row)

    await session.flush()
    await session.refresh(row)

    return localization_session_to_dto(row)


@router.delete("/{localization_session_id}")
async def delete_localization_session(localization_session_id: UUID, session: AsyncSession = Depends(get_session)):
    row = await session.get(LocalizationSession, localization_session_id)

    if row:
        DockerSessionClient().stop_session(container_id=row.container_id)
        await session.delete(row)
        await session.commit()
        return {"detail": f"Localization session with id {localization_session_id} deleted"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Localization session with id {localization_session_id} not found",
        )


@router.put("/{localization_session_id}/camera")
async def set_localization_session_camera_intrinsics(
    localization_session_id: UUID, camera: CameraConfig = Body(...), session: AsyncSession = Depends(get_session)
):
    if camera.model != "PINHOLE":
        raise HTTPException(status_code=422, detail="Only PINHOLE camera model is supported")

    url = await _session_base_url(session, localization_session_id)
    async with ApiClient(Configuration(host=url)) as api_client:
        try:
            await DefaultApi(api_client).set_camera_intrinsics(
                LocalizeCamera(actual_instance=PinholeCameraConfig.model_validate(camera.model_dump()))
            )
        except Exception as e:
            raise HTTPException(502, f"session backend unreachable: {e}") from e


@router.get("/{localization_session_id}/status")
async def get_localization_session_status(
    localization_session_id: UUID, session: AsyncSession = Depends(get_session)
) -> str:
    return DockerSessionClient().get_session_status(f"vls-session-{localization_session_id}")


@router.post("/{localization_session_id}/maps")
async def load_localization_maps(
    localization_session_id: UUID,
    map_ids: list[UUID] = Body(..., description="IDs of localization maps to load"),
    session: AsyncSession = Depends(get_session),
):
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

    return {"ok": True}


@router.delete("/{localization_session_id}/maps/{map_id}")
async def unload_map(localization_session_id: UUID, map_id: UUID, session: AsyncSession = Depends(get_session)):
    map_row = await session.get(LocalizationMap, map_id)
    if not map_row:
        raise HTTPException(status_code=404, detail="Localization map not found")

    url = await _session_base_url(session, localization_session_id)
    async with ApiClient(Configuration(host=url)) as api_client:
        try:
            await DefaultApi(api_client).unload_reconstruction(id=map_row.reconstruction_id)
        except Exception as e:
            raise HTTPException(502, f"session backend unreachable: {e}") from e

    return {"ok": True}


@router.get("/{localization_session_id}/maps/{map_id}/status")
async def get_map_load_status(
    localization_session_id: UUID, map_id: UUID, session: AsyncSession = Depends(get_session)
) -> LoadStateResponse:
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
    transform: Transform
    map_transform: Transform
    metrics: LocalizationMetrics


@router.post("/{localization_session_id}/localization")
async def localize_image(
    localization_session_id: UUID, image: UploadFile = File(...), session: AsyncSession = Depends(get_session)
) -> list[MapLocalization]:
    url = await _session_base_url(session, localization_session_id)
    async with ApiClient(Configuration(host=url)) as api_client:
        try:
            localizations = await DefaultApi(api_client).localize_image(await image.read())
            reconstruction_id_to_map = {
                map.reconstruction_id: map
                for map in await get_localization_maps(
                    reconstruction_ids=[response.id for response in localizations], ids=None, session=session
                )
            }

            return [
                MapLocalization(
                    id=reconstruction_id_to_map[localization.id].id,
                    transform=Transform.model_validate(localization.transform.model_dump()),
                    map_transform=Transform(
                        position=Vector3(
                            x=reconstruction_id_to_map[localization.id].position_x,
                            y=reconstruction_id_to_map[localization.id].position_y,
                            z=reconstruction_id_to_map[localization.id].position_z,
                        ),
                        rotation=Quaternion(
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
    return row.rstrip("/")  # e.g., "http://vls-session-<uuid>:8080"
