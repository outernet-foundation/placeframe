export interface CaptureSession {
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

export interface LocalizationImage {
  index: number;
  filename: string;
  path: string;
  status: "ok" | "failed";
  error: string | null;
  position: { x: number; y: number; z: number } | null;
  quaternion_xyzw: [number, number, number, number] | null;
  rpy_deg: { roll: number; pitch: number; yaw: number } | null;
  thumbnail_base64: string;
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
