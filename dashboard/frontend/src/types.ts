// is_spherical is null when the capture's manifest could not be read, or when the listing was asked
// not to check; the Export button for rendered views appears only on a definite true.
export interface CaptureSession {
  is_spherical?: boolean | null;
  id: string;
  name: string;
  device_type: string;
  size_bytes: number;
  recorded_at: string;
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

export type JobKind = "reconstruct" | "visualize" | "localize";
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

// `status` of one raw LightGlue match. NO_POINT3D is a match the matcher liked but PnP never
// saw, because the database keypoint carried no triangulated point — distinct from an outlier.
export const MATCH_NO_POINT3D = 0;
export const MATCH_OUTLIER = 1;
export const MATCH_INLIER = 2;

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
