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
    median,
    savez_compressed,
    sign,
    stack,
    uint8,
)
from numpy.linalg import det, norm, svd
from numpy.typing import NDArray  # noqa: TID251 — Phase T piece 3 follow-up migration
from pycolmap import Frame, Point3D, Reconstruction, Rigid3d, Sim3d
from pycolmap._core import bundle_adjustment  # noqa: PLC2701 — no public API
from scipy.spatial.transform import Rotation

from .colmap_pipeline import run_colmap_pipeline_with_vio_check
from .metrics_builder import MetricsBuilder
from .options_builder import OptionsBuilder
from .pairs import PairSource
from .progress_publisher import ReconstructionPublisher
from .rig import FramePose, Rig, image_name

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
    pairs_by_source: dict[PairSource, list[tuple[str, str]]],
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

    reconstructions = run_colmap_pipeline_with_vio_check(
        database_path=colmap_db_path,
        image_path=images_path,
        sfm_output_path=colmap_sfm_directory,
        options=options,
        metrics=metrics,
        rigs=rigs,
        keypoints=keypoints,
        pairs_by_source=pairs_by_source,
        match_indices=match_indices,
        publisher=publisher,
    )

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

    # Sort registered frames by integer timestamp across rigs so "first registered" is the
    # earliest-captured frame the recon kept, regardless of rig.
    registered = sorted(_registered_frames(rigs, best_reconstruction), key=lambda entry: entry[0])
    if not registered:
        raise RuntimeError("Could not find anchor frame in best reconstruction")

    # Align the map frame to gravity via per-frame samples: each frame's gravity-in-rig-local is
    # projected into recon-world by the recon's own rig-rotation for that frame, then aggregated
    # via per-component median and renormalised. Robust to per-frame IMU noise and to VIO tilt
    # drift over the capture. Falls back to identity rotation when no samples are available.
    gravity_samples_in_recon_world = [
        rig_from_world.rotation.matrix().T @ transform.gravity_in_rig_local
        for _frame_id, transform, rig_from_world in registered
        if transform.gravity_in_rig_local is not None
    ]
    if gravity_samples_in_recon_world:
        gravity_stack = stack(gravity_samples_in_recon_world)
        gravity_in_recon_world_estimate = median(gravity_stack, axis=0)
        gravity_in_recon_world_estimate /= norm(gravity_in_recon_world_estimate)
        # OPENCV convention: +Y is the world's "down" axis, so map-frame down is also [0, 1, 0].
        alignment_rotation, _ = Rotation.align_vectors([[0.0, 1.0, 0.0]], [gravity_in_recon_world_estimate])
        rotation_align = alignment_rotation.as_matrix()
        metrics.metrics.gravity_aligned_in_map_frame = True
        metrics.metrics.gravity_sample_count = len(gravity_samples_in_recon_world)
    else:
        rotation_align = eye(3, dtype=float64)
        metrics.metrics.gravity_aligned_in_map_frame = False
        metrics.metrics.gravity_sample_count = 0

    _first_frame_id, _first_transform, first_rig_from_world = registered[0]
    first_camera_position = -first_rig_from_world.rotation.matrix().T @ first_rig_from_world.translation
    translation_align = -rotation_align @ first_camera_position
    best_reconstruction.transform(Sim3d(concatenate([rotation_align, translation_align.reshape(3, 1)], axis=1)))

    # Rigid Umeyama best-fit of map centers to VIO position priors. Fit is not applied — the
    # residual is the prior-drift diagnostic surfaced for calibration-corpus filtering. No signal
    # without position priors, so this skips for multi-camera captures (which carry no per-frame
    # translations by contract).
    if not options.is_multi_camera_capture:
        truth_centers_list: list[NDArray[float64]] = [
            transform.translation.astype(float64)
            for _frame_id, transform, _ in registered
            if transform.translation is not None
        ]
        map_centers_list: list[NDArray[float64]] = [
            -rig_from_world.rotation.matrix().T @ rig_from_world.translation
            for _frame_id, transform, rig_from_world in registered
            if transform.translation is not None
        ]
        if len(truth_centers_list) >= 3:
            truth_centers = asarray(truth_centers_list, dtype=float64)
            map_centers = asarray(map_centers_list, dtype=float64)
            truth_mean, map_mean = truth_centers.mean(axis=0), map_centers.mean(axis=0)
            u, _, vt = svd((map_centers - map_mean).T @ (truth_centers - truth_mean))
            fit_rotation = vt.T @ diag([1.0, 1.0, sign(det(vt.T @ u.T))]) @ u.T
            fit_translation = truth_mean - fit_rotation @ map_mean
            residuals = norm((fit_rotation @ map_centers.T).T + fit_translation - truth_centers, axis=1)
            metrics.metrics.prior_drift_residual_rms_m = float((residuals**2).mean() ** 0.5)
            metrics.metrics.prior_drift_residual_max_m = float(residuals.max())

    # Write the best reconstruction to disk in COLMAP format
    best_reconstruction.write_text(str(output_path))  # pyright: ignore[reportUnknownMemberType] — upstream stub uses unparameterized os.PathLike

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
    reconstruction: Reconstruction,
) -> Iterator[tuple[int, FramePose, Rigid3d]]:
    # Multi-camera rigs (e.g. ZED stereo) share one Frame per rig+frame, so any registered
    # image of any camera in that frame yields the Frame's rig_from_world. The
    # reconstruction's image map already contains only the registered images keyed by the
    # DB-assigned id, so the inverse name→id map is the registered-only subset of the
    # original colmap_image_ids dict — no need to thread it back from the pipeline.
    image_ids_by_name = {reconstruction.images[image_id].name: image_id for image_id in reconstruction.images}
    for rig_id, rig in rigs.items():
        for frame_id, transform in rig.frame_poses.items():
            for camera_id in rig.cameras.keys():
                image_id = image_ids_by_name.get(image_name(rig_id, camera_id, frame_id))
                if image_id is None:
                    continue
                rig_from_world = cast(Rigid3d, cast(Frame, reconstruction.images[image_id].frame).rig_from_world)  # type: ignore
                yield int(frame_id), transform, rig_from_world
                break
