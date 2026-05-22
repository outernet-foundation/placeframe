from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from shutil import rmtree
from typing import Any, Iterator, ValuesView, cast

from placeframe_api_client import ReconstructionStatus

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
from pycolmap import Camera as ColmapCamera
from pycolmap import (
    Database,
    Frame,
    Point3D,
    PosePrior,
    PosePriorCoordinateSystem,
    Reconstruction,
    Rigid3d,
    SensorType,
    Sim3d,
    data_t,
    sensor_t,
)
from pycolmap import Image as pycolmapImage
from pycolmap._core import apply_rig_config, bundle_adjustment, estimate_two_view_geometry, incremental_mapping  # noqa: PLC2701 — no public API
from scipy.spatial.transform import Rotation

from .metrics_builder import MetricsBuilder
from .options_builder import OptionsBuilder
from .progress_publisher import ReconstructionPublisher
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
    publisher: ReconstructionPublisher,
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
    image_cameras: dict[str, ColmapCamera] = {}
    for rig_id, rig in rigs.items():
        for camera_id, camera in rig.cameras.items():
            colmap_camera_id = database.write_camera(camera[1])

            for frame_id, transform in rig.frame_poses.items():
                image_name = f"{rig_id}/{camera_id}/{frame_id}.jpg"

                colmap_image_ids[image_name] = database.write_image(
                    pycolmapImage(name=image_name, camera_id=colmap_camera_id)
                )
                image_cameras[image_name] = camera[1]
                database.write_keypoints(colmap_image_ids[image_name], keypoints[image_name])

                # Only write pose prior for images from reference sensors (all others are implied by rig)
                if camera[0].ref_sensor:
                    database.write_pose_prior(
                        PosePrior(
                            position=transform.translation.reshape(3, 1),
                            position_covariance=position_covariance,
                            coordinate_system=PosePriorCoordinateSystem.CARTESIAN,
                            corr_data_id=data_t(
                                sensor_t(SensorType.CAMERA, colmap_camera_id),
                                colmap_image_ids[image_name],
                            ),
                        ),
                    )

    # Apply rig configuration to database (must be done after writing cameras and images)
    apply_rig_config([rig.colmap_rig_config for rig in rigs.values()], database)

    # COLMAP assigns rig_t IDs at apply_rig_config time; harvest them so the
    # incremental BA loop can pin every rig's sensor_from_rig transform.
    constant_rigs = {rig.rig_id for rig in database.read_all_rigs()}

    # Write matches to database
    for a, b in pairs:
        (image_a_indices, image_b_indices) = match_indices[(a, b)]
        database.write_matches(
            colmap_image_ids[a],
            colmap_image_ids[b],
            stack((image_a_indices, image_b_indices), axis=1).astype(uint32, copy=False),
        )

    # Per-pair so each completion ticks progress; sqlite writes stay on the main thread.
    publisher.set_phase(ReconstructionStatus.VERIFYING_GEOMETRY, len(pairs))
    verification_options = options.two_view_geometry_options()
    with ThreadPoolExecutor() as pool:
        future_to_pair = {
            pool.submit(
                estimate_two_view_geometry,
                image_cameras[a],
                keypoints[a],
                image_cameras[b],
                keypoints[b],
                stack(match_indices[(a, b)], axis=1).astype(uint32, copy=False),
                verification_options,
            ): (a, b)
            for a, b in pairs
        }
        for completed, future in enumerate(as_completed(future_to_pair), start=1):
            a, b = future_to_pair[future]
            database.write_two_view_geometry(colmap_image_ids[a], colmap_image_ids[b], future.result())
            publisher.on_progress(completed)

    # Close database
    database.close()

    # Compute and store verified matches metrics
    metrics.build_verified_matches_metrics(colmap_db_path, pairs)

    progress = _IncrementalMappingProgress(publisher)

    # Phase total is the candidate image count — an upper bound, since COLMAP may drop images that
    # fail to register or get filtered after bundle adjustment.
    publisher.set_phase(ReconstructionStatus.RECONSTRUCTING, len(colmap_image_ids))
    reconstructions = incremental_mapping(
        database_path=str(colmap_db_path),
        image_path=str(images_path),
        output_path=str(colmap_sfm_directory),
        options=options.incremental_pipeline_options(constant_rigs),
        initial_image_pair_callback=progress.on_initial_image_pair,
        next_image_callback=progress.on_next_image,
    )

    # Check that at least one reconstruction was created
    if len(reconstructions) == 0:
        return None

    # Choose the reconstruction with the most registered images
    # TODO: Write information to metrics about this for visibility
    best_reconstruction = max(reconstructions.values(), key=lambda r: r.num_reg_images())

    # Final standalone BA with rig refinement re-enabled. The incremental loop above ran with
    # rig refinement off (every global BA refining rig poses scales N times); one final pass
    # lets sensor_from_rig settle against the converged geometry.
    bundle_adjustment(best_reconstruction, options.final_bundle_adjustment_options())

    metrics.build_reconstruction_metrics(best_reconstruction)

    # Pose priors are translation constraints expressed in a gravity-aligned VIO world
    # frame. Bundle adjustment with N priors spread over the capture trajectory pins the
    # COLMAP world frame's rotation to within sub-degree of VIO's by construction — the
    # only rotation that lets all N camera positions match their priors is the one that
    # aligns COLMAP world to VIO world. No explicit rotation correction is needed, and
    # introducing one (e.g. snapping a chosen frame's pose to its VIO pose) would force
    # one frame to fit exactly at the cost of pulling every other frame off its prior.
    # All that remains is to translate the origin onto the first registered frame.
    # Sort by integer frame_id so multi-rig captures interleave by timestamp instead of
    # dict-iteration order.
    registered = sorted(_registered_frames(rigs, colmap_image_ids, best_reconstruction), key=lambda entry: entry[0])
    if not registered:
        raise RuntimeError("Could not find anchor frame in best reconstruction")

    _first_frame_id, _first_transform, first_rig_from_world = registered[0]
    first_camera_position = -first_rig_from_world.rotation.matrix().T @ first_rig_from_world.translation
    best_reconstruction.transform(
        Sim3d(concatenate([eye(3, dtype=float64), -first_camera_position.reshape(3, 1)], axis=1))
    )

    # Rigid Umeyama best-fit of map centers to truth — fit not applied; only the residual is
    # kept as the VIO-quality signal that filters unreliable captures from the calibration corpus.
    truth_centers_list: list[NDArray[float64]] = []
    map_centers_list: list[NDArray[float64]] = []
    for _frame_id, transform, rig_from_world in registered:
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


