from __future__ import annotations

from bisect import bisect_left
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any, Literal

from placeframe_api_client import ReconstructionStatus

from math import cos, radians
from numpy import asarray, clip, dot, eye, float64, intp, stack, uint32
from numpy.linalg import norm
from numpy.typing import NDArray  # noqa: TID251 — Phase T piece 3 follow-up migration
from pycolmap import INVALID_POINT3D_ID
from pycolmap import Camera as ColmapCamera
from pycolmap import (
    Database,
    Frame,
    IncrementalMapper,
    IncrementalMapperOptions,
    IncrementalPipeline,
    IncrementalPipelineOptions,
    ObservationManager,
    PosePrior,
    PosePriorCoordinateSystem,
    RANSACOptions,
    Reconstruction,
    ReconstructionManager,
    Rigid3d,
    SensorType,
    Sim3d,
    TwoViewGeometry,
    align_reconstruction_to_orig_rig_scales,
    data_t,
    estimate_sim3d_robust,
    sensor_t,
)
from pycolmap import Image as pycolmapImage
from pycolmap._core import apply_rig_config, estimate_two_view_geometry  # noqa: PLC2701 — no public API

from .metrics_builder import MetricsBuilder
from .options_builder import OptionsBuilder, PairPoseGraphOptions
from .pairs import Pair, PairSource
from .progress_publisher import ReconstructionPublisher
from .rig import Rig, image_name

# Mirror of the C++ IncrementalMapperImpl::kMinNumInitialRegTrials constant. After this
# many failures while the reconstruction is still below min_model_size the loop falls
# back to trying a different initial pair instead of grinding through every candidate.
INITIAL_REGISTRATION_TRIALS_LIMIT = 30

# Mapper options halved once per relaxation round when the primary attempt fails to
# register enough images. Upstream halves each option once per round, in order.
INIT_RELAXATION_TARGETS: tuple[Literal["init_min_num_inliers", "init_min_tri_angle"], ...] = (
    "init_min_num_inliers",
    "init_min_tri_angle",
)
INIT_RELAXATION_ROUNDS = 2

# Sim3 has 7 degrees of freedom and needs 3 non-collinear point correspondences for a
# unique fit. The check requires at least 3 more correspondences beyond that to give the
# residual statistic any signal — below this count the local-Umeyama prediction is
# mathematically vacuous and the registration is accepted by default.
VIO_CHECK_MIN_NEIGHBORS = 6

# Cap on the number of nearest-in-time already-registered VIO neighbors used to fit the
# local Umeyama. Larger windows leak secular VIO drift into the fit; the cap keeps the
# fit anchored to the local trajectory segment.
VIO_CHECK_WINDOW = 10


@dataclass(frozen=True)
class VioFrameData:
    timestamp_ns: int
    position: NDArray[float64]


@dataclass(frozen=True)
class PipelineContext:
    database: Database
    options: OptionsBuilder
    publisher: ReconstructionPublisher


@dataclass(frozen=True)
class IncrementalContext:
    mapper: IncrementalMapper
    mapper_options: IncrementalMapperOptions
    pipeline_options: IncrementalPipelineOptions
    controller: IncrementalPipeline
    reconstruction_manager: ReconstructionManager
    database: Database
    skipped_image_ids: set[int]
    vio_data_by_image_id: dict[int, VioFrameData]
    # (timestamp_ns, image_id) sorted by timestamp_ns. Lets vio_check bisect for the
    # nearest-in-time neighbors instead of scanning every registered image per call.
    sorted_vio_entries: list[tuple[int, int]]
    vio_check_max_disagreement_m: float
    pose_graph_options: PairPoseGraphOptions
    # Sorted (image_id_low, image_id_high) tuple keyed to pair source. Lets the per-frame
    # pose-graph check attribute rejections back to the source that admitted the pair.
    pair_source_by_image_pair: dict[tuple[int, int], PairSource]
    # Mutable counters threaded through frozen dataclass; printed once at run end.
    pose_graph_rejections: dict[PairSource, int]
    publisher: ReconstructionPublisher


@dataclass
class IncrementalLoopState:
    register_next_succeeded: bool
    previous_register_next_succeeded: bool
    previous_global_refinement_registered_frame_count: int
    previous_global_refinement_point_count: int


class TrialOutcome(Enum):
    NEXT_TRIAL = auto()
    NEXT_RELAXATION = auto()
    COMPLETE = auto()


