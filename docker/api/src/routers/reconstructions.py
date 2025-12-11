from __future__ import annotations

from io import BytesIO
from struct import pack
from typing import Optional
from uuid import UUID

from common.boto_clients import create_s3_client
from common.schemas import binary_schema
from core.axis_convention import (
    AxisConvention,
    change_basis_unity_from_opencv_points,
    change_basis_unity_from_opencv_poses,
)
from core.reconstruction_manifest import ReconstructionManifest, ReconstructionStatus
from core.reconstruction_metrics import ReconstructionMetrics
from core.reconstruction_options import ReconstructionOptions
from datamodels.public_dtos import (
    ReconstructionCreate,
    ReconstructionRead,
    reconstruction_from_dto,
    reconstruction_to_dto,
)
from datamodels.public_tables import CaptureSession, LocalizationMap, Reconstruction
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from numpy import ascontiguousarray, float32, load, uint8
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..settings import get_settings

settings = get_settings()
BUCKET = "dev-reconstructions"

router = APIRouter(prefix="/reconstructions", tags=["reconstructions"])


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


@router.post("")
async def create_reconstruction(
    reconstruction: ReconstructionCreateWithOptions, session: AsyncSession = Depends(get_session)
) -> ReconstructionRead:
    # If we were provided an ID, ensure it doesn't already exist
    if reconstruction.create.id is not None:
        result = await session.execute(select(Reconstruction).where(Reconstruction.id == reconstruction.create.id))
        existing_row = result.scalar_one_or_none()

        if existing_row is not None:
            raise HTTPException(409, f"Reconstruction with id {reconstruction.create.id} already exists")

    capture_session = await session.get(CaptureSession, reconstruction.create.capture_session_id)
    if not capture_session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Capture session with id {reconstruction.create.capture_session_id} not found",
        )

    row = reconstruction_from_dto(reconstruction.create)

    session.add(row)

    await session.flush()
    await session.refresh(row)

    manifest = ReconstructionManifest(
        capture_id=str(row.capture_session_id),
        status="pending",
        options=reconstruction.options or ReconstructionOptions(),
        metrics=ReconstructionMetrics(),
    )

    s3_client.put_object(
        Bucket=settings.reconstructions_bucket,
        Key=f"{row.id}/manifest.json",
        Body=manifest.model_dump_json().encode("utf-8"),
        ContentType="application/json",
    )

    return reconstruction_to_dto(row)


@router.delete("/{id}")
async def delete_reconstruction(id: UUID, session: AsyncSession = Depends(get_session)) -> None:
    row = await session.get(Reconstruction, id)

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reconstruction with id {id} not found")

    result = await session.execute(select(LocalizationMap).where(LocalizationMap.reconstruction_id == id))
    localization_map = result.scalar_one_or_none()

    if localization_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Reconstruction with id {id} has an associated localization map and cannot be deleted",
        )

    await session.delete(row)

    await session.flush()
    return None


@router.get("")
async def get_reconstructions(
    ids: Optional[list[UUID]] = Query(None, description="Optional list of Ids to filter by"),
    capture_session_id: Optional[UUID] = Query(None, description="Optional capture session Id to filter by"),
    capture_session_name: Optional[str] = Query(None, description="Optional capture session name to filter by"),
    session: AsyncSession = Depends(get_session),
) -> list[ReconstructionRead]:
    if capture_session_name and capture_session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot provide both capture_session_id and capture_session_name",
        )

    query = select(Reconstruction)

    if ids:
        query = query.where(Reconstruction.id.in_(ids))

    if capture_session_id:
        query = query.where(Reconstruction.capture_session_id == capture_session_id)

    if capture_session_name:
        result = await session.execute(select(CaptureSession.id).where(CaptureSession.name == capture_session_name))
        capture_session_row = result.scalar_one_or_none()
        if not capture_session_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Capture session with name {capture_session_name} not found",
            )
        query = query.where(Reconstruction.capture_session_id == capture_session_row)

    result = await session.execute(query)

    return [reconstruction_to_dto(row) for row in result.scalars().all()]


