from __future__ import annotations

from pathlib import Path
from typing import Any, ValuesView, cast

from numpy import concatenate, empty, eye, float32, float64, intp, savez_compressed, stack, uint8, uint32
from numpy.typing import NDArray
from pycolmap import Database, PosePrior, PosePriorCoordinateSystem
from pycolmap import Image as pycolmapImage
from pycolmap._core import Frame, Point3D, Rigid3d, Sim3d, apply_rig_config, incremental_mapping, match_spatial
from scipy.spatial.transform import Rotation

from .metrics_builder import MetricsBuilder
from .options_builder import OptionsBuilder
from .rig import Rig, Transform

COLMAP_DB_FILE = "database.db"
COLMAP_SFM_DIRECTORY = "sfm_model"


def run_colmap_reconstruction(
    root_path: Path,
    output_path: Path,
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
    best_reconstruction = reconstructions[
        max(range(len(reconstructions)), key=lambda i: reconstructions[i].num_reg_images())
    ]

    # Use the first frame that is registered in the best reconstruction to determine the similarity transform
    anchor_frame_prior_pose: Transform | None = None
    anchor_rig_from_world_transform: Rigid3d | None = None
    for rig_id, camera_id, frame_id in (
        (rig_id, camera_id, frame_id)
        for rig_id in rigs.keys()
        for frame_id in rigs[rig_id].frame_poses.keys()
        for camera_id in rigs[rig_id].cameras.keys()
    ):
        image_id = colmap_image_ids[f"{rig_id}/{camera_id}/{frame_id}.jpg"]
        if image_id in best_reconstruction.images:
            reconstruction_frame = cast(Frame, best_reconstruction.images[image_id].frame)
            anchor_frame_prior_pose = rigs[rig_id].frame_poses[frame_id]
            anchor_rig_from_world_transform = cast(Rigid3d, reconstruction_frame.rig_from_world)  # type: ignore
            break

    if anchor_frame_prior_pose is None or anchor_rig_from_world_transform is None:
        raise RuntimeError("Could not find anchor frame in best reconstruction")

    # Transform the reconstruction to align with the rig coordinate system
    best_reconstruction.transform(
        Sim3d(
            concatenate(
                [
                    anchor_frame_prior_pose.rotation @ anchor_rig_from_world_transform.rotation.matrix(),
                    anchor_frame_prior_pose.rotation @ anchor_rig_from_world_transform.translation.reshape(3, 1)
                    + anchor_frame_prior_pose.translation.reshape(3, 1),
                ],
                axis=1,
            )
        )
    )

    # Write the best reconstruction to disk in COLMAP format
    best_reconstruction.write_text(str(output_path))

    # Write point cloud to disk in NPZ format
    point_cloud_point_count = len(best_reconstruction.points3D)
    point_cloud_positions = empty((point_cloud_point_count, 3), dtype=float32)
    point_cloud_colors = empty((point_cloud_point_count, 3), dtype=uint8)

    for point_cloud_point_index, point_cloud_point in enumerate(
        cast(ValuesView[Point3D], best_reconstruction.points3D.values())  # type: ignore
    ):
        point_cloud_positions[point_cloud_point_index] = point_cloud_point.xyz
        point_cloud_colors[point_cloud_point_index] = point_cloud_point.color

    point_cloud_npz_file_path = output_path / "points3D.npz"
    savez_compressed(str(point_cloud_npz_file_path), positions=point_cloud_positions, colors=point_cloud_colors)

    # Write frame poses to disk in NPZ format
    frame_count = len(best_reconstruction.frames)
    frame_positions = empty((frame_count, 3), dtype=float32)
    frame_orientations = empty((frame_count, 4), dtype=float32)

    for frame_index, frame in enumerate(cast(ValuesView[Frame], best_reconstruction.frames.values())):  # type: ignore
        # Convert from rig_from_world to world_from_rig
        rig_from_world = cast(Rigid3d, frame.rig_from_world)
        world_from_rig_rotation_matrix = rig_from_world.rotation.matrix().T
        world_from_rig_translation = -world_from_rig_rotation_matrix @ rig_from_world.translation

        frame_positions[frame_index] = world_from_rig_translation
        frame_orientations[frame_index] = Rotation.from_matrix(world_from_rig_rotation_matrix).as_quat()

    frame_poses_npz_file_path = output_path / "frame_poses.npz"
    savez_compressed(str(frame_poses_npz_file_path), positions=frame_positions, orientations=frame_orientations)

    return best_reconstruction
