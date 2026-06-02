import csv
import io
import tarfile
from typing import IO, Annotated, BinaryIO, cast
from uuid import UUID

from botocore.exceptions import ReadTimeoutError
from common.multipart_requests import MultipartRequestModel, MultipartRequestOperation
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
from datamodels.public_tables import CaptureSession, DeviceType, LocalizationMap, Reconstruction

from .reconstructions import (
    ReconstructionReadWithQueue,
    select_reconstructions_with_queue,
    to_reconstruction_with_queue,
)
from litestar import Router, delete, get, patch, post
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException, InternalServerException, NotFoundException
from litestar.params import Body, Parameter
from litestar.response import Stream
from litestar.status_codes import HTTP_409_CONFLICT, HTTP_422_UNPROCESSABLE_ENTITY, HTTP_504_GATEWAY_TIMEOUT
from pydantic import AwareDatetime, BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..storage import get_storage

BUCKET = "dev-captures"
MIN_TEMPORAL_COVERAGE = 0.5


def _validate_temporal_coverage(tf: tarfile.TarFile, capture_interval_seconds: float) -> None:
    try:
        frames_member = tf.getmember("rig0/frames.csv")
        frames_file = tf.extractfile(frames_member)
    except KeyError:
        return
    if frames_file is None:
        return

    reader = csv.reader(io.TextIOWrapper(frames_file, encoding="utf-8"))
    next(reader, None)
    timestamps = [float(row[0]) for row in reader if row]
    if len(timestamps) < 2:
        return

    duration_s = (max(timestamps) - min(timestamps)) / 1000
    expected_frames = duration_s / capture_interval_seconds
    if expected_frames <= 0:
        return

    coverage = len(timestamps) / expected_frames
    if coverage >= MIN_TEMPORAL_COVERAGE:
        return

    raise HTTPException(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        detail=(
            f"Insufficient temporal coverage: {len(timestamps)} frames captured"
            f" but {expected_frames:.0f} expected over {duration_s:.1f}s"
            f" (coverage={coverage:.1%}). Minimum is {MIN_TEMPORAL_COVERAGE:.0%}."
        ),
    )


class CaptureSessionUploadRequest(MultipartRequestModel):
    device_type: DeviceType
    data: UploadFile
    id: UUID | None = None
    name: str | None = None
    recorded_at: AwareDatetime | None = None


@post("", operation_class=MultipartRequestOperation)
async def create_capture_session(
    session: AsyncSession,
    data: Annotated[CaptureSessionUploadRequest, Body(media_type=RequestEncodingType.MULTI_PART)],
) -> CaptureSessionRead:
    fileobj = data.data.file
    _validate_capture_session_tar(fileobj)

    row = await _create_capture(
        session,
        CaptureSessionCreate(
            id=data.id,
            recorded_at=data.recorded_at,
            size_bytes=None,
            device_type=data.device_type,
            name=data.name,
        ),
        overwrite=False,
    )
    session.add(row)
    await session.flush()
    await session.refresh(row)

    try:
        get_storage().upload_fileobj(
            BUCKET, f"{row.id}.tar", cast(BinaryIO, fileobj), data.data.content_type or "application/x-tar"
        )
    except ReadTimeoutError as e:
        raise HTTPException(status_code=HTTP_504_GATEWAY_TIMEOUT, detail="Upload failed: storage timeout") from e
    except Exception as e:
        raise InternalServerException(detail="Upload failed") from e

    row.size_bytes = get_storage().head_object_size(BUCKET, f"{row.id}.tar")
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


class ExpandedReconstruction(BaseModel):
    reconstruction: ReconstructionReadWithQueue
    localization_map_id: UUID | None = None


class ExpandedCaptureSession(BaseModel):
    capture_session: CaptureSessionRead
    reconstructions: list[ExpandedReconstruction]


class CaptureSessionsExpanded(BaseModel):
    capture_sessions: list[ExpandedCaptureSession]


@get("/expanded")
async def get_capture_sessions_expanded(session: AsyncSession) -> CaptureSessionsExpanded:
    captures = list((await session.execute(select(CaptureSession))).scalars().all())
    capture_ids = [c.id for c in captures]

    reconstruction_rows: list[tuple[Reconstruction, int | None, int | None]] = []
    if capture_ids:
        reconstruction_rows = [
            (row[0], row[1], row[2])
            for row in (
                await session.execute(
                    select_reconstructions_with_queue().where(Reconstruction.capture_session_id.in_(capture_ids))
                )
            ).all()
        ]

    map_by_reconstruction: dict[UUID, UUID] = {}
    reconstruction_ids = [r.id for r, _, _ in reconstruction_rows]
    if reconstruction_ids:
        map_result = await session.execute(
            select(LocalizationMap).where(LocalizationMap.reconstruction_id.in_(reconstruction_ids))
        )
        map_by_reconstruction = {row.reconstruction_id: row.id for row in map_result.scalars().all()}

    reconstructions_by_capture: dict[UUID, list[ExpandedReconstruction]] = {}
    for r, position, depth in reconstruction_rows:
        reconstructions_by_capture.setdefault(r.capture_session_id, []).append(
            ExpandedReconstruction(
                reconstruction=to_reconstruction_with_queue(r, position, depth),
                localization_map_id=map_by_reconstruction.get(r.id),
            )
        )

    return CaptureSessionsExpanded(
        capture_sessions=[
            ExpandedCaptureSession(
                capture_session=capture_session_to_dto(c),
                reconstructions=reconstructions_by_capture.get(c.id, []),
            )
            for c in captures
        ],
    )


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