def _registered_frames(
    rigs: dict[str, Rig],
    colmap_image_ids: dict[str, int],
    reconstruction: Reconstruction,
) -> Iterator[tuple[int, Transform, Rigid3d]]:
    # Multi-camera rigs (e.g. ZED stereo) share one Frame per rig+frame, so any registered
    # image of any camera in that frame yields the Frame's rig_from_world.
    for rig_id, rig in rigs.items():
        for frame_id, transform in rig.frame_poses.items():
            for camera_id in rig.cameras.keys():
                image_id = colmap_image_ids[f"{rig_id}/{camera_id}/{frame_id}.jpg"]
                if image_id in reconstruction.images:
                    rig_from_world = cast(Rigid3d, cast(Frame, reconstruction.images[image_id].frame).rig_from_world)  # type: ignore
                    yield int(frame_id), transform, rig_from_world
                    break


class _IncrementalMappingProgress:
    # Tracks per-image registration count across COLMAP's multi-model retries.
    # Each new model attempt begins with the seed pair (count = 2); attempt index
    # bumps when initial_image_pair fires after a previous attempt has registered.

    def __init__(self, publisher: ReconstructionPublisher) -> None:
        self._publisher = publisher
        self._registered = 0
        self._attempt = 1

    def on_initial_image_pair(self) -> None:
        if self._registered > 0:
            self._attempt += 1
        self._registered = 2
        self._publisher.on_progress(self._registered, self._attempt)

    def on_next_image(self) -> None:
        self._registered += 1
        self._publisher.on_progress(self._registered, self._attempt)