def run_colmap_pipeline_with_vio_check(
    database_path: Path,
    image_path: Path,
    sfm_output_path: Path,
    options: OptionsBuilder,
    metrics: MetricsBuilder,
    rigs: dict[str, Rig],
    keypoints: dict[str, Any],
    pairs: list[Pair],
    match_indices: dict[tuple[str, str], tuple[NDArray[intp], NDArray[intp]]],
    publisher: ReconstructionPublisher,
) -> dict[int, Reconstruction]:
    if not image_path.exists():
        raise FileNotFoundError(f"Image path does not exist: {image_path}")
    sfm_output_path.mkdir(exist_ok=True, parents=True)

    # Two-phase ingest. Phase 1 builds a trajectory from short-baseline pairs only
    # (intra_frame_stereo, sequential, spatial); retrieval pairs are withheld from the database so
    # they cannot poison the seed or any same-registration PnP solve. Phase 2 ingests retrieval
    # matches into the same database against the now-stiff Phase 1 reconstruction with existing
    # frames fixed, triangulates the new loop-closure tracks, then releases the fixed-frame
    # constraint for a final global BA that absorbs the closures. The pose-graph consistency
    # check runs in both phases; in Phase 2 its oracle (the existing model) is uncontaminated by
    # construction, which is the regime where it carries the most leverage.
    phase_1_pairs = [pair for pair in pairs if pair.source != PairSource.RETRIEVAL]
    phase_2_pairs = [pair for pair in pairs if pair.source == PairSource.RETRIEVAL]

    with Database.open(str(database_path)) as database:  # pyright: ignore[reportUnknownMemberType] — upstream stub uses unparameterized os.PathLike
        pipeline_context = PipelineContext(database=database, options=options, publisher=publisher)
        colmap_image_ids, image_cameras, vio_data_by_image_id = _seed_database_images(pipeline_context, rigs, keypoints)
        pair_source_by_image_pair: dict[tuple[int, int], PairSource] = {}
        for pair in pairs:
            image_id_a = colmap_image_ids[pair.image_a]
            image_id_b = colmap_image_ids[pair.image_b]
            image_id_pair = (image_id_a, image_id_b) if image_id_a < image_id_b else (image_id_b, image_id_a)
            pair_source_by_image_pair[image_id_pair] = pair.source
        pose_graph_rejections: dict[PairSource, int] = dict.fromkeys(PairSource, 0)

        _write_pair_matches(pipeline_context, phase_1_pairs, match_indices, colmap_image_ids)
        publisher.set_phase(ReconstructionStatus.VERIFYING_GEOMETRY, len(phase_1_pairs))
        _verify_two_view_geometries(
            pipeline_context, image_cameras, keypoints, phase_1_pairs, match_indices, colmap_image_ids
        )

        # Phase total is the candidate image count — an upper bound, since COLMAP may drop images that
        # fail to register or get filtered after bundle adjustment.
        publisher.set_phase(ReconstructionStatus.RECONSTRUCTING, len(colmap_image_ids))
        reconstruction_manager = _run_incremental_reconstruction(
            pipeline_context,
            image_path,
            vio_data_by_image_id,
            pair_source_by_image_pair,
            pose_graph_rejections,
        )

        if phase_2_pairs and reconstruction_manager.size() > 0:
            _write_pair_matches(pipeline_context, phase_2_pairs, match_indices, colmap_image_ids)
            publisher.set_phase(ReconstructionStatus.VERIFYING_GEOMETRY, len(phase_2_pairs))
            _verify_two_view_geometries(
                pipeline_context, image_cameras, keypoints, phase_2_pairs, match_indices, colmap_image_ids
            )
            publisher.set_phase(ReconstructionStatus.RECONSTRUCTING, len(colmap_image_ids))
            _run_phase2_retrieval_ingest(
                pipeline_context,
                reconstruction_manager,
                phase_2_pairs,
                colmap_image_ids,
                pair_source_by_image_pair,
                pose_graph_rejections,
            )

        metrics.build_verified_matches_metrics(database, pairs)
        _log_pose_graph_summary(pose_graph_rejections)

    reconstruction_manager.write(str(sfm_output_path))  # pyright: ignore[reportUnknownMemberType] — upstream stub uses unparameterized os.PathLike
    return {index: reconstruction_manager.get(index) for index in range(reconstruction_manager.size())}


def _seed_database_images(
    pipeline_context: PipelineContext,
    rigs: dict[str, Rig],
    keypoints: dict[str, Any],
) -> tuple[dict[str, int], dict[str, ColmapCamera], dict[int, VioFrameData]]:
    position_covariance = (pipeline_context.options.pose_prior_position_sigma_m() ** 2) * eye(3, dtype=float64)

    colmap_image_ids: dict[str, int] = {}
    image_cameras: dict[str, ColmapCamera] = {}
    vio_data_by_image_id: dict[int, VioFrameData] = {}

    for rig_id, rig in rigs.items():
        for camera_id, camera in rig.cameras.items():
            colmap_camera_id = pipeline_context.database.write_camera(camera[1])

            for frame_id, transform in rig.frame_poses.items():
                name = image_name(rig_id, camera_id, frame_id)
                colmap_image_id = pipeline_context.database.write_image(
                    pycolmapImage(name=name, camera_id=colmap_camera_id)
                )
                colmap_image_ids[name] = colmap_image_id
                image_cameras[name] = camera[1]
                pipeline_context.database.write_keypoints(colmap_image_id, keypoints[name])

                # PosePrior is the BA-side consumer of per-frame VIO positions. Multi-camera captures
                # carry positions in frames.csv so pair-generation can use them as a spatial signal,
                # but BA must not see them: VIO drift baked into a quadratic loss tears global
                # geometry apart on revisits (the original priors-off motivation). Stereo baseline
                # anchors metric scale instead.
                if (
                    camera[0].ref_sensor
                    and not pipeline_context.options.is_multi_camera_capture
                    and transform.translation is not None
                ):
                    pipeline_context.database.write_pose_prior(
                        PosePrior(
                            position=transform.translation.reshape(3, 1),
                            position_covariance=position_covariance,
                            coordinate_system=PosePriorCoordinateSystem.CARTESIAN,
                            corr_data_id=data_t(
                                sensor_t(SensorType.CAMERA, colmap_camera_id),
                                colmap_image_id,
                            ),
                        ),
                    )

                # Skipping frames without a translation leaves them outside the VIO check entirely:
                # gravity-only frames have no metric position for the local-Umeyama prediction.
                if transform.translation is not None:
                    vio_data_by_image_id[colmap_image_id] = VioFrameData(
                        timestamp_ns=int(frame_id),
                        position=transform.translation,
                    )

    apply_rig_config([rig.colmap_rig_config for rig in rigs.values()], pipeline_context.database)

    return colmap_image_ids, image_cameras, vio_data_by_image_id