def _validate_capture_session_tar(fileobj: IO[bytes]) -> None:
    try:
        fileobj.seek(0)
        with tarfile.open(fileobj=fileobj, mode="r:*") as tf:
            try:
                member = tf.getmember("manifest.json")
            except KeyError:
                raise HTTPException(
                    status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Capture session tar file is missing manifest.json",
                )

            if not member.isfile():
                raise HTTPException(
                    status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="manifest.json is not a regular file"
                )

            manifest_file = tf.extractfile(member)
            if manifest_file is None:
                raise HTTPException(
                    status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail="Could not read manifest.json from tar"
                )

            try:
                manifest = CaptureSessionManifest.model_validate_json(manifest_file.read().decode("utf-8"))
            except Exception as e:
                raise HTTPException(
                    status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Capture session manifest.json is invalid: {e}"
                ) from e

            if manifest.capture_interval_seconds is not None:
                _validate_temporal_coverage(tf, manifest.capture_interval_seconds)

        fileobj.seek(0)
    except tarfile.ReadError as e:
        raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid tar file: {e}") from e


@get(
    "/{id:uuid}/tar",
    media_type="application/x-tar",
    content_encoding="binary",
    content_media_type="application/x-tar",
)
async def download_capture_session_tar(session: AsyncSession, id: UUID) -> Stream:
    # Validate capture session exists
    if await session.get(CaptureSession, id) is None:
        raise NotFoundException(f"Capture session {id} not found")

    try:
        obj = get_storage().get_object(BUCKET, f"{id}.tar")
        body = obj["Body"]
    except ReadTimeoutError as e:
        raise HTTPException(status_code=HTTP_504_GATEWAY_TIMEOUT, detail="Download failed: storage timeout") from e
    except Exception as e:
        # Missing object or any other storage failure indicates inconsistent internal state
        raise InternalServerException("Download failed") from e

    return Stream(
        body.iter_chunks(chunk_size=1024 * 1024),
        media_type="application/x-tar",
        headers={"Content-Disposition": f'attachment; filename="{id}.tar"'},
    )


@get(
    "/{id:uuid}/manifest.json",
    media_type="application/json",
    content_encoding="binary",
    content_media_type="application/json",
)
async def get_capture_session_manifest_file(session: AsyncSession, id: UUID) -> Stream:
    if await session.get(CaptureSession, id) is None:
        raise NotFoundException(f"Capture session {id} not found")

    contents = _extract_member_bytes(id, "manifest.json")
    return Stream(iter([contents]), media_type="application/json")


@get(
    "/{id:uuid}/frames.csv",
    media_type="text/csv",
    content_encoding="binary",
    content_media_type="text/csv",
)
async def get_capture_session_frames_csv(session: AsyncSession, id: UUID) -> Stream:
    if await session.get(CaptureSession, id) is None:
        raise NotFoundException(f"Capture session {id} not found")

    contents = _extract_member_bytes(id, "rig0/frames.csv")
    return Stream(iter([contents]), media_type="text/csv")


@get(
    "/{id:uuid}/images/{frame_timestamp:int}",
    media_type="image/jpeg",
    content_encoding="binary",
    content_media_type="image/jpeg",
)
async def get_capture_session_image(session: AsyncSession, id: UUID, frame_timestamp: int) -> Stream:
    if await session.get(CaptureSession, id) is None:
        raise NotFoundException(f"Capture session {id} not found")

    contents = _extract_member_bytes(id, f"rig0/camera0/{frame_timestamp}.jpg")
    return Stream(iter([contents]), media_type="image/jpeg")


def _extract_member_bytes(capture_id: UUID, member_name: str) -> bytes:
    # Stream-mode tar (`r|*`) avoids loading the full capture tar into memory; fit-calibration
    # calls /images/{ts} ~100x per capture and tars run 500MB–2GB. We still read sequentially
    # to find the member, so worst case is one full pass per call. A future optimization could
    # store frames.csv + images as separate MinIO objects to make these endpoints O(1).
    try:
        obj = get_storage().get_object(BUCKET, f"{capture_id}.tar")
        body = obj["Body"]
    except ReadTimeoutError as e:
        raise HTTPException(status_code=HTTP_504_GATEWAY_TIMEOUT, detail="Download failed: storage timeout") from e
    except Exception as e:
        raise InternalServerException("Download failed") from e

    try:
        with tarfile.open(fileobj=cast(BinaryIO, body), mode="r|*") as tf:
            for member in tf:
                if member.name != member_name:
                    continue
                if not member.isfile():
                    raise HTTPException(
                        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"{member_name} in capture {capture_id} is not a regular file",
                    )
                extracted = tf.extractfile(member)
                if extracted is None:
                    raise HTTPException(
                        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                        detail=f"Could not read {member_name} from capture {capture_id} tar",
                    )
                return extracted.read()
    except tarfile.ReadError as e:
        raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid tar file: {e}") from e

    raise NotFoundException(f"{member_name} not found in capture {capture_id} tar")


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
                raise HTTPException(
                    status_code=HTTP_409_CONFLICT, detail=f"Capture with id {capture.id} already exists"
                )

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
        get_capture_sessions_expanded,
        get_capture_session,
        get_capture_session_reconstructions,
        delete_capture_session,
        update_capture_session,
        update_capture_sessions,
        download_capture_session_tar,
        get_capture_session_manifest_file,
        get_capture_session_frames_csv,
        get_capture_session_image,
        get_capture_session_rig_config,
    ],
)
