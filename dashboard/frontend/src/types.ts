// is_spherical is null when the capture's manifest could not be read, or when the listing was asked
// not to check; the Export button for rendered views appears only on a definite true.
export interface CaptureSession {
  is_spherical?: boolean | null;
  id: string;
  name: string;
  device_type: string;
  size_bytes: number;
  recorded_at: string;
  // The video a spherical capture was imported from on this machine, when the importer recorded it.
  source_video?: string | null;
}

export interface Reconstruction {
  id: string;
  capture_session_id: string | null;
  status: string;
  created_at: string;
  error: string | null;
  progress_current: number | null;
  progress_total: number | null;
  queue_position: number | null;
  queue_depth: number | null;
  map_point_count: number | null;
  map_image_count: number | null;
  cached_tar_path: string | null;
  cached_png_path: string | null;
  is_stereo: boolean | null;
  total_frame_count: number | null;
  registered_frame_count: number | null;
  capture_name?: string | null; // capture session name; an imported reconstruction's is its tar name
  options?: Record<string, unknown>; // the ReconstructionOptions it was built with
  options_diff?: Record<string, unknown>; // just the options that differ from the server defaults
  localization_map_id?: string | null; // set once published to devices; null means unpublished
  label?: string | null; // a transformed copy's label (what it was aligned to), shown instead of the bare id
  alignment?: Record<string, unknown> | null; // the Sim(3) and provenance recorded by transform-reconstruction
  // The reconstructor's own IMU fit, on a capture that carries the IMU (an .insv import); null otherwise.
  imu_scale?: {
    applied: boolean;
    rejected_because: string | null;
    m_per_unit: number | null;
    sigma_m_per_unit: number | null;
  } | null;
}

/** Imported from a native .insv, so its maps follow the camera body and the IMU can scale them. An
 * Insta360 Studio export is stabilised and carries no IMU; neither does a capture whose source went
 * unrecorded (every .insv import records its source). */
export function isFromInsv(c: CaptureSession | null | undefined): boolean {
  return c?.source_video?.toLowerCase().endsWith(".insv") === true;
}

/** A copy already scaled to metres by its .insv's IMU, which has nothing left to fit. */
export function isImuScaled(r: Reconstruction): boolean {
  return r.alignment?.source === "imu_scale";
}

/** A transformed copy kept only for the viewer: no artifacts to localize against, so it cannot be published. */
export function isViewerOnly(r: Reconstruction): boolean {
  return r.alignment?.viewer_only === true;
}

// A reconstruction published for devices to localize against. Publishing builds nothing: it records
// that this map is one to offer and where its frame sits in the world frame a device localizes into.
export interface LocalizationMap {
  id: string;
  name: string | null;
  reconstruction_id: string;
  capture_session_id: string | null;
  capture_name: string | null;
  device_label: string | null; // the string a device's picker shows, which is the capture's name
  position: { x: number; y: number; z: number };
  rotation: { x: number; y: number; z: number; w: number };
  is_identity_placement: boolean;
  created_at: string | null;
}

export type JobKind = "reconstruct" | "visualize" | "localize" | "icp" | "merge" | "imu_scale";
export type JobStatus = "running" | "succeeded" | "failed";

export interface Job<TResult = unknown> {
  id: string;
  kind: JobKind;
  status: JobStatus;
  reconstruction_id: string | null;
  run_id: string | null;
  result: TResult | null;
  error: string | null;
  progress: JobProgress | null;
  // Set on the align page's jobs (ICP matches and merges), which the captures page shows as rows.
  label?: string | null;
  capture_session_id?: string | null;
  created_at?: string;
  notice?: string | null;
}

/** Where a long step of a job has got to, while it is still running. */
export interface JobProgress {
  phase: string;
  current?: number;
  total?: number;
  detail?: string;
}

export const TERMINAL_STATUSES = new Set(["succeeded", "failed", "cancelled"]);

export interface PoselessImageSet {
  id: string;
  name: string;
  path: string;
  image_count: number;
  recorded_at: string;
  // Set once the folder has been uploaded: later reconstructions reuse this capture unless the
  // focal length changes (it is baked into the capture at upload).
  capture_session_id?: string;
  focal_length?: number;
}

