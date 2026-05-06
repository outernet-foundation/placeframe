from io import BytesIO
from typing import Annotated
from uuid import UUID

from common.boto_clients import create_s3_client
from datamodels.public_dtos import (
    LocalizationMapBatchUpdate,
    LocalizationMapCreate,
    LocalizationMapRead,
    LocalizationMapUpdate,
    localization_map_apply_batch_update_dto,
    localization_map_apply_dto,
    localization_map_from_dto,
    localization_map_to_dto,
)
from datamodels.public_tables import LocalizationMap, LocalizationMapCameraPosition, ReconstructionStatus
from litestar import Router, delete, get, patch, post
from litestar.di import Provide
from litestar.exceptions import ClientException, HTTPException, NotFoundException
from litestar.params import Parameter
from litestar.status_codes import HTTP_409_CONFLICT
from numpy import load
from scipy.spatial.transform import Rotation
from sqlalchemy import delete as sqlalchemy_delete
from sqlalchemy import exists, func, insert, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_session
from ..settings import get_settings
from .reconstructions import fetch_reconstruction_status

settings = get_settings()

s3_client = create_s3_client(
    minio_endpoint_url=settings.minio_endpoint_url,
    minio_access_key=settings.minio_access_key,
    minio_secret_key=settings.minio_secret_key,
)

_TRANSFORM_FIELDS = {"position_x", "position_y", "position_z", "rotation_x", "rotation_y", "rotation_z", "rotation_w"}


async def _sync_camera_positions(session: AsyncSession, row: LocalizationMap) -> None:
    """Compute world-space camera positions from the reconstruction's frame poses and store them in the DB."""
    frame_poses_bytes = s3_client.get_object(
        Bucket=settings.reconstructions_bucket, Key=f"{row.reconstruction_id}/sfm_model/frame_poses.npz"
    )["Body"].read()

    with load(BytesIO(frame_poses_bytes)) as npz:
        frame_positions = npz["positions"]  # (N, 3)

    rotation_matrix = Rotation.from_quat([row.rotation_x, row.rotation_y, row.rotation_z, row.rotation_w]).as_matrix()
    translation = [row.position_x, row.position_y, row.position_z]
    world_positions = (rotation_matrix @ frame_positions.T).T + translation

    await session.execute(
        sqlalchemy_delete(LocalizationMapCameraPosition).where(
            LocalizationMapCameraPosition.localization_map_id == row.id
        )
    )

    if len(world_positions) > 0:
        await session.execute(
            insert(LocalizationMapCameraPosition),
            [
                {
                    "localization_map_id": row.id,
                    "tenant_id": row.tenant_id,
                    "position_x": float(p[0]),
                    "position_y": float(p[1]),
                    "position_z": float(p[2]),
                }
                for p in world_positions
            ],
        )


@post("")
async def create_localization_map(session: AsyncSession, data: LocalizationMapCreate) -> LocalizationMapRead:
    reconstruction_status = await fetch_reconstruction_status(session, data.reconstruction_id)

    if reconstruction_status != ReconstructionStatus.SUCCEEDED:
        raise HTTPException(
            HTTP_409_CONFLICT, f"Reconstruction with id {data.reconstruction_id} is not in 'succeeded' state"
        )

    row = localization_map_from_dto(data)

    session.add(row)

    await session.flush()
    await session.refresh(row)
    await _sync_camera_positions(session, row)
    return localization_map_to_dto(row)


@delete("/{id:uuid}")
async def delete_localization_map(session: AsyncSession, id: UUID) -> None:
    row = await session.get(LocalizationMap, id)

    if not row:
        raise NotFoundException(f"LocalizationMap with id {id} not found")

    await session.delete(row)

    await session.flush()
    return None


@delete("")
async def delete_localization_maps(
    session: AsyncSession, ids: Annotated[list[UUID], Parameter(description="List of Ids to delete")]
) -> None:
    for id in ids:
        row = await session.get(LocalizationMap, id)

        if not row:
            raise NotFoundException(f"LocalizationMap with id {id} not found")

        await session.delete(row)

    await session.flush()
    return None