def _write_pair_matches(
    pipeline_context: PipelineContext,
    pairs: list[Pair],
    match_indices: dict[tuple[str, str], tuple[NDArray[intp], NDArray[intp]]],
    colmap_image_ids: dict[str, int],
) -> None:
    for pair in pairs:
        pipeline_context.database.write_matches(
            colmap_image_ids[pair.image_a],
            colmap_image_ids[pair.image_b],
            stack(match_indices[(pair.image_a, pair.image_b)], axis=1).astype(uint32, copy=False),
        )


def _verify_two_view_geometries(
    pipeline_context: PipelineContext,
    image_cameras: dict[str, ColmapCamera],
    keypoints: dict[str, Any],
    pairs: list[Pair],
    match_indices: dict[tuple[str, str], tuple[NDArray[intp], NDArray[intp]]],
    colmap_image_ids: dict[str, int],
) -> None:
    verification_options_by_source = {
        source: pipeline_context.options.retrieval_two_view_geometry_options()
        if source == PairSource.RETRIEVAL
        else pipeline_context.options.two_view_geometry_options()
        for source in PairSource
    }

    rejected_by_source: dict[PairSource, int] = dict.fromkeys(PairSource, 0)
    pair_min_match_spread = pipeline_context.options.pair_min_match_spread()

    # Per-pair so each completion ticks progress; sqlite writes stay on the main thread.
    with ThreadPoolExecutor() as pool:
        future_to_pair: dict[Future[TwoViewGeometry], Pair] = {}
        for pair in pairs:
            future_to_pair[
                pool.submit(
                    estimate_two_view_geometry,
                    image_cameras[pair.image_a],
                    keypoints[pair.image_a],
                    image_cameras[pair.image_b],
                    keypoints[pair.image_b],
                    stack(match_indices[(pair.image_a, pair.image_b)], axis=1).astype(uint32, copy=False),
                    verification_options_by_source[pair.source],
                )
            ] = pair
        for completed, future in enumerate(as_completed(future_to_pair), start=1):
            pair = future_to_pair[future]
            two_view_geometry = future.result()
            if _pair_passes_match_spread(
                two_view_geometry,
                keypoints[pair.image_a],
                keypoints[pair.image_b],
                image_cameras[pair.image_a],
                image_cameras[pair.image_b],
                pair_min_match_spread,
            ):
                pipeline_context.database.write_two_view_geometry(
                    colmap_image_ids[pair.image_a], colmap_image_ids[pair.image_b], two_view_geometry
                )
            else:
                rejected_by_source[pair.source] += 1
            pipeline_context.publisher.on_progress(completed)

    print(
        "Match-spread filter rejections: "
        + ", ".join(f"{source.value}={count}" for source, count in rejected_by_source.items())
    )


def _pair_passes_match_spread(
    two_view_geometry: TwoViewGeometry,
    keypoints_a: NDArray[Any],
    keypoints_b: NDArray[Any],
    camera_a: ColmapCamera,
    camera_b: ColmapCamera,
    pair_min_match_spread: float,
) -> bool:
    # Per-image spread = geometric mean of per-axis std of inlier-match keypoint positions,
    # normalized by image dimensions. Pair spread = min(spread_a, spread_b). Aliased pairs
    # that match on a small visually-similar region (the repeated-decor pattern in cubicle
    # offices) concentrate matches in a tiny image region in BOTH images, yielding a low
    # pair spread. True wide-baseline matches spread across the image. Threshold of 0
    # disables; pairs with fewer than 4 inliers are also bypassed since std is too noisy.
    if pair_min_match_spread <= 0:
        return True
    inlier_matches: NDArray[uint32] = two_view_geometry.inlier_matches  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType] — upstream stub uses unbound TypeVar for inlier_matches shape
    if len(inlier_matches) < 4:
        return True
    positions_a = keypoints_a[inlier_matches[:, 0], :2] / asarray([camera_a.width, camera_a.height], dtype=float64)
    positions_b = keypoints_b[inlier_matches[:, 1], :2] / asarray([camera_b.width, camera_b.height], dtype=float64)
    std_a = positions_a.std(axis=0)
    std_b = positions_b.std(axis=0)
    spread_a = float((std_a[0] * std_a[1]) ** 0.5)
    spread_b = float((std_b[0] * std_b[1]) ** 0.5)
    return min(spread_a, spread_b) >= pair_min_match_spread