export interface LocalizationMetrics {
  num_inliers: number;
  num_correspondences: number;
  num_matches: number;
  inlier_ratio: number;
  inlier_coverage: number;
  reprojection_error_median: number;
  confidence_tight: number;
  confidence_loose: number;
  confidence_is_calibrated: boolean;
}

export interface LocalizationImage {
  index: number;
  filename: string;
  path: string;
  status: "ok" | "failed";
  error: string | null;
  position: { x: number; y: number; z: number } | null;
  quaternion_xyzw: [number, number, number, number] | null;
  rpy_deg: { roll: number; pitch: number; yaw: number } | null;
  // Absent on runs localized before these were recorded, so both are optional.
  metrics?: LocalizationMetrics | null;
  has_detail?: boolean;
  thumbnail_base64: string;
}

// One registered frame of a reconstruction (an equirect, or one stereo pair), from
// GET /api/reconstructions/{id}/frames. Its images are the views or cameras COLMAP registered for
// that instant; observations and the mean track reprojection error are summed over all of them.
export interface ReconstructionFrame {
  index: number;
  filename: string;
  image_count: number;
  position: { x: number; y: number; z: number };
  quaternion_xyzw: [number, number, number, number];
  rpy_deg: { roll: number; pitch: number; yaw: number };
  observations: number;
  reprojection_error_mean: number | null;
  // Null when the capture's images aren't available (an imported reconstruction).
  thumbnail_base64: string | null;
}

// One frame's registered images with their keypoints, from
// GET /api/reconstructions/{id}/frames/{index}/detail. `width`/`height` are the size COLMAP
// recorded, which the keypoints are in; the served image may be larger and scales uniformly.
// `keypoints` is flattened x, y, error triples; error is the 3D point's track reprojection error,
// or -1 for a keypoint that was never triangulated.
export interface ReconstructionFrameDetail {
  index: number;
  images: { name: string; width: number; height: number; keypoints: number[] }[];
}

export interface ReconstructionFrames {
  reconstruction_id: string;
  frames: ReconstructionFrame[];
}

// `status` of one raw LightGlue match. NO_POINT3D is a match the matcher liked but PnP never
// saw, because the database keypoint carried no triangulated point — distinct from an outlier.
export const MATCH_NO_POINT3D = 0;
export const MATCH_OUTLIER = 1;
export const MATCH_INLIER = 2;

// A localizer `camera_from_map_transform`: world-to-camera, so the camera's own position is
// -R^T t. Quaternion xyzw.
export interface CameraFromMapTransform {
  translation: { x: number; y: number; z: number };
  rotation: { x: number; y: number; z: number; w: number };
}

export interface PairDetail {
  rank: number;
  image_id: number;
  name: string;
  width: number;
  height: number;
  retrieval_score: number;
  num_keypoints: number;
  num_matches: number;
  num_correspondences: number;
  num_inliers: number;
  inlier_ratio: number;
  reprojection_error_median: number | null;
  distance_m: number | null;
  view_angle_deg: number | null;
  // The pose this database image supports on its own (PnP over its correspondences alone), null
  // when it had too few inliers for one. Absent on runs localized before it was recorded.
  camera_from_map_transform?: CameraFromMapTransform | null;
  pose_num_inliers?: number;
  // Parallel arrays over this pair's raw matches. A negative reprojection error means
  // undefined, either because PnP never saw the match or because it reprojected nowhere real.
  query_xy: [number, number][];
  database_xy: [number, number][];
  status: number[];
  reprojection_error_px: number[];
}

