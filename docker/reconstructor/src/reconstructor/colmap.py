from __future__ import annotations

from pathlib import Path
from shutil import rmtree
from typing import Any, Iterator, ValuesView, cast

from numpy import (
    asarray,
    concatenate,
    diag,
    empty,
    eye,
    float32,
    float64,
    intp,
    savez_compressed,
    sign,
    stack,
    uint8,
    uint32,
)
from numpy.linalg import det, norm, svd
from numpy.typing import NDArray  # noqa: TID251 — Phase T piece 3 follow-up migration
from pycolmap import Database, PosePrior, PosePriorCoordinateSystem, Reconstruction
from pycolmap import Image as pycolmapImage
from pycolmap._core import Frame, Point3D, Rigid3d, Sim3d, apply_rig_config, incremental_mapping, match_spatial  # noqa: PLC2701 — no public API
from scipy.spatial.transform import Rotation

from .metrics_builder import MetricsBuilder
from .options_builder import OptionsBuilder
from .rig import Rig, Transform

COLMAP_DB_FILE = "database.db"
COLMAP_SFM_DIRECTORY = "sfm_model"


def _registered_frames(
    rigs: dict[str, Rig],
    colmap_image_ids: dict[str, int],
    reconstruction: Reconstruction,
) -> Iterator[tuple[Transform, Rigid3d]]:
    # Multi-camera rigs (e.g. ZED stereo) share one Frame per rig+frame, so any registered
    # image of any camera in that frame yields the Frame's rig_from_world.
    for rig_id, rig in rigs.items():
        for frame_id, transform in rig.frame_poses.items():
            for camera_id in rig.cameras.keys():
                image_id = colmap_image_ids[f"{rig_id}/{camera_id}/{frame_id}.jpg"]
                if image_id in reconstruction.images:
                    rig_from_world = cast(Rigid3d, cast(Frame, reconstruction.images[image_id].frame).rig_from_world)  # type: ignore
                    yield transform, rig_from_world
                    break


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
    if colmap_db_path.exists():
        colmap_db_path.unlink()

    colmap_sfm_directory = root_path / COLMAP_SFM_DIRECTORY
    if colmap_sfm_directory.exists():
        rmtree(colmap_sfm_directory)

    colmap_sfm_directory.mkdir(parents=True)

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

    metrics.build_reconstruction_metrics(best_reconstruction)

    # Use the first frame that is registered in the best reconstruction to determine the similarity transform
    anchor = next(_registered_frames(rigs, colmap_image_ids, best_reconstruction), None)
    if anchor is None:
        raise RuntimeError("Could not find anchor frame in best reconstruction")
    anchor_frame_prior_pose, anchor_rig_from_world_transform = anchor

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

    # Rigid Umeyama best-fit of map centers to truth — fit not applied; only the residual is
    # kept as the VIO-quality signal that filters unreliable captures from the calibration corpus.
    truth_centers_list: list[NDArray[float64]] = []
    map_centers_list: list[NDArray[float64]] = []
    for transform, rig_from_world in _registered_frames(rigs, colmap_image_ids, best_reconstruction):
        truth_centers_list.append(transform.translation.astype(float64))
        map_centers_list.append(-rig_from_world.rotation.matrix().T @ rig_from_world.translation)

    if len(truth_centers_list) < 3:
        raise RuntimeError(f"Need ≥3 registered frames for alignment diagnostic (got {len(truth_centers_list)})")

    truth_centers = asarray(truth_centers_list, dtype=float64)
    map_centers = asarray(map_centers_list, dtype=float64)
    truth_mean, map_mean = truth_centers.mean(axis=0), map_centers.mean(axis=0)
    u, _, vt = svd((map_centers - map_mean).T @ (truth_centers - truth_mean))
    fit_rotation = vt.T @ diag([1.0, 1.0, sign(det(vt.T @ u.T))]) @ u.T
    fit_translation = truth_mean - fit_rotation @ map_mean
    residuals = norm((fit_rotation @ map_centers.T).T + fit_translation - truth_centers, axis=1)
    metrics.metrics.truth_alignment_rms_residual_m = float((residuals**2).mean() ** 0.5)
    metrics.metrics.truth_alignment_max_residual_m = float(residuals.max())

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