def _run_incremental_reconstruction(
    pipeline_context: PipelineContext,
    image_path: Path,
    vio_data_by_image_id: dict[int, VioFrameData],
    pair_source_by_image_pair: dict[tuple[int, int], PairSource],
    pose_graph_rejections: dict[PairSource, int],
) -> ReconstructionManager:
    # COLMAP assigns rig_t IDs at apply_rig_config time; harvest them so the incremental BA
    # loop can pin every rig's sensor_from_rig transform.
    pipeline_options = pipeline_context.options.incremental_pipeline_options({
        rig.rig_id for rig in pipeline_context.database.read_all_rigs()
    })
    pipeline_options.image_path = image_path

    reconstruction_manager = ReconstructionManager()
    controller = IncrementalPipeline(pipeline_options, pipeline_context.database, reconstruction_manager)
    if controller.database_cache.num_images() == 0:
        raise RuntimeError("No images survived two-view geometry verification")

    context = IncrementalContext(
        mapper=IncrementalMapper(controller.database_cache),
        mapper_options=pipeline_options.get_mapper(),
        pipeline_options=pipeline_options,
        controller=controller,
        reconstruction_manager=reconstruction_manager,
        database=pipeline_context.database,
        skipped_image_ids=set(),
        vio_data_by_image_id=vio_data_by_image_id,
        sorted_vio_entries=sorted((data.timestamp_ns, image_id) for image_id, data in vio_data_by_image_id.items()),
        vio_check_max_disagreement_m=pipeline_context.options.vio_check_max_disagreement_m(),
        pose_graph_options=pipeline_context.options.pair_pose_graph_options(),
        pair_source_by_image_pair=pair_source_by_image_pair,
        pose_graph_rejections=pose_graph_rejections,
        publisher=pipeline_context.publisher,
    )

    # relaxation_target=None is the primary attempt: no stop-check, no relaxation. Each later
    # entry halves one init threshold.
    for relaxation_target in (None, *(INIT_RELAXATION_TARGETS * INIT_RELAXATION_ROUNDS)):
        if relaxation_target is not None:
            if context.mapper.num_total_reg_images() == context.controller.database_cache.num_images():
                break
            print(f"[colmap_pipeline] Relaxing {relaxation_target}")
            if relaxation_target == "init_min_num_inliers":
                context.mapper_options.init_min_num_inliers = int(context.mapper_options.init_min_num_inliers / 2)
            else:
                context.mapper_options.init_min_tri_angle /= 2
            context.mapper.reset_initialization_stats()

        for _ in range(context.pipeline_options.init_num_trials):
            outcome = _run_single_trial(context)
            if outcome == TrialOutcome.NEXT_RELAXATION:
                break
            if outcome == TrialOutcome.COMPLETE:
                return reconstruction_manager

    return reconstruction_manager


def _run_phase2_retrieval_ingest(
    pipeline_context: PipelineContext,
    reconstruction_manager: ReconstructionManager,
    phase_2_pairs: list[Pair],
    colmap_image_ids: dict[str, int],
    pair_source_by_image_pair: dict[tuple[int, int], PairSource],
    pose_graph_rejections: dict[PairSource, int],
) -> None:
    # Retrieval-ingest pass against the converged Phase 1 reconstruction. Fresh
    # IncrementalPipeline binds a fresh DatabaseCache to the augmented database (now containing
    # retrieval matches and two-view geometries), and the new IncrementalMapper resumes the
    # existing Reconstruction via begin_reconstruction. fix_existing_frames pins Phase 1 poses
    # during triangulation, complete_and_merge_tracks, and retriangulate so the retrieval
    # correspondences cannot pull the model toward themselves before the pose-graph
    # consistency check has a stiff oracle to judge them against. The flag is released for
    # the final global BA so the closures can deform the graph.
    pipeline_options = pipeline_context.options.incremental_pipeline_options({
        rig.rig_id for rig in pipeline_context.database.read_all_rigs()
    })

    best_index = max(
        range(reconstruction_manager.size()),
        key=lambda index: reconstruction_manager.get(index).num_reg_images(),
    )
    best_reconstruction = reconstruction_manager.get(best_index)

    controller = IncrementalPipeline(pipeline_options, pipeline_context.database, reconstruction_manager)
    mapper = IncrementalMapper(controller.database_cache)
    mapper.begin_reconstruction(best_reconstruction)

    mapper_options = pipeline_options.get_mapper()
    mapper_options.fix_existing_frames = True

    triangulation_options = pipeline_options.get_triangulation()

    context = IncrementalContext(
        mapper=mapper,
        mapper_options=mapper_options,
        pipeline_options=pipeline_options,
        controller=controller,
        reconstruction_manager=reconstruction_manager,
        database=pipeline_context.database,
        skipped_image_ids=set(),
        vio_data_by_image_id={},
        sorted_vio_entries=[],
        vio_check_max_disagreement_m=pipeline_context.options.vio_check_max_disagreement_m(),
        pose_graph_options=pipeline_context.options.pair_pose_graph_options(),
        pair_source_by_image_pair=pair_source_by_image_pair,
        pose_graph_rejections=pose_graph_rejections,
        publisher=pipeline_context.publisher,
    )

    registered_image_ids = set(best_reconstruction.reg_image_ids())
    retrieval_touched_image_ids: set[int] = set()
    for pair in phase_2_pairs:
        image_id_a = colmap_image_ids[pair.image_a]
        image_id_b = colmap_image_ids[pair.image_b]
        if image_id_a in registered_image_ids:
            retrieval_touched_image_ids.add(image_id_a)
        if image_id_b in registered_image_ids:
            retrieval_touched_image_ids.add(image_id_b)

    print(
        f"[phase2] retrieval pairs={len(phase_2_pairs)} touched registered images="
        f"{len(retrieval_touched_image_ids)} of {len(registered_image_ids)} total"
    )

    for image_id in retrieval_touched_image_ids:
        mapper.triangulate_image(triangulation_options, image_id)
        _check_and_excise_poisoned_pairs(context, best_reconstruction, image_id)

    mapper.complete_and_merge_tracks(triangulation_options)
    mapper.retriangulate(triangulation_options)

    mapper_options.fix_existing_frames = False
    _iterative_global_refinement(pipeline_options, mapper_options, mapper)

    best_reconstruction.update_point_3d_errors()
    mapper.end_reconstruction(False)
    align_reconstruction_to_orig_rig_scales(controller.database_cache.rigs, best_reconstruction)


