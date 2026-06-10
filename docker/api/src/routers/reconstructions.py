from __future__ import annotations

import tarfile
from collections.abc import Iterable, Iterator
from io import BytesIO
from logging import getLogger
from struct import pack
from time import perf_counter
from typing import TYPE_CHECKING, Annotated, Any, BinaryIO, Optional, cast
from uuid import UUID

if TYPE_CHECKING:
    from mypy_boto3_s3.type_defs import ObjectIdentifierTypeDef

from common.boto_clients import create_s3_client
from common.multipart_requests import MultipartRequestModel, MultipartRequestOperation
from common.tar import iter_tar_file_members
from core.axis_convention import (
    AxisConvention,
    change_basis_unity_from_opencv_points,
    change_basis_unity_from_opencv_poses,
)
from core.reconstruction_manifest import MANIFEST_VERSION, Manifest
from core.reconstruction_metrics import ReconstructionMetrics
from core.reconstruction_options import ReconstructionOptions
from datamodels.public_dtos import (
    ReconstructionCreate,
    ReconstructionRead,
    reconstruction_from_dto,
    reconstruction_to_dto,
)
from datamodels.public_tables import (
    CaptureSession,
    LocalizationMap,
    Reconstruction,
    ReconstructionStatus,
)
from litestar import Request, Router, delete, get, post, put
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import ClientException, HTTPException, NotFoundException, PermissionDeniedException
from litestar.params import Body, KwargDefinition, Parameter
from litestar.response import Stream
from litestar.status_codes import HTTP_409_CONFLICT, HTTP_422_UNPROCESSABLE_ENTITY
from numpy import ascontiguousarray, float32, load, uint8
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..settings import get_settings
from ..storage import get_storage
from itertools import starmap

settings = get_settings()
BUCKET = "dev-reconstructions"
logger = getLogger(__name__)

TAR_VERSION = 1
METADATA_MEMBER = "metadata.json"
DATABASE_ARTIFACT = "database.db"
TAR_BLOCK = 512
ARTIFACT_CHUNK = 1024 * 1024


s3_client = create_s3_client(
    minio_endpoint_url=settings.minio_endpoint_url,
    minio_access_key=settings.minio_access_key,
    minio_secret_key=settings.minio_secret_key,
)


class ReconstructionCreateWithOptions(BaseModel):
    create: ReconstructionCreate
    options: Optional[ReconstructionOptions] = Field(
        default=None, description="Optional reconstruction options to use during reconstruction."
    )


# Extends the generated row DTO with computed queue fields. The base type is auto-generated
# from the database schema, so the queue numbers can't live there; they're computed per-read
# from the queue ordering. Both fields are None when status != QUEUED.
class ReconstructionReadWithQueue(ReconstructionRead):
    queue_position: int | None = None
    queue_depth: int | None = None


# Carries only the reconstruction row; its relocalization inputs live in the MinIO prefix, and the
# capture session, localization map, camera positions and evaluations are per-backend state recreated
# after import rather than transported.
class ReconstructionTarManifest(BaseModel):
    tar_version: int = TAR_VERSION
    reconstruction: ReconstructionRead


class ReconstructionTarUploadRequest(MultipartRequestModel):
    data: UploadFile


# Single SELECT that returns each Reconstruction row alongside its queue position and depth
# (NULL when the row isn't queued). Built as a CTE + LEFT JOIN so the queue computation
# happens in the same round trip as the row fetch and against the same transaction snapshot.
# Callers add their own .where() clauses; result rows are (Reconstruction, position, depth).
QueuedReconstructionRow = tuple[Reconstruction, Optional[int], Optional[int]]


def select_reconstructions_with_queue() -> Select[QueuedReconstructionRow]:
    queued = (
        select(
            Reconstruction.id.label("id"),
            func.row_number().over(order_by=Reconstruction.created_at).label("position"),
            func.count().over().label("depth"),
        )
        .where(Reconstruction.status == ReconstructionStatus.QUEUED)
        .cte("queued")
    )
    stmt = select(Reconstruction, queued.c.position, queued.c.depth).outerjoin(queued, queued.c.id == Reconstruction.id)
    return cast("Select[QueuedReconstructionRow]", stmt)