async def fetch_localization_maps(
    session: AsyncSession,
    ids: list[UUID] | None = None,
    reconstruction_ids: list[UUID] | None = None,
    position_x: float | None = None,
    position_y: float | None = None,
    position_z: float | None = None,
    radius: float | None = None,
) -> list[LocalizationMapRead]:
    spatial_params = [position_x, position_y, position_z, radius]
    has_spatial = any(p is not None for p in spatial_params)
    if has_spatial and not all(p is not None for p in spatial_params):
        raise ClientException(
            "Cannot provide partial spatial parameters; position_x, position_y, position_z, and radius must all be provided together"
        )

    if has_spatial and (ids or reconstruction_ids):
        raise ClientException("Cannot combine spatial filter with ids or reconstruction_ids")

    if ids and reconstruction_ids:
        raise ClientException("Cannot filter by both ids and reconstruction_ids")

    query = select(LocalizationMap)

    if ids:
        query = query.where(LocalizationMap.id.in_(ids))

    if reconstruction_ids:
        query = query.where(LocalizationMap.reconstruction_id.in_(reconstruction_ids))

    if has_spatial:
        query = query.where(
            exists(
                select(1)
                .select_from(text("localization_map_camera_positions cp"))
                .where(text("cp.localization_map_id = localization_maps.id"))
                .where(
                    func.ST_3DDWithin(
                        func.ST_MakePoint(text("cp.position_x"), text("cp.position_y"), text("cp.position_z")),
                        func.ST_MakePoint(position_x, position_y, position_z),
                        radius,
                    )
                )
            )
        )

    result = await session.execute(query)
    rows = result.scalars().all()

    # if (ids and len(ids) != len(rows)) or (reconstruction_ids and len(reconstruction_ids) != len(rows)):
    #     raise NotFoundException("One or more LocalizationMaps not found")

    return [localization_map_to_dto(row) for row in rows]


@get("")
async def get_localization_maps(
    session: AsyncSession,
    ids: Annotated[list[UUID] | None, Parameter(description="Optional list of Ids to filter by")] = None,
    reconstruction_ids: Annotated[
        list[UUID] | None, Parameter(description="Optional list of Reconstruction Ids to filter by")
    ] = None,
    position_x: float | None = None,
    position_y: float | None = None,
    position_z: float | None = None,
    radius: float | None = None,
) -> list[LocalizationMapRead]:
    return await fetch_localization_maps(session, ids, reconstruction_ids, position_x, position_y, position_z, radius)


@get("/{id:uuid}")
async def get_localization_map(session: AsyncSession, id: UUID) -> LocalizationMapRead:
    row = await session.get(LocalizationMap, id)

    if not row:
        raise NotFoundException(f"LocalizationMap with id {id} not found")

    return localization_map_to_dto(row)


@patch("/{id:uuid}")
async def update_localization_map(session: AsyncSession, id: UUID, data: LocalizationMapUpdate) -> LocalizationMapRead:
    row = await session.get(LocalizationMap, id)

    if not row:
        raise NotFoundException(f"LocalizationMap with id {id} not found")

    updated_fields = data.model_dump(exclude_unset=True).keys()
    localization_map_apply_dto(row, data)

    await session.flush()
    await session.refresh(row)

    if any(f in _TRANSFORM_FIELDS for f in updated_fields):
        await _sync_camera_positions(session, row)

    return localization_map_to_dto(row)


@patch("")
async def update_localization_maps(
    session: AsyncSession, data: list[LocalizationMapBatchUpdate], allow_missing: bool = False
) -> list[LocalizationMapRead]:
    rows: list[tuple[LocalizationMap, LocalizationMapBatchUpdate]] = []
    for localization_map in data:
        row = await session.get(LocalizationMap, localization_map.id)
        if not row:
            if not allow_missing:
                raise NotFoundException(f"LocalizationMap with id {localization_map.id} not found")
            continue

        localization_map_apply_batch_update_dto(row, localization_map)
        rows.append((row, localization_map))

    await session.flush()
    for row, update in rows:
        await session.refresh(row)
        if any(f in _TRANSFORM_FIELDS for f in update.model_dump(exclude_unset=True).keys()):
            await _sync_camera_positions(session, row)

    return [localization_map_to_dto(r) for r, _ in rows]


router = Router(
    "/localization-maps",
    tags=["Localization Maps"],
    dependencies={"session": Provide(get_session)},
    route_handlers=[
        create_localization_map,
        delete_localization_map,
        delete_localization_maps,
        get_localization_maps,
        get_localization_map,
        update_localization_map,
        update_localization_maps,
    ],
)