@router.get("/{id}")
async def get_reconstruction(id: UUID, session: AsyncSession = Depends(get_session)) -> ReconstructionRead:
    row = await session.get(Reconstruction, id)

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reconstruction with id {id} not found")

    return reconstruction_to_dto(row)


@router.get("/{id}/manifest")
async def get_reconstruction_manifest(id: UUID, session: AsyncSession = Depends(get_session)) -> ReconstructionManifest:
    row = await session.get(Reconstruction, id)

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reconstruction with id {id} not found")

    try:
        manifest = ReconstructionManifest.model_validate_json(
            s3_client.get_object(Bucket=settings.reconstructions_bucket, Key=f"{id}/manifest.json")["Body"].read()
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving manifest for reconstruction with id {id}: {e}",
        )

    return manifest


@router.get("/{id}/localization_map")
async def get_reconstruction_localization_map(id: UUID, session: AsyncSession = Depends(get_session)) -> UUID:
    row = await session.get(Reconstruction, id)

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reconstruction with id {id} not found")

    result = await session.execute(select(LocalizationMap.id).where(LocalizationMap.reconstruction_id == id))

    localization_map = result.scalar_one_or_none()

    if localization_map is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Localization map for reconstruction with id {id} not found"
        )

    return localization_map


@router.get("/{id}/status")
async def get_reconstruction_status(id: UUID, session: AsyncSession = Depends(get_session)) -> ReconstructionStatus:
    manifest = await get_reconstruction_manifest(id, session)

    return manifest.status


@router.get("/{id}/points", response_class=StreamingResponse, responses={200: {"content": binary_schema}})
async def get_reconstruction_points(
    id: UUID, axis_convention: AxisConvention = Query(...), session: AsyncSession = Depends(get_session)
) -> StreamingResponse:
    row = await session.get(Reconstruction, id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reconstruction with id {id} not found")

    # Load point cloud from S3
    npz_bytes = s3_client.get_object(Bucket=settings.reconstructions_bucket, Key=f"{row.id}/sfm_model/points3D.npz")[
        "Body"
    ].read()

    # Extract positions and colors
    with load(BytesIO(npz_bytes)) as npz:
        point_cloud_positions = npz["positions"]
        point_cloud_colors = npz["colors"]

    # Change basis if needed
    if axis_convention == AxisConvention.UNITY:
        point_cloud_positions = change_basis_unity_from_opencv_points(point_cloud_positions)

    # Serialize and return point cloud as binary stream
    return StreamingResponse(
        BytesIO(
            (
                pack("<I", int(point_cloud_positions.shape[0]))
                + ascontiguousarray(point_cloud_positions, dtype=float32).astype("<f4", copy=False).tobytes()
                + ascontiguousarray(point_cloud_colors, dtype=uint8).tobytes()
            )
        ),
        media_type="application/octet-stream",
    )


@router.get("/{id}/frame_poses", response_class=StreamingResponse, responses={200: {"content": binary_schema}})
async def get_reconstruction_frame_poses(
    id: UUID, axis_convention: AxisConvention = Query(...), session: AsyncSession = Depends(get_session)
) -> StreamingResponse:
    row = await session.get(Reconstruction, id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reconstruction with id {id} not found")

    # Load frame poses from S3
    npz_bytes = s3_client.get_object(Bucket=settings.reconstructions_bucket, Key=f"{row.id}/sfm_model/frame_poses.npz")[
        "Body"
    ].read()

    # Extract positions and orientations
    with load(BytesIO(npz_bytes)) as npz:
        frame_positions = npz["positions"]
        frame_orientations = npz["orientations"]

    # Change basis if needed
    if axis_convention == AxisConvention.UNITY:
        frame_positions, frame_orientations = change_basis_unity_from_opencv_poses(frame_positions, frame_orientations)

    # Serialize and return frame poses as binary stream
    return StreamingResponse(
        BytesIO(
            pack("<I", int(frame_positions.shape[0]))
            + ascontiguousarray(frame_positions, dtype=float32).astype("<f4", copy=False).tobytes()
            + ascontiguousarray(frame_orientations, dtype=float32).astype("<f4", copy=False).tobytes()
        ),
        media_type="application/octet-stream",
    )