def to_reconstruction_with_queue(
    row: Reconstruction, queue_position: int | None, queue_depth: int | None
) -> ReconstructionReadWithQueue:
    base = reconstruction_to_dto(row)
    return ReconstructionReadWithQueue(**base.model_dump(), queue_position=queue_position, queue_depth=queue_depth)


@post("")
async def create_reconstruction(
    session: AsyncSession, data: ReconstructionCreateWithOptions, request: Request[str, dict[str, Any], Any]
) -> ReconstructionReadWithQueue:
    raw_body = await request.body()
    logger.info(
        "create_reconstruction raw_body=%s parsed_options=%s",
        raw_body.decode("utf-8", errors="replace"),
        data.options.model_dump() if data.options else None,
    )
    # If we were provided an ID, ensure it doesn't already exist
    if data.create.id is not None:
        result = await session.execute(select(Reconstruction).where(Reconstruction.id == data.create.id))
        existing_row = result.scalar_one_or_none()

        if existing_row is not None:
            raise HTTPException(
                status_code=HTTP_409_CONFLICT, detail=f"Reconstruction with id {data.create.id} already exists"
            )

    capture_session = await session.get(CaptureSession, data.create.capture_session_id)
    if not capture_session:
        raise NotFoundException(f"Capture session with id {data.create.capture_session_id} not found")

    manifest = Manifest(options=data.options or ReconstructionOptions(), metrics=ReconstructionMetrics())

    row = reconstruction_from_dto(data.create)
    row.status = ReconstructionStatus.QUEUED
    row.manifest = manifest.model_dump(mode="json")
    row.manifest_version = MANIFEST_VERSION

    session.add(row)

    await session.flush()

    result = await session.execute(select_reconstructions_with_queue().where(Reconstruction.id == row.id))
    return to_reconstruction_with_queue(*result.one())


@delete("/{id:uuid}")
async def delete_reconstruction(session: AsyncSession, id: UUID) -> None:
    row = await session.get(Reconstruction, id)

    if not row:
        raise NotFoundException(f"Reconstruction with id {id} not found")

    result = await session.execute(select(LocalizationMap).where(LocalizationMap.reconstruction_id == id))
    localization_map = result.scalar_one_or_none()

    if localization_map:
        raise NotFoundException(f"Reconstruction with id {id} has an associated localization map and cannot be deleted")

    # Delete S3 objects before the row so a synchronous failure leaves a recoverable state.
    # The row id is the only handle to find these objects in MinIO.
    prefix = f"{id}/"
    paginator = s3_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=settings.reconstructions_bucket, Prefix=prefix):
        objects: list[ObjectIdentifierTypeDef] = [
            {"Key": key} for obj in page.get("Contents", []) if (key := obj.get("Key")) is not None
        ]
        if objects:
            response = s3_client.delete_objects(Bucket=settings.reconstructions_bucket, Delete={"Objects": objects})
            errors = response.get("Errors", [])
            if errors:
                raise RuntimeError(f"S3 delete failed for {len(errors)} objects under {prefix}")

    await session.delete(row)

    await session.flush()
    return None


@get("")
async def get_reconstructions(
    session: AsyncSession,
    ids: Annotated[list[UUID] | None, Parameter(description="Optional list of Ids to filter by")] = None,
    capture_session_ids: Annotated[
        list[UUID] | None, Parameter(description="Optional list of capture session Ids to filter by")
    ] = None,
    capture_session_name: Annotated[
        Optional[str], Parameter(description="Optional capture session name to filter by")
    ] = None,
) -> list[ReconstructionReadWithQueue]:
    if capture_session_name and capture_session_ids:
        raise ClientException("Cannot provide both capture_session_ids and capture_session_name")

    query = select_reconstructions_with_queue()

    if ids:
        query = query.where(Reconstruction.id.in_(ids))

    if capture_session_ids:
        query = query.where(Reconstruction.capture_session_id.in_(capture_session_ids))

    if capture_session_name:
        result = await session.execute(select(CaptureSession.id).where(CaptureSession.name == capture_session_name))
        capture_session_row = result.scalar_one_or_none()
        if not capture_session_row:
            raise NotFoundException(f"Capture session with name {capture_session_name} not found")
        query = query.where(Reconstruction.capture_session_id == capture_session_row)

    result = await session.execute(query)

    return list(starmap(to_reconstruction_with_queue, result.all()))


