from io import BytesIO

from common.boto_clients import create_s3_client
from datamodels.public_tables import LocalizationMap, LocalizationMapCameraPosition
from numpy import load
from scipy.spatial.transform import Rotation
from sqlalchemy import delete as sqlalchemy_delete
from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession

from .settings import get_settings

settings = get_settings()

s3_client = create_s3_client(
    minio_endpoint_url=settings.minio_endpoint_url,
    minio_access_key=settings.minio_access_key,
    minio_secret_key=settings.minio_secret_key,
)


async def sync_camera_positions(session: AsyncSession, row: LocalizationMap) -> None:
    frame_poses_bytes = s3_client.get_object(
        Bucket=settings.reconstructions_bucket, Key=f"{row.reconstruction_id}/sfm_model/frame_poses.npz"
    )["Body"].read()

    with load(BytesIO(frame_poses_bytes)) as npz:
        frame_positions = npz["positions"]

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
