import tarfile
from io import BytesIO
from typing import Annotated
from uuid import UUID

from core.axis_convention import AxisConvention
from core.capture_session_manifest import CaptureSessionManifest
from datamodels.public_dtos import (
    CaptureSessionBatchUpdate,
    CaptureSessionCreate,
    CaptureSessionRead,
    CaptureSessionUpdate,
    capture_session_apply_batch_update_dto,
    capture_session_apply_dto,
    capture_session_from_dto,
    capture_session_from_dto_overwrite,
    capture_session_to_dto,
)
from datamodels.public_tables import CaptureSession, Reconstruction
from litestar import Router, delete, get, patch, post, put
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException, NotFoundException
from litestar.params import Body, Parameter
from litestar.response import Stream
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..storage import get_storage

BUCKET = "dev-captures"


@post("")
async def create_capture_session(session: AsyncSession, data: CaptureSessionCreate) -> CaptureSessionRead:
    row = await _create_capture(session, data, False)

    session.add(row)

    await session.flush()
    await session.refresh(row)
    return capture_session_to_dto(row)


@post("/bulk")
async def create_capture_sessions(
    session: AsyncSession, data: list[CaptureSessionCreate], overwrite: bool = False
) -> list[CaptureSessionRead]:
    rows: list[CaptureSession] = []
    for capture in data:
        row = await _create_capture(session, capture, overwrite)
        rows.append(row)

    session.add_all(rows)

    await session.flush()
    for row in rows:
        await session.refresh(row)
    return [capture_session_to_dto(r) for r in rows]


@get("")
async def get_capture_sessions(
    session: AsyncSession,
    ids: Annotated[list[UUID] | None, Parameter(description="Optional list of Ids to filter by")] = None,
) -> list[CaptureSessionRead]:
    query = select(CaptureSession)

    if ids:
        query = query.where(CaptureSession.id.in_(ids))

    result = await session.execute(query)

    results = [capture_session_to_dto(row) for row in result.scalars().all()]
    return results


@get("/{id:uuid}")
async def get_capture_session(session: AsyncSession, id: UUID) -> CaptureSessionRead:
    row = await session.get(CaptureSession, id)

    if not row:
        raise NotFoundException(f"Capture session with id {id} not found")

    return capture_session_to_dto(row)


@get("/{id:uuid}/reconstructions")
async def get_capture_session_reconstructions(session: AsyncSession, id: UUID) -> list[UUID]:
    row = await session.get(CaptureSession, id)

    if not row:
        raise NotFoundException(f"Capture session with id {id} not found")

    result = await session.execute(select(Reconstruction.id).where(Reconstruction.capture_session_id == id))

    return [r[0] for r in result.all()]


@delete("/{id:uuid}")
async def delete_capture_session(session: AsyncSession, id: UUID) -> None:
    row = await session.get(CaptureSession, id)

    if not row:
        raise NotFoundException(f"Capture session with id {id} not found")

    await session.delete(row)

    await session.flush()
    return None


@patch("/{id:uuid}")
async def update_capture_session(session: AsyncSession, id: UUID, data: CaptureSessionUpdate) -> CaptureSessionRead:
    row = await session.get(CaptureSession, id)

    if not row:
        raise NotFoundException(f"Capture session with id {id} not found")

    capture_session_apply_dto(row, data)

    await session.flush()
    await session.refresh(row)
    return capture_session_to_dto(row)


@patch("")
async def update_capture_sessions(
    session: AsyncSession, data: list[CaptureSessionBatchUpdate], allow_missing: bool = False
) -> list[CaptureSessionRead]:
    rows: list[CaptureSession] = []
    for capture in data:
        row = await session.get(CaptureSession, capture.id)

        if not row:
            if not allow_missing:
                raise NotFoundException(f"Capture session with id {capture.id} not found")
            continue

        capture_session_apply_batch_update_dto(row, capture)
        rows.append(row)

    await session.flush()
    for row in rows:
        await session.refresh(row)
    return [capture_session_to_dto(r) for r in rows]


@put("/{id:uuid}/tar")
async def upload_capture_session_tar(
    session: AsyncSession, id: UUID, data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)]
) -> None:
    # Validate capture session exists
    row = await session.get(CaptureSession, id)
    if row is None:
        raise NotFoundException(f"Capture session {id} not found")

    #  Validate manifest inside tar
    file_bytes = await data.read()
    with tarfile.open(fileobj=BytesIO(file_bytes), mode="r:*") as tar_file:
        capture_session_manifest = tar_file.extractfile("manifest.json")
        if capture_session_manifest is None:
            raise NotFoundException("Capture session tar file is missing manifest.json")
        try:
            _ = CaptureSessionManifest.model_validate_json(capture_session_manifest.read().decode("utf-8"))
        except Exception as exception:
            raise NotFoundException(f"Capture session manifest.json is invalid: {exception}") from exception

    # Upload tar file to storage
    try:
        get_storage().upload_fileobj(BUCKET, f"{id}.tar", BytesIO(file_bytes), data.content_type or "application/x-tar")
    except Exception as exception:
        raise HTTPException(502, f"Upload failed: {exception}") from exception

    return None


@get("/{id:uuid}/tar")
async def download_capture_session_tar(session: AsyncSession, id: UUID) -> Stream:
    row = await session.get(CaptureSession, id)

    if row is None:
        raise NotFoundException(f"Capture session {id} not found")

    try:
        body = get_storage().get_object(BUCKET, f"{id}.tar")["Body"]
    except Exception as exception:
        raise HTTPException(502, f"Download failed: {exception}") from exception

    return Stream(
        body.iter_chunks(chunk_size=1024 * 1024),
        media_type="application/x-tar",
        headers={"Content-Disposition": f'attachment; filename="{id}.tar"'},
    )


# dummy method, just to get RigConfig into the OpenAPI schema
@get("/{id:uuid}/rig_config")
async def get_capture_session_rig_config(session: AsyncSession, id: UUID) -> CaptureSessionManifest:
    rig_config = CaptureSessionManifest(axis_convention=AxisConvention.OPENCV, rigs=[])

    return rig_config


async def _create_capture(session: AsyncSession, capture: CaptureSessionCreate, overwrite: bool) -> CaptureSession:
    if capture.id is not None:
        result = await session.execute(select(CaptureSession).where(CaptureSession.id == capture.id))
        existing_row = result.scalar_one_or_none()

        if existing_row is not None:
            if not overwrite:
                raise HTTPException(409, f"Capture with id {capture.id} already exists")

            capture_session_from_dto_overwrite(existing_row, capture)
            return existing_row

    return capture_session_from_dto(capture)


router = Router(
    "/capture_sessions",
    tags=["Capture Sessions"],
    dependencies={"session": Provide(get_session)},
    route_handlers=[
        create_capture_session,
        create_capture_sessions,
        get_capture_sessions,
        get_capture_session,
        get_capture_session_reconstructions,
        delete_capture_session,
        update_capture_session,
        update_capture_sessions,
        upload_capture_session_tar,
        download_capture_session_tar,
        get_capture_session_rig_config,
    ],
)