@get("/{id:uuid}")
async def get_reconstruction(session: AsyncSession, id: UUID) -> ReconstructionReadWithQueue:
    result = (await session.execute(select_reconstructions_with_queue().where(Reconstruction.id == id))).first()

    if not result:
        raise NotFoundException(f"Reconstruction with id {id} not found")

    return to_reconstruction_with_queue(*result)


async def fetch_reconstruction_status(session: AsyncSession, id: UUID) -> ReconstructionStatus:
    row = await session.get(Reconstruction, id)

    if not row:
        raise NotFoundException(f"Reconstruction with id {id} not found")
    return row.status


@get("/{id:uuid}/localization_map")
async def get_reconstruction_localization_map(session: AsyncSession, id: UUID) -> UUID:
    row = await session.get(Reconstruction, id)

    if not row:
        raise NotFoundException(f"Reconstruction with id {id} not found")

    result = await session.execute(select(LocalizationMap.id).where(LocalizationMap.reconstruction_id == id))

    localization_map = result.scalar_one_or_none()

    if localization_map is None:
        raise NotFoundException(f"Localization map for reconstruction with id {id} not found")

    return localization_map


@put("/{id:uuid}/retry")
async def retry_reconstruction(session: AsyncSession, id: UUID) -> ReconstructionReadWithQueue:
    row = await session.get(Reconstruction, id)

    if not row:
        raise NotFoundException(f"Reconstruction with id {id} not found")

    if row.status not in (ReconstructionStatus.FAILED, ReconstructionStatus.CANCELLED):
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail=f"Reconstruction with id {id} is in state {row.status.value} and cannot be retried",
        )

    row.status = ReconstructionStatus.QUEUED
    row.error = None
    row.progress_current = None
    row.progress_total = None
    row.progress_attempt = None

    await session.flush()

    result = await session.execute(select_reconstructions_with_queue().where(Reconstruction.id == row.id))
    return to_reconstruction_with_queue(*result.one())


@get("/{id:uuid}/points", media_type="application/octet-stream")
async def get_reconstruction_points(
    session: AsyncSession,
    id: UUID,
    axis_convention: Annotated[AxisConvention, Parameter(description="List of Ids to delete")],
) -> Annotated[bytes, KwargDefinition(format="binary")]:
    row = await session.get(Reconstruction, id)
    if not row:
        raise NotFoundException(f"Reconstruction with id {id} not found")

    fetch_start = perf_counter()
    npz_bytes = s3_client.get_object(Bucket=settings.reconstructions_bucket, Key=f"{row.id}/sfm_model/points3D.npz")[
        "Body"
    ].read()
    fetch_ms = (perf_counter() - fetch_start) * 1000

    serialize_start = perf_counter()
    with load(BytesIO(npz_bytes)) as npz:
        point_cloud_positions = npz["positions"]
        point_cloud_colors = npz["colors"]

    if axis_convention == AxisConvention.UNITY:
        point_cloud_positions = change_basis_unity_from_opencv_points(point_cloud_positions)

    point_count = int(point_cloud_positions.shape[0])
    payload = (
        pack("<I", point_count)
        + ascontiguousarray(point_cloud_positions, dtype=float32).astype("<f4", copy=False).tobytes()
        + ascontiguousarray(point_cloud_colors, dtype=uint8).tobytes()
    )
    serialize_ms = (perf_counter() - serialize_start) * 1000

    logger.info(
        "GET reconstruction points id=%s axis=%s points=%d bytes=%d fetch_ms=%.1f serialize_ms=%.1f",
        id,
        axis_convention.value,
        point_count,
        len(payload),
        fetch_ms,
        serialize_ms,
    )

    return payload


