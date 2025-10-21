import json
from typing import Annotated, Callable, TypeVar, cast
from uuid import UUID, uuid4

import httpx
from common.classes import CameraIntrinsics, Transform
from common.session_client_docker import DockerSessionClient
from fastapi import APIRouter, Body, Depends, File, Form, HTTPException, UploadFile, status
from models.public_dtos import LocalizationSessionRead, localization_session_to_dto
from models.public_tables import LocalizationMap, LocalizationSession
from pydantic import TypeAdapter, ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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


@router.delete("/{id}")
async def delete_localization_session(id: UUID, session: AsyncSession = Depends(get_session)):
    row = await session.get(LocalizationSession, id)

    if row:
        DockerSessionClient().stop_session(container_id=row.container_id)
        await session.delete(row)
        await session.commit()
        return {"detail": f"Localization session with id {id} deleted"}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Localization session with id {id} not found"
        )


@router.get("/{id}/status")
async def get_localization_session_status(id: UUID, session: AsyncSession = Depends(get_session)) -> str:
    return DockerSessionClient().get_session_status(f"vls-session-{id}")


@router.post("/{id}/maps")
async def load_localization_maps(
    id: UUID,
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

    base = await _session_base_url(session, id)
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


@router.delete("/{id}/maps/{map_id}")
async def unload_map(id: UUID, map_id: UUID, session: AsyncSession = Depends(get_session)):
    map_row = await session.get(LocalizationMap, map_id)
    if not map_row:
        raise HTTPException(status_code=404, detail="Localization map not found")

    base = await _session_base_url(session, id)
    async with httpx.AsyncClient() as client:
        try:
            r = await client.delete(f"{base}/reconstructions/{map_row.reconstruction_id}")
        except httpx.RequestError as e:
            raise HTTPException(502, f"session backend unreachable: {e}") from e
    if r.is_success:
        return {"ok": True}
    raise HTTPException(status_code=r.status_code, detail=r.text)


@router.get("/{id}/maps/{map_id}/status")
async def get_map_load_status(id: UUID, map_id: UUID, session: AsyncSession = Depends(get_session)) -> str:
    map_row = await session.get(LocalizationMap, map_id)
    if not map_row:
        raise HTTPException(status_code=404, detail="Localization map not found")

    base = await _session_base_url(session, id)
    async with httpx.AsyncClient() as client:
        try:
            r = await client.get(f"{base}/reconstructions/{map_row.reconstruction_id}/status")
        except httpx.RequestError as e:
            raise HTTPException(502, f"session backend unreachable: {e}") from e
    if r.is_success:
        status_json = r.json()
        return status_json.get("status", "unknown")
    raise HTTPException(status_code=r.status_code, detail=r.text)


T = TypeVar("T")


def make_multipart_json_dep(name: str, adapter: TypeAdapter[T]) -> Callable[[str], T]:
    def dep(value: str = Form(..., alias=name)) -> T:
        try:
            return adapter.validate_json(value)
        except ValidationError as e:
            raise HTTPException(status_code=422, detail=e.errors())

    return dep


INTR_ADAPTER: TypeAdapter[CameraIntrinsics] = TypeAdapter(CameraIntrinsics)
parse_camera = make_multipart_json_dep("camera", INTR_ADAPTER)


@router.post(
    "/{id}/localization",
    openapi_extra={
        "requestBody": {
            "content": {"multipart/form-data": {"encoding": {"camera": {"contentType": "application/json"}}}}
        }
    },
)
async def localize_image(
    id: UUID,
    camera: Annotated[CameraIntrinsics, Depends(parse_camera)],
    image: UploadFile = File(..., description="Image to localize"),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Transform]:
    # only pinhole supported for now
    if camera["model"] != "PINHOLE":
        raise HTTPException(status_code=422, detail="Only PINHOLE camera model is supported")

    async with httpx.AsyncClient() as client:
        try:
            r = await client.post(
                f"{await _session_base_url(session, id)}/localization",
                files={
                    "image": (
                        image.filename or "image.jpg",
                        await image.read(),
                        image.content_type or "application/octet-stream",
                    ),
                    "camera": (None, json.dumps(cast(object, camera)), "application/json"),
                },
            )
        except httpx.RequestError as e:
            raise HTTPException(502, f"session backend unreachable: {e}") from e

    if not r.is_success:
        raise HTTPException(status_code=r.status_code, detail=r.text)

    return r.json()


async def _session_base_url(db: AsyncSession, session_id: UUID) -> str:
    row = (
        await db.execute(select(LocalizationSession.container_url).where(LocalizationSession.id == session_id))
    ).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Localization session not found")
    return row.rstrip("/")  # e.g., "http://vls-session-<uuid>:8080"
