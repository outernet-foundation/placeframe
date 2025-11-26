from __future__ import annotations

from pathlib import Path
from typing import Any

from numpy import eye, float64, intp, stack, uint32
from numpy.typing import NDArray
from pycolmap import Database, PosePrior, PosePriorCoordinateSystem
from pycolmap import Image as pycolmapImage
from pycolmap._core import apply_rig_config, incremental_mapping, match_spatial

from .metrics_builder import MetricsBuilder
from .options_builder import OptionsBuilder
from .rig import Rig

COLMAP_DB_FILE = "database.db"
COLMAP_SFM_DIRECTORY = "sfm_model"


def run_reconstruction(
    root_path: Path,
    images_path: Path,
    options: OptionsBuilder,
    metrics: MetricsBuilder,
    rigs: dict[str, Rig],
    keypoints: dict[str, Any],
    pairs: list[tuple[str, str]],
    match_indices: dict[tuple[str, str], tuple[NDArray[intp], NDArray[intp]]],
):
    colmap_db_path = root_path / COLMAP_DB_FILE
    colmap_sfm_directory = root_path / COLMAP_SFM_DIRECTORY
    colmap_sfm_directory.mkdir(parents=True, exist_ok=True)

    position_covariance = (options.pose_prior_position_sigma_m() ** 2) * eye(3, dtype=float64)

    # Create COLMAP database
    database = Database.open(str(colmap_db_path))
    # Write cameras, images, keypoints, and pose priors to database
    colmap_image_ids: dict[str, int] = {}
    for rig_id, rig in rigs.items():
        for camera_id, camera in rig.cameras.items():
            colmap_camera_id = database.write_camera(camera[1])

            for frame_id, transform in rig.frame_poses.items():
                image_name = f"{rig_id}/{camera_id}/{frame_id}.jpg"

                colmap_image_ids[image_name] = database.write_image(
                    pycolmapImage(name=image_name, camera_id=colmap_camera_id)
                )
                database.write_keypoints(colmap_image_ids[image_name], keypoints[image_name])

                # Only write pose prior for images from reference sensors (all others are implied by rig)
                if camera[0].ref_sensor:
                    database.write_pose_prior(
                        colmap_image_ids[image_name],
                        PosePrior(
                            position=transform.translation.reshape(3, 1),
                            position_covariance=position_covariance,
                            coordinate_system=PosePriorCoordinateSystem.CARTESIAN,
                        ),
                    )

    # Apply rig configuration to database (must be done after writing cameras and images)
    apply_rig_config([rig.colmap_rig_config for rig in rigs.values()], database)

    # Write matches to database
    for a, b in pairs:
        (image_a_indices, image_b_indices) = match_indices[(a, b)]
        database.write_matches(
            colmap_image_ids[a],
            colmap_image_ids[b],
            stack((image_a_indices, image_b_indices), axis=1).astype(uint32, copy=False),
        )

    # Close database
    database.close()

    # Perform rig-aware geometric verification of matches
    print("Verifying geometry for matches")
    match_spatial(
        database_path=str(colmap_db_path),
        matching_options=options.feature_matching_options(),
        verification_options=options.two_view_geometry_options(),
    )

    # Compute and store verified matches metrics
    metrics.build_verified_matches_metrics(colmap_db_path, pairs)

    # Run incremental mapping
    print("Running incremental mapping")
    reconstructions = incremental_mapping(
        database_path=str(colmap_db_path),
        image_path=str(images_path),
        output_path=str(colmap_sfm_directory),
        options=options.incremental_pipeline_options(),
    )

    # Check that at least one reconstruction was created
    if len(reconstructions) == 0:
        return None

    # Choose the reconstruction with the most registered images
    # TODO: Write information to metrics about this for visibility
    return reconstructions[max(range(len(reconstructions)), key=lambda i: reconstructions[i].num_reg_images())]