def _run_single_trial(context: IncrementalContext) -> TrialOutcome:
    reconstruction_index = context.reconstruction_manager.add()
    reconstruction = context.reconstruction_manager.get(reconstruction_index)
    context.mapper.begin_reconstruction(reconstruction)

    initial_pair_data = context.mapper.find_initial_image_pair(
        context.mapper_options,
        context.pipeline_options.init_image_id1,
        context.pipeline_options.init_image_id2,
    )
    if initial_pair_data is None:
        context.mapper.end_reconstruction(True)
        context.reconstruction_manager.delete(reconstruction_index)
        return TrialOutcome.NEXT_RELAXATION
    initial_pair = initial_pair_data[0]

    context.mapper.register_initial_image_pair(context.mapper_options, *initial_pair, initial_pair_data[1])

    triangulation_options = context.pipeline_options.get_triangulation()
    triangulation_options.min_angle = context.mapper_options.init_min_tri_angle
    for image_id in initial_pair:
        frame = reconstruction.images[image_id].frame
        assert frame is not None
        for data_id in frame.image_ids:
            context.mapper.triangulate_image(triangulation_options, data_id.id)

    context.mapper.adjust_global_bundle(context.mapper_options, context.pipeline_options.get_global_bundle_adjustment())
    reconstruction.normalize()
    context.mapper.filter_points(context.mapper_options)
    context.mapper.filter_frames(context.mapper_options)

    if reconstruction.num_reg_frames() == 0 or reconstruction.num_points3D() == 0:
        context.mapper.end_reconstruction(True)
        context.reconstruction_manager.delete(reconstruction_index)
        return TrialOutcome.NEXT_TRIAL

    context.publisher.on_initial_pair()

    state = IncrementalLoopState(
        register_next_succeeded=True,
        previous_register_next_succeeded=True,
        previous_global_refinement_registered_frame_count=reconstruction.num_reg_frames(),
        previous_global_refinement_point_count=reconstruction.num_points3D(),
    )
    while state.register_next_succeeded or state.previous_register_next_succeeded:
        if _run_incremental_registration_step(state, context, reconstruction):
            break

    # Final global BA when the last incremental refinement was local-only.
    if reconstruction.num_reg_frames() > 0 and not (
        reconstruction.num_reg_frames() == state.previous_global_refinement_registered_frame_count
        and reconstruction.num_points3D() == state.previous_global_refinement_point_count
    ):
        _iterative_global_refinement(context.pipeline_options, context.mapper_options, context.mapper)

    registered_image_count = reconstruction.num_reg_images()
    if (
        context.pipeline_options.multiple_models
        and context.reconstruction_manager.size() > 1
        and registered_image_count < context.pipeline_options.min_model_size
    ) or registered_image_count == 0:
        context.mapper.end_reconstruction(True)
        context.reconstruction_manager.delete(reconstruction_index)
    else:
        reconstruction.update_point_3d_errors()
        context.mapper.end_reconstruction(False)
        align_reconstruction_to_orig_rig_scales(context.controller.database_cache.rigs, reconstruction)

    if (
        not context.pipeline_options.multiple_models
        or context.reconstruction_manager.size() >= context.pipeline_options.max_num_models
        or context.mapper.num_total_reg_images() >= context.controller.database_cache.num_images() - 1
    ):
        return TrialOutcome.COMPLETE

    return TrialOutcome.NEXT_TRIAL