@get("/{id:uuid}/frame_poses", media_type="application/octet-stream")
async def get_reconstruction_frame_poses(
    session: AsyncSession,
    id: UUID,
    axis_convention: Annotated[AxisConvention, Parameter(description="Axis convention for returned poses")],
) -> Annotated[bytes, KwargDefinition(format="binary")]:
    row = await session.get(Reconstruction, id)
    if not row:
        raise NotFoundException(f"Reconstruction with id {id} not found")

    fetch_start = perf_counter()
    npz_bytes = s3_client.get_object(Bucket=settings.reconstructions_bucket, Key=f"{row.id}/sfm_model/frame_poses.npz")[
        "Body"
    ].read()
    fetch_ms = (perf_counter() - fetch_start) * 1000

    serialize_start = perf_counter()
    with load(BytesIO(npz_bytes)) as npz:
        frame_positions = npz["positions"]
        frame_orientations = npz["orientations"]

    if axis_convention == AxisConvention.UNITY:
        frame_positions, frame_orientations = change_basis_unity_from_opencv_poses(frame_positions, frame_orientations)

    frame_count = int(frame_positions.shape[0])
    payload = (
        pack("<I", frame_count)
        + ascontiguousarray(frame_positions, dtype=float32).astype("<f4", copy=False).tobytes()
        + ascontiguousarray(frame_orientations, dtype=float32).astype("<f4", copy=False).tobytes()
    )
    serialize_ms = (perf_counter() - serialize_start) * 1000

    logger.info(
        "GET reconstruction frame_poses id=%s axis=%s frames=%d bytes=%d fetch_ms=%.1f serialize_ms=%.1f",
        id,
        axis_convention.value,
        frame_count,
        len(payload),
        fetch_ms,
        serialize_ms,
    )

    return payload


# dummy method, just to get ReconstructionMetrics into the OpenAPI schema
@get("/{id:uuid}/metrics")
async def get_reconstruction_metrics(session: AsyncSession, id: UUID) -> ReconstructionMetrics:
    return ReconstructionMetrics()


@get(
    "/{id:uuid}/tar",
    media_type="application/x-tar",
    content_encoding="binary",
    content_media_type="application/x-tar",
)
async def export_reconstruction_tar(
    session: AsyncSession,
    id: UUID,
) -> Stream:
    reconstruction = await session.get(Reconstruction, id)
    if reconstruction is None:
        raise NotFoundException(f"Reconstruction with id {id} not found")

    if reconstruction.status != ReconstructionStatus.SUCCEEDED:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT,
            detail=f"Reconstruction with id {id} is in state {reconstruction.status.value};"
            " only succeeded reconstructions can be exported",
        )

    manifest = ReconstructionTarManifest(reconstruction=reconstruction_to_dto(reconstruction))
    metadata_bytes = manifest.model_dump_json().encode("utf-8")

    return Stream(
        iter_reconstruction_tar(id, metadata_bytes),
        media_type="application/x-tar",
        headers={"Content-Disposition": f'attachment; filename="reconstruction-{id}.tar"'},
    )


