from typing import List, Optional
from uuid import UUID

from common.boto_clients import create_s3_client
from common.classes import PointCloudPoint, Transform
from common.schemas import binary_schema
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from models.public_dtos import ReconstructionCreate, ReconstructionRead, reconstruction_from_dto, reconstruction_to_dto
from models.public_tables import CaptureSession, LocalizationMap, Reconstruction
from numpy import array
from scipy.spatial.transform import Rotation  # ensure this import exists
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..settings import get_settings

settings = get_settings()
BUCKET = "dev-reconstructions"

router = APIRouter(prefix="/reconstructions", tags=["reconstructions"])


@router.post("")
async def create_reconstruction(
    reconstruction: ReconstructionCreate, session: AsyncSession = Depends(get_session)
) -> ReconstructionRead:
    # If we were provided an ID, ensure it doesn't already exist
    if reconstruction.id is not None:
        result = await session.execute(select(Reconstruction).where(Reconstruction.id == reconstruction.id))
        existing_row = result.scalar_one_or_none()

        if existing_row is not None:
            raise HTTPException(409, f"Reconstruction with id {reconstruction.id} already exists")

    capture_session = await session.get(CaptureSession, reconstruction.capture_session_id)
    if not capture_session:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Capture session with id {reconstruction.capture_session_id} not found",
        )

    row = reconstruction_from_dto(reconstruction)

    session.add(row)

    await session.flush()
    await session.refresh(row)
    return reconstruction_to_dto(row)


@router.delete("/{id}")
async def delete_reconstruction(id: UUID, session: AsyncSession = Depends(get_session)) -> None:
    row = await session.get(Reconstruction, id)

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reconstruction with id {id} not found")

    await session.delete(row)

    await session.flush()
    return None


@router.get("")
async def get_reconstructions(
    ids: Optional[List[UUID]] = Query(None, description="Optional list of Ids to filter by"),
    session: AsyncSession = Depends(get_session),
) -> List[ReconstructionRead]:
    query = select(Reconstruction)

    if ids:
        query = query.where(Reconstruction.id.in_(ids))

    result = await session.execute(query)

    return [reconstruction_to_dto(row) for row in result.scalars().all()]


@router.get("/{id}")
async def get_reconstruction(id: UUID, session: AsyncSession = Depends(get_session)) -> ReconstructionRead:
    row = await session.get(Reconstruction, id)

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reconstruction with id {id} not found")

    return reconstruction_to_dto(row)


@router.get("/{id}/localization_map")
async def get_reconstruction_localization_map(id: UUID, session: AsyncSession = Depends(get_session)) -> UUID | None:
    row = await session.get(Reconstruction, id)

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reconstruction with id {id} not found")

    result = await session.execute(select(LocalizationMap.id).where(LocalizationMap.reconstruction_id == id))

    return result.scalar_one_or_none()


@router.get("/{id}/status")
async def get_reconstruction_status(id: UUID, session: AsyncSession = Depends(get_session)) -> str:
    row = await session.get(Reconstruction, id)

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reconstruction with id {id} not found")

    return row.status


@router.get("/{id}/points")
async def get_reconstruction_points(id: UUID, session: AsyncSession = Depends(get_session)) -> list[PointCloudPoint]:
    row = await session.get(Reconstruction, id)

    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reconstruction with id {id} not found")

    return [
        PointCloudPoint(
            position={"x": float(parts[1]), "y": float(parts[2]), "z": float(parts[3])},
            color=(float(parts[4]), float(parts[5]), float(parts[6])),
        )
        for parts in [
            line.split()
            for line in [
                line.decode("utf-8").strip()
                for line in create_s3_client(settings.s3_endpoint_url, settings.s3_access_key, settings.s3_secret_key)
                .get_object(Bucket=settings.reconstructions_bucket, Key=f"{row.id}/sfm_model/points3D.txt")["Body"]
                .iter_lines()
            ]
            if line and not line.startswith("#")
        ]
    ]


@router.get("/{id}/points.ply", response_class=StreamingResponse, responses={200: {"content": binary_schema}})
async def get_reconstruction_points3D_ply(id: UUID, session: AsyncSession = Depends(get_session)) -> StreamingResponse:
    row = await session.get(Reconstruction, id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reconstruction with id {id} not found")

    return StreamingResponse(
        create_s3_client(settings.s3_endpoint_url, settings.s3_access_key, settings.s3_secret_key).get_object(
            Bucket=settings.reconstructions_bucket, Key=f"{row.id}/sfm_model/points3D.ply"
        )["Body"],
        media_type="application/octet-stream",
    )


@router.get("/{id}/image_poses")
async def get_reconstruction_image_poses(id: UUID, session: AsyncSession = Depends(get_session)) -> list[Transform]:
    row = await session.get(Reconstruction, id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Reconstruction with id {id} not found")

    poses: list[Transform] = []
    for parts in [
        line.split(
            maxsplit=9  # COLMAP images.txt: ID QW QX QY QZ TX TY TZ CAM_ID NAME; NAME may have spaces, so keep it as one field
        )
        for index, line in enumerate([
            line
            for line in [
                line.decode("utf-8").strip()
                for line in create_s3_client(settings.s3_endpoint_url, settings.s3_access_key, settings.s3_secret_key)
                .get_object(Bucket=settings.reconstructions_bucket, Key=f"{row.id}/sfm_model/images.txt")["Body"]
                .iter_lines()
            ]
            if line and not line.startswith("#")
        ])
        if index % 2 == 0  # every other line is a header
    ]:
        qw, qx, qy, qz = map(float, parts[1:5])
        tx, ty, tz = map(float, parts[5:8])

        # Convert from COLMAP world-from-camera to camera-from-world
        camera_from_world = -Rotation.from_quat([qx, qy, qz, qw]).as_matrix().T @ array([tx, ty, tz], dtype=float)

        poses.append(
            Transform(
                position={
                    "x": float(camera_from_world[0]),
                    "y": float(camera_from_world[1]),
                    "z": float(camera_from_world[2]),
                },
                rotation={"w": qw, "x": -qx, "y": -qy, "z": -qz},
            )
        )

    return poses