def _run_incremental_registration_step(
    state: IncrementalLoopState,
    context: IncrementalContext,
    reconstruction: Reconstruction,
) -> bool:
    state.previous_register_next_succeeded = state.register_next_succeeded
    next_image_id = _find_and_register_next_image(context, reconstruction, structure_less=False)
    if next_image_id is None:
        next_image_id = _find_and_register_next_image(context, reconstruction, structure_less=True)
    state.register_next_succeeded = next_image_id is not None

    if next_image_id is not None:
        frame = reconstruction.images[next_image_id].frame
        assert frame is not None
        for data_id in frame.image_ids:
            context.mapper.triangulate_image(context.pipeline_options.get_triangulation(), data_id.id)
            _check_and_excise_poisoned_pairs(context, reconstruction, data_id.id)
        context.mapper.iterative_local_refinement(
            context.pipeline_options.ba_local_max_refinements,
            context.pipeline_options.ba_local_max_refinement_change,
            context.mapper_options,
            context.pipeline_options.get_local_bundle_adjustment(),
            context.pipeline_options.get_triangulation(),
            next_image_id,
        )
        if context.controller.check_run_global_refinement(
            reconstruction,
            state.previous_global_refinement_registered_frame_count,
            state.previous_global_refinement_point_count,
        ):
            _iterative_global_refinement(context.pipeline_options, context.mapper_options, context.mapper)
            state.previous_global_refinement_point_count = reconstruction.num_points3D()
            state.previous_global_refinement_registered_frame_count = reconstruction.num_reg_frames()
        context.publisher.on_next_image()

    if context.mapper.num_shared_reg_images() >= int(context.pipeline_options.max_model_overlap):
        return True

    if (not state.register_next_succeeded) and state.previous_register_next_succeeded:
        _iterative_global_refinement(context.pipeline_options, context.mapper_options, context.mapper)

    return False


def _find_and_register_next_image(
    context: IncrementalContext,
    reconstruction: Reconstruction,
    structure_less: bool,
) -> int | None:
    next_images = [
        i
        for i in context.mapper.find_next_images(context.mapper_options, structure_less=structure_less)
        if i not in context.skipped_image_ids
    ]
    register = (
        context.mapper.register_next_structure_less_image if structure_less else context.mapper.register_next_image
    )

    for registration_trial, candidate_image_id in enumerate(next_images):
        if not register(context.mapper_options, candidate_image_id):
            # If the initial pair fails to grow the model for a while, abort and try
            # a different initial pair instead of grinding through every candidate.
            if (
                registration_trial >= INITIAL_REGISTRATION_TRIALS_LIMIT
                and reconstruction.num_reg_images() < context.pipeline_options.min_model_size
            ):
                break
            continue

        if vio_check(
            context.vio_data_by_image_id,
            context.sorted_vio_entries,
            reconstruction,
            candidate_image_id,
            context.vio_check_max_disagreement_m,
        ):
            return candidate_image_id

        # Skip-list every image attached to this frame — multi-camera rigs share one
        # frame across all cameras, and deregister_frame removes them all together.
        # Adding only candidate_image_id would let find_next_images re-suggest the
        # other stereo image at the same (rejected) pose on the next iteration.
        rejected_frame = reconstruction.images[candidate_image_id].frame
        assert rejected_frame is not None
        context.skipped_image_ids.update(data_id.id for data_id in rejected_frame.image_ids)
        # ObservationManager.deregister_frame walks the correspondence graph,
        # decrements num_visible_correspondences on every Point2D's neighbors, deletes
        # Point3D observations, then internally calls Reconstruction::DeRegisterFrame.
        # Calling Reconstruction.deregister_frame directly skips the correspondence-graph
        # cleanup and leaves the next triangulate_image to hit
        # `num_tri_corrs <= num_total_corrs`. Note IncrementalMapper::DeRegisterFrameEvent
        # (private in COLMAP, not exposed in pycolmap) also normally fires here to keep
        # the mapper's per-rig / per-camera reg_stats_ counters in sync with reality;
        # skipping it leaves find_next_images' scoring slightly skewed but does not crash.
        context.mapper.observation_manager.deregister_frame(rejected_frame.frame_id)

    return None


def _check_and_excise_poisoned_pairs(
    context: IncrementalContext,
    reconstruction: Reconstruction,
    new_image_id: int,
) -> None:
    # Pair-level pose-graph consistency. For each already-registered partner sharing a
    # verified two-view geometry with the just-triangulated new_image_id, compare the
    # partner's pair-implied relative pose against the partial reconstruction's estimated
    # relative pose. Partners exceeding rotation or translation-direction thresholds are
    # flagged poisoned; their inlier-match observations on new_image_id are deleted from
    # the observation manager before the next local BA pass. The pose graph is too soft
    # to be a reliable oracle below pose_graph_min_registered_frames — the check returns
    # early in that regime and the front-door filters (covisibility, drift budget,
    # vio_check) carry the load until the graph stiffens.
    pose_graph_options = context.pose_graph_options
    if pose_graph_options.max_rotation_disagreement_deg <= 0 and pose_graph_options.max_translation_direction_deg <= 0:
        return
    if reconstruction.num_reg_images() < pose_graph_options.min_registered_frames:
        return
    if new_image_id not in reconstruction.images:
        return

    cos_max_rotation = (
        cos(radians(pose_graph_options.max_rotation_disagreement_deg))
        if pose_graph_options.max_rotation_disagreement_deg > 0
        else -2.0
    )
    cos_max_translation_direction = (
        cos(radians(pose_graph_options.max_translation_direction_deg))
        if pose_graph_options.max_translation_direction_deg > 0
        else -2.0
    )

    for partner_id in reconstruction.reg_image_ids():
        if partner_id == new_image_id:
            continue
        image_id_low, image_id_high = (
            (new_image_id, partner_id) if new_image_id < partner_id else (partner_id, new_image_id)
        )
        if not context.database.exists_two_view_geometry(image_id_low, image_id_high):
            continue

        two_view_geometry = context.database.read_two_view_geometry(image_id_low, image_id_high)
        implied_high_from_low = two_view_geometry.cam2_from_cam1
        if implied_high_from_low is None:
            continue
        rotation_disagreement_cos, translation_direction_cos, estimated_baseline_m = _pose_graph_disagreement(
            reconstruction, image_id_low, image_id_high, implied_high_from_low
        )
        rotation_failed = (
            pose_graph_options.max_rotation_disagreement_deg > 0 and rotation_disagreement_cos < cos_max_rotation
        )
        translation_failed = (
            pose_graph_options.max_translation_direction_deg > 0
            and estimated_baseline_m >= pose_graph_options.min_baseline_m
            and translation_direction_cos < cos_max_translation_direction
        )
        if not (rotation_failed or translation_failed):
            continue

        excised = _excise_pair_observations(
            context.mapper.observation_manager,
            reconstruction,
            two_view_geometry,
            new_image_id,
            partner_id,
            new_is_low=new_image_id == image_id_low,
        )
        source = context.pair_source_by_image_pair.get((image_id_low, image_id_high))
        if source is not None:
            context.pose_graph_rejections[source] += 1
        _log_pose_graph_rejection(
            new_image_id=new_image_id,
            partner_id=partner_id,
            source=source,
            rotation_failed=rotation_failed,
            translation_failed=translation_failed,
            excised=excised,
        )