export interface LocalizationDetail {
  reconstruction_id: string;
  // The intrinsics the pipeline actually used, in the canonicalized frame every keypoint
  // coordinate below lives in — NOT the displayed image's natural size.
  camera: { width: number; height: number; fx: number; fy: number; cx: number; cy: number };
  retrieval_top_k: number;
  ransac_threshold: number;
  num_query_keypoints: number;
  timings_ms: Record<string, number>;
  pairs: PairDetail[];
  // The pooled estimate, kept when the confidence gate rejected it. Absent on older runs.
  camera_from_map_transform?: CameraFromMapTransform | null;
  metrics: (LocalizationMetrics & { measurement_covariance: number[][]; pnp_covariance: number[][] }) | null;
  gate: { loose_min: number; tight_min: number; passed: boolean } | null;
  failure_reason: string | null;
}

export interface LocalizationResult {
  run_id: string;
  reconstruction_id: string;
  capture_session_id: string;
  image_dir: string;
  created_at: string;
  use_chunking: boolean;
  images: LocalizationImage[];
}

// "incomplete": no result and no live job — interrupted, e.g. by a dashboard restart mid-run.
export type LocalizationRunStatus = "done" | "running" | "failed" | "incomplete";

export interface LocalizationSummary {
  run_id: string;
  reconstruction_id: string | null;
  created_at: string | null;
  image_dir: string | null;
  use_chunking: boolean | null;
  status: LocalizationRunStatus;
  error: string | null;
  progress: { completed: number; total: number } | null;
  image_count: number;
  valid_count: number;
}

// Offline fusion (howard-test offline-fusion): a localization recording replayed against a map.
// Field names are offline_fusion.VpsParams / FusionParams'; null leaves the server's default.
export interface VpsParams {
  interval_s: number;
  latency_s: number;
  retrieval_top_k: number | null;
  ransac_threshold: number | null;
  use_chunking: boolean;
}

export interface FusionParams {
  gate_chi2: number;
  bypass_gate: boolean;
  bypass_kalman: boolean;
  snap_sigmas_sq: number;
  slew_s: number;
  drift_per_m: number;
  base_translation_variance: number;
  base_rotation_variance: number;
  bootstrap_sigma_translation_m: number;
  bootstrap_sigma_rotation_rad: number;
}

export interface FusionRunParams {
  vps: Partial<VpsParams>;
  fusion: Partial<FusionParams>;
}

export type FusionRunStatus = "done" | "running" | "failed" | "incomplete";

export interface FusionRunSummary {
  run_id: string;
  reconstruction_id: string | null;
  recording: string | null;
  created_at: string | null;
  params: FusionRunParams | null;
  status: FusionRunStatus;
  error: string | null;
  // howard-test's progress while running: {phase: "localizing" | "rendering", current, total}.
  progress: { phase: string; current?: number; total?: number } | null;
  frame_count: number | null;
  request_count: number;
  accepted_count: number;
  rejected_count: number;
}

// One video frame's fusion state. fused_position is the camera's position in the map under the
// published alignment: what jumps when a fix lands, and drifts with VIO between fixes.
export interface FusionFrame {
  index: number;
  t: number;
  timestamp_ns: number;
  tracking_state: string;
  has_fix: boolean;
  slewing: boolean;
  sigma_translation_m: number;
  sigma_rotation_deg: number;
  vps_applied: number[];
  fused_position: [number, number, number] | null;
  // How far this frame's change in the alignment moved the camera in the map (VIO motion excluded):
  // the visible jump of a snap, or a slew's step. Null without a fix and on the first frame with one.
  correction_m?: number | null;
}

// "not_applied": localized, but its fix would have landed after the recording ended.
export type FusionRequestStatus = "accepted" | "rejected" | "failed" | "not_applied";

export interface FusionRequest {
  index: number;
  still_timestamp_ns: number;
  request_s: number;
  apply_s: number;
  request_frame: number;
  status: FusionRequestStatus;
  error: string | null;
  mahalanobis_sq: number | null;
  snapped: boolean | null;
  num_inliers: number | null;
  inlier_ratio: number | null;
}

export interface FusionResult {
  run_id: string;
  reconstruction_id: string;
  recording: string;
  created_at: string;
  params: { vps: VpsParams; fusion: FusionParams };
  device_model: string | null;
  width: number;
  height: number;
  frame_count: number;
  still_count: number;
  map_point_count: number;
  frames: FusionFrame[];
  requests: FusionRequest[];
}