@post("/tar", operation_class=MultipartRequestOperation)
async def import_reconstruction_tar(
    session: AsyncSession,
    request: Request[str, dict[str, Any], Any],
    data: Annotated[ReconstructionTarUploadRequest, Body(media_type=RequestEncodingType.MULTI_PART)],
) -> ReconstructionReadWithQueue:
    # Worker tokens route to the orchestration session with no tenant, so current_tenant() raises on insert.
    if request.auth and request.auth.get("azp") == "placeframe-worker":
        raise PermissionDeniedException("Reconstruction import requires a user identity, not a worker token")

    fileobj = cast(BinaryIO, data.data.file)
    fileobj.seek(0)
    metadata_bytes = next(
        (member.read() for name, member in iter_tar_file_members(fileobj) if name == METADATA_MEMBER), None
    )
    if metadata_bytes is None:
        raise HTTPException(status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=f"{METADATA_MEMBER} not found in tar")

    try:
        manifest = ReconstructionTarManifest.model_validate_json(metadata_bytes)
    except ValidationError as error:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Malformed tar metadata: {error}"
        ) from error

    if manifest.tar_version != TAR_VERSION:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported tar_version {manifest.tar_version}; expected {TAR_VERSION}",
        )

    reconstruction = manifest.reconstruction
    reconstruction_id = reconstruction.id

    existing = await session.get(Reconstruction, reconstruction_id)
    if existing is not None:
        raise HTTPException(
            status_code=HTTP_409_CONFLICT, detail=f"Reconstruction with id {reconstruction_id} already exists"
        )

    # Upload before insert: a row pointing at missing artifacts looks healthy but breaks the localizer,
    # while orphaned artifacts under a known id are recoverable.
    storage = get_storage()
    prefix = f"{reconstruction_id}/"
    fileobj.seek(0)
    for name, member in iter_tar_file_members(fileobj):
        if name == METADATA_MEMBER:
            continue

        storage.upload_fileobj(
            settings.reconstructions_bucket, f"{prefix}{name}", cast(BinaryIO, member), "application/octet-stream"
        )

    # capture_session_id stays NULL: an imported reconstruction has no source capture on this backend.
    inserted = False
    try:
        reconstruction_row = reconstruction_from_dto(ReconstructionCreate(id=reconstruction_id))
        reconstruction_row.status = ReconstructionStatus.SUCCEEDED
        reconstruction_row.manifest = reconstruction.manifest
        reconstruction_row.manifest_version = reconstruction.manifest_version
        session.add(reconstruction_row)
        await session.flush()
        inserted = True
    finally:
        if not inserted:
            storage.delete_prefix(settings.reconstructions_bucket, prefix)

    result = await session.execute(select_reconstructions_with_queue().where(Reconstruction.id == reconstruction_id))
    return to_reconstruction_with_queue(*result.one())


# Frames each member by hand (not tarfile.addfile, which buffers a whole member) so a large artifact
# never lands in memory. Runs after the request transaction closes: storage only, no DB session.
def iter_reconstruction_tar(reconstruction_id: UUID, metadata_bytes: bytes) -> Iterator[bytes]:
    storage = get_storage()
    prefix = f"{reconstruction_id}/"

    yield from _tar_member(METADATA_MEMBER, len(metadata_bytes), [metadata_bytes])

    for key, size in storage.list_objects(settings.reconstructions_bucket, prefix):
        relative = key[len(prefix) :]
        if not relative or relative == DATABASE_ARTIFACT:
            continue

        body = storage.get_object(settings.reconstructions_bucket, key)["Body"]
        yield from _tar_member(relative, size, body.iter_chunks(ARTIFACT_CHUNK))

    yield b"\x00" * (TAR_BLOCK * 2)


def _tar_member(name: str, size: int, chunks: Iterable[bytes]) -> Iterator[bytes]:
    info = tarfile.TarInfo(name)
    info.size = size
    info.mtime = 0

    yield info.tobuf(format=tarfile.GNU_FORMAT)
    yield from chunks

    remainder = size % TAR_BLOCK
    if remainder:
        yield b"\x00" * (TAR_BLOCK - remainder)


router = Router(
    "/reconstructions",
    tags=["Reconstructions"],
    dependencies={"session": Provide(get_session)},
    route_handlers=[
        create_reconstruction,
        delete_reconstruction,
        get_reconstructions,
        get_reconstruction,
        get_reconstruction_localization_map,
        retry_reconstruction,
        get_reconstruction_points,
        get_reconstruction_frame_poses,
        get_reconstruction_metrics,
        export_reconstruction_tar,
        import_reconstruction_tar,
    ],
)