def _pose_graph_disagreement(
    reconstruction: Reconstruction,
    image_id_low: int,
    image_id_high: int,
    implied_high_from_low: Rigid3d,
) -> tuple[float, float, float]:
    cam_low_from_world: Rigid3d = reconstruction.images[image_id_low].cam_from_world()
    cam_high_from_world: Rigid3d = reconstruction.images[image_id_high].cam_from_world()
    estimated_high_from_low: Rigid3d = cam_high_from_world * cam_low_from_world.inverse()

    estimated_rotation: NDArray[float64] = estimated_high_from_low.rotation.matrix()
    implied_rotation: NDArray[float64] = implied_high_from_low.rotation.matrix()
    rotation_trace = float((estimated_rotation @ implied_rotation.T).trace())
    rotation_disagreement_cos = float(clip((rotation_trace - 1.0) / 2.0, -1.0, 1.0))

    estimated_translation: NDArray[float64] = estimated_high_from_low.translation
    implied_translation: NDArray[float64] = implied_high_from_low.translation
    estimated_baseline_m = float(norm(estimated_translation))
    implied_translation_norm = float(norm(implied_translation))
    if estimated_baseline_m > 0 and implied_translation_norm > 0:
        translation_direction_cos = float(
            clip(
                dot(estimated_translation / estimated_baseline_m, implied_translation / implied_translation_norm),
                -1.0,
                1.0,
            )
        )
    else:
        translation_direction_cos = 1.0
    return rotation_disagreement_cos, translation_direction_cos, estimated_baseline_m


def _excise_pair_observations(
    observation_manager: ObservationManager,
    reconstruction: Reconstruction,
    two_view_geometry: TwoViewGeometry,
    new_image_id: int,
    partner_id: int,
    new_is_low: bool,
) -> int:
    inlier_matches: NDArray[uint32] = two_view_geometry.inlier_matches  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType] — upstream stub uses unbound TypeVar for inlier_matches shape
    if len(inlier_matches) == 0:
        return 0
    new_image = reconstruction.images[new_image_id]
    partner_image = reconstruction.images[partner_id]
    excised_count = 0
    for match in inlier_matches:
        new_kp_idx = int(match[0]) if new_is_low else int(match[1])
        partner_kp_idx = int(match[1]) if new_is_low else int(match[0])
        shared_point3d_id = new_image.point2D(new_kp_idx).point3D_id
        if (
            shared_point3d_id != INVALID_POINT3D_ID
            and shared_point3d_id == partner_image.point2D(partner_kp_idx).point3D_id
        ):
            observation_manager.delete_observation(new_image_id, new_kp_idx)
            excised_count += 1
    return excised_count


