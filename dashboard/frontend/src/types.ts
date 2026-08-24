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
}

export interface VisualizeResult {
  reconstruction_id: string;
  output: string;
  point_count: number;
  rendered_point_count: number;
}

export type JobKind = "reconstruct" | "visualize";
export type JobStatus = "running" | "succeeded" | "failed";

export interface Job<TResult = unknown> {
  id: string;
  kind: JobKind;
  status: JobStatus;
  reconstruction_id: string | null;
  result: TResult | null;
  error: string | null;
}

export const TERMINAL_STATUSES = new Set(["succeeded", "failed", "cancelled"]);
