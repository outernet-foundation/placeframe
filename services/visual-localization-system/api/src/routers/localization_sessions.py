from typing import cast
from uuid import UUID, uuid4

import httpx
from common.classes import CameraIntrinsics, LocalizationMetrics, Transform
from common.session_client_docker import DockerSessionClient
from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile, status
from models.public_dtos import LocalizationSessionRead, localization_session_to_dto
from models.public_tables import LocalizationMap, LocalizationSession
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.routers.localization_maps import get_localization_maps

from ..database import get_session
from ..settings import get_settings

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
    localization_session_id: UUID, camera: CameraIntrinsics = Body(...), session: AsyncSession = Depends(get_session)
):
    if camera["model"] != "PINHOLE":
        raise HTTPException(status_code=422, detail="Only PINHOLE camera model is supported")

    async with httpx.AsyncClient() as client:
        try:
            await client.put(
                f"{await _session_base_url(session, localization_session_id)}/camera", json=cast(object, camera)
            )
        except httpx.RequestError as e:
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

    base = await _session_base_url(session, localization_session_id)
    async with httpx.AsyncClient() as client:
        for reconstruction_id in reconstruction_ids:
            try:
                response = await client.post(f"{base}/reconstructions/{reconstruction_id}")
            except httpx.RequestError as e:
                raise HTTPException(502, f"session backend unreachable: {e}") from e
            if not response.is_success:
                try:
                    raise HTTPException(status_code=response.status_code, detail=response.json())
                except Exception:
                    raise HTTPException(status_code=response.status_code, detail=response.text)
    return {"ok": True}


@router.delete("/{localization_session_id}/maps/{map_id}")
async def unload_map(localization_session_id: UUID, map_id: UUID, session: AsyncSession = Depends(get_session)):
    map_row = await session.get(LocalizationMap, map_id)
    if not map_row:
        raise HTTPException(status_code=404, detail="Localization map not found")

    base = await _session_base_url(session, localization_session_id)
    async with httpx.AsyncClient() as client:
        try:
            r = await client.delete(f"{base}/reconstructions/{map_row.reconstruction_id}")
        except httpx.RequestError as e:
            raise HTTPException(502, f"session backend unreachable: {e}") from e
    if r.is_success:
        return {"ok": True}
    raise HTTPException(status_code=r.status_code, detail=r.text)


@router.get("/{localization_session_id}/maps/{map_id}/status")
async def get_map_load_status(
    localization_session_id: UUID, map_id: UUID, session: AsyncSession = Depends(get_session)
) -> str:
    map_row = await session.get(LocalizationMap, map_id)
    if not map_row:
        raise HTTPException(status_code=404, detail="Localization map not found")

    base = await _session_base_url(session, localization_session_id)
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{base}/reconstructions/{map_row.reconstruction_id}/status")
        except httpx.RequestError as e:
            raise HTTPException(502, f"session backend unreachable: {e}") from e
    if r.is_success:
        status_json = r.json()
        return status_json.get("status", "unknown")
    raise HTTPException(status_code=r.status_code, detail=r.text)


class MapLocalization(BaseModel):
    id: UUID
    transform: Transform
    map_transform: Transform
    metrics: LocalizationMetrics


@router.post("/{localization_session_id}/localization")
async def localize_image(
    localization_session_id: UUID, image: UploadFile = File(...), session: AsyncSession = Depends(get_session)
) -> list[MapLocalization]:
    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(
                f"{await _session_base_url(session, localization_session_id)}/localization",
                files={
                    "image": (
                        image.filename or "image.jpg",
                        await image.read(),
                        image.content_type or "application/octet-stream",
                    )
                },
            )
        except httpx.RequestError as e:
            raise HTTPException(502, f"session backend unreachable: {e}") from e

    if not r.is_success:
        raise HTTPException(status_code=r.status_code, detail=r.text)

    localizer_response: dict[UUID, tuple[Transform, LocalizationMetrics]] = r.json()
    maps = await get_localization_maps(
        reconstruction_ids=[id for id in localizer_response.keys()], ids=None, session=session
    )

    return [
        MapLocalization(
            id=id,
            transform=localizer_response[id][0],
            map_transform={
                "position": {"x": maps[i].position_x, "y": maps[i].position_y, "z": maps[i].position_z},
                "rotation": {
                    "w": maps[i].rotation_w,
                    "x": maps[i].rotation_x,
                    "y": maps[i].rotation_y,
                    "z": maps[i].rotation_z,
                },
            },
            metrics=localizer_response[id][1],
        )
        for i, id in enumerate(localizer_response)
    ]


async def _session_base_url(db: AsyncSession, session_id: UUID) -> str:
    row = (
        await db.execute(select(LocalizationSession.container_url).where(LocalizationSession.id == session_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Localization session not found")
    return row.rstrip("/")  # e.g., "http://vls-session-<uuid>:8080"