def vio_check(
    vio_by_image_id: dict[int, VioFrameData],
    sorted_vio_entries: list[tuple[int, int]],
    reconstruction: Reconstruction,
    image_id: int,
    max_disagreement_m: float,
) -> bool:
    query = _resolve_vio_pose(vio_by_image_id, reconstruction, image_id)
    if query is None:
        _log_vio_check(image_id, passed=True, disagreement_m=None, neighbor_count=0)
        return True
    query_data, _, query_reconstruction_position = query

    # Walk outward from the query's timestamp in sorted-VIO order, picking the closer-in-time
    # side at each step. setdefault on frame_id dedups multi-camera neighbors (stereo images of
    # one frame share rig_from_world and VIO position, so each frame contributes once).
    candidates_by_frame: dict[int, tuple[NDArray[float64], NDArray[float64]]] = {}
    query_index = bisect_left(sorted_vio_entries, (query_data.timestamp_ns,))
    left, right = query_index - 1, query_index
    while len(candidates_by_frame) < VIO_CHECK_WINDOW and (left >= 0 or right < len(sorted_vio_entries)):
        if left < 0:
            candidate_image_id = sorted_vio_entries[right][1]
            right += 1
        elif (
            right >= len(sorted_vio_entries)
            or query_data.timestamp_ns - sorted_vio_entries[left][0]
            <= sorted_vio_entries[right][0] - query_data.timestamp_ns
        ):
            candidate_image_id = sorted_vio_entries[left][1]
            left -= 1
        else:
            candidate_image_id = sorted_vio_entries[right][1]
            right += 1

        if candidate_image_id == image_id:
            continue
        resolved = _resolve_vio_pose(vio_by_image_id, reconstruction, candidate_image_id)
        if resolved is None:
            continue
        candidate_data, candidate_frame_id, reconstruction_position = resolved
        candidates_by_frame.setdefault(candidate_frame_id, (candidate_data.position, reconstruction_position))

    if len(candidates_by_frame) < VIO_CHECK_MIN_NEIGHBORS:
        _log_vio_check(image_id, passed=True, disagreement_m=None, neighbor_count=len(candidates_by_frame))
        return True

    vio_points = asarray([vio_position for vio_position, _ in candidates_by_frame.values()], dtype=float64)
    reconstruction_points = asarray(
        [reconstruction_position for _, reconstruction_position in candidates_by_frame.values()], dtype=float64
    )

    # LO-RANSAC Sim3 fit (vio -> recon). max_error sets the inlier tolerance: same scale as the
    # final rejection threshold, so a "tolerable" neighbor and a "tolerable" query are judged
    # against the same metric. Returns None for degenerate inputs (stationary device, collinear
    # neighbors, etc.) — vacuous accept.
    ransac_options = RANSACOptions()
    ransac_options.max_error = max_disagreement_m
    fit = _robust_sim3_fit(vio_points, reconstruction_points, ransac_options)
    if fit is None:
        _log_vio_check(image_id, passed=True, disagreement_m=None, neighbor_count=len(candidates_by_frame))
        return True

    disagreement_m = float(norm(fit * query_data.position - query_reconstruction_position))
    passed = disagreement_m <= max_disagreement_m
    _log_vio_check(image_id, passed=passed, disagreement_m=disagreement_m, neighbor_count=len(candidates_by_frame))
    return passed


def _resolve_vio_pose(
    vio_by_image_id: dict[int, VioFrameData],
    reconstruction: Reconstruction,
    image_id: int,
) -> tuple[VioFrameData, int, NDArray[float64]] | None:
    if (
        (vio_data := vio_by_image_id.get(image_id)) is not None
        and image_id in reconstruction.images
        and (frame := reconstruction.images[image_id].frame) is not None
        and (position := _frame_position(frame)) is not None
    ):
        return vio_data, frame.frame_id, position
    return None


def _robust_sim3_fit(src: NDArray[float64], tgt: NDArray[float64], options: RANSACOptions) -> Sim3d | None:
    # pycolmap 4.0.4 stub declares `-> Sim3d | None` but the binding actually returns
    # `dict | None` with the Sim3d under `tgt_from_src` (alongside `num_inliers` and
    # `inlier_mask`). Confined to this helper so the rest of the file holds the honest
    # Sim3d | None type.
    result = estimate_sim3d_robust(src, tgt, options)
    if result is None:
        return None
    return result["tgt_from_src"]  # type: ignore[index]


def _log_vio_check(image_id: int, *, passed: bool, disagreement_m: float | None, neighbor_count: int) -> None:
    disagreement_str = "vacuous" if disagreement_m is None else f"{disagreement_m:.6f}"
    print(
        f"[vio_check] image_id={image_id} neighbors={neighbor_count} disagreement_m={disagreement_str} passed={passed}"
    )


def _log_pose_graph_rejection(
    *,
    new_image_id: int,
    partner_id: int,
    source: PairSource | None,
    rotation_failed: bool,
    translation_failed: bool,
    excised: int,
) -> None:
    reasons = ",".join(
        reason for reason, failed in (("rotation", rotation_failed), ("translation", translation_failed)) if failed
    )
    source_str = source.value if source is not None else "unknown"
    print(
        f"[pose_graph_check] image_id={new_image_id} partner_id={partner_id} "
        f"source={source_str} reason={reasons} excised={excised}"
    )


def _log_pose_graph_summary(rejections: dict[PairSource, int]) -> None:
    print(
        "Pose-graph consistency rejections: "
        + ", ".join(f"{source.value}={count}" for source, count in rejections.items())
    )


def _iterative_global_refinement(
    options: IncrementalPipelineOptions,
    mapper_options: IncrementalMapperOptions,
    mapper: IncrementalMapper,
) -> None:
    mapper.iterative_global_refinement(
        options.ba_global_max_refinements,
        options.ba_global_max_refinement_change,
        mapper_options,
        options.get_global_bundle_adjustment(),
        options.get_triangulation(),
    )
    mapper.filter_frames(mapper_options)


def _frame_position(frame: Frame) -> NDArray[float64] | None:
    rig_from_world: Rigid3d | None = frame.rig_from_world
    if rig_from_world is None:
        return None
    return -rig_from_world.rotation.matrix().T @ rig_from_world.translation
