import type { CaptureSession, Job, LocalizationResult, LocalizationSummary, PoselessImageSet, Reconstruction } from "./types";

const API_BASE = "http://localhost:8010";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${body}`);
  }
  return response.json() as Promise<T>;
}

export function listCaptures(): Promise<CaptureSession[]> {
  return request("/api/captures");
}

// `stats: false` skips each capture's mono/stereo + frame-count lookup (slow) — the tree draws from
// the fast listing and fills those columns in from a second, full one.
export function listReconstructions(stats = true): Promise<Reconstruction[]> {
  return request(`/api/reconstructions${stats ? "" : "?stats=false"}`);
}

// Uploads a server-local reconstruction tar; the API also creates its localization map. A tar can
// only be imported once (it carries a fixed id); `newId` imports it again as a separate copy.
export function importReconstruction(tarPath: string, newId = false): Promise<Reconstruction> {
  return request("/api/reconstructions/import", {
    method: "POST",
    body: JSON.stringify({ tar_path: tarPath, new_id: newId }),
  });
}

export type ImportKind = "image_folder" | "capture_tar" | "reconstruction_tar" | "spherical_video";

export interface ImportResult {
  kind: ImportKind;
  image_set?: PoselessImageSet;
  capture?: CaptureSession;
  reconstruction?: Reconstruction;
  job_id?: string; // a video: extraction, upload and reconstruction take minutes
  name?: string;
}

export interface VideoSettings {
  stride: number | null;
  maxWidth: number | null;
  layout: string | null;
  viewFovDeg: number | null;
}

export interface CaptureEstimate {
  stride: number;
  max_width: number;
  frames: number;
  width: number;
  height: number;
  bytes_per_frame: number;
  total_bytes: number;
  over_limit: boolean;
}

export interface VideoInfo {
  width: number;
  height: number;
  fps: number;
  frame_count: number;
  projection: string | null;
  is_spherical: boolean;
  limit_bytes: number;
  capture?: CaptureEstimate;
}

// What a capture built at these settings would weigh. Asked before importing, because the API
// rejects an oversized body outright and an extraction only reveals its size once it is spent.
// Only the settings that change the frames matter here; the layout is applied at reconstruction
// time, long after the capture is built, so it cannot change its size.
export function estimateVideoCapture(
  path: string,
  settings: Pick<VideoSettings, "stride" | "maxWidth">,
): Promise<VideoInfo> {
  return request("/api/import/estimate", {
    method: "POST",
    body: JSON.stringify({ path, stride: settings.stride, max_width: settings.maxWidth }),
  });
}

// One entry point for everything importable: the backend decides from the path
// whether it is a folder of images, a reconstruction tar, or a spherical video.
export function importPath(path: string, newId = false, settings?: VideoSettings): Promise<ImportResult> {
  return request("/api/import", {
    method: "POST",
    body: JSON.stringify({
      path,
      new_id: newId,
      stride: settings?.stride ?? null,
      max_width: settings?.maxWidth ?? null,
      layout: settings?.layout ?? null,
      view_fov_deg: settings?.viewFovDeg ?? null,
    }),
  });
}

export function listLocalizations(): Promise<LocalizationSummary[]> {
  return request("/api/localizations");
}

// 204 No Content on success — no JSON body, so this bypasses `request()`'s response.json() call
// (which would throw on an empty body).
async function deleteRequest(path: string): Promise<void> {
  const response = await fetch(`${API_BASE}${path}`, { method: "DELETE" });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${body}`);
  }
}

// `cascade` also deletes its localization map (the API refuses while one exists), this machine's
// cached tar/PNG, and its local localization runs.
export function deleteReconstruction(reconstructionId: string, cascade = false): Promise<void> {
  return deleteRequest(`/api/reconstructions/${reconstructionId}${cascade ? "?cascade=true" : ""}`);
}

// Renames the capture session; a linked image folder's local name follows it.
export function renameCapture(captureId: string, name: string): Promise<CaptureSession> {
  return request(`/api/captures/${captureId}`, { method: "PATCH", body: JSON.stringify({ name }) });
}

// The capture's tar and row; `cascade` deletes its reconstructions first (each cascading as above).
export function deleteCapture(captureId: string, cascade = false): Promise<void> {
  return deleteRequest(`/api/captures/${captureId}${cascade ? "?cascade=true" : ""}`);
}

// Removes a finished (or interrupted) run's local results; the backend refuses a running one.
export function deleteLocalization(runId: string): Promise<void> {
  return deleteRequest(`/api/localizations/${runId}`);
}

export function startReconstruct(captureId: string, optionsJson: string | null): Promise<{ job_id: string }> {
  return request("/api/reconstruct", {
    method: "POST",
    body: JSON.stringify({ capture_id: captureId, options_json: optionsJson }),
  });
}

export function listPoselessSets(): Promise<PoselessImageSet[]> {
  return request("/api/poseless-sets");
}

export function registerPoselessSet(path: string): Promise<PoselessImageSet> {
  return request("/api/poseless-sets", {
    method: "POST",
    body: JSON.stringify({ path }),
  });
}

export function renamePoselessSet(id: string, name: string): Promise<PoselessImageSet> {
  return request(`/api/poseless-sets/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ name }),
  });
}

export function startPoselessReconstruct(
  id: string,
  focalLength: number,
  targetKeyframes: number | null,
  optionsJson: string | null,
): Promise<{ job_id: string }> {
  return request(`/api/poseless-sets/${id}/reconstruct`, {
    method: "POST",
    body: JSON.stringify({ focal_length: focalLength, target_keyframes: targetKeyframes, options_json: optionsJson }),
  });
}

export function getJob<TResult = unknown>(jobId: string): Promise<Job<TResult>> {
  return request(`/api/jobs/${jobId}`);
}

export function startLocalize(
  reconstructionId: string,
  imageDir: string,
  retrievalTopK: number | null,
  ransacThreshold: number | null,
  useChunking: boolean,
  fovDeg: number | null,
): Promise<{ job_id: string; run_id: string }> {
  return request("/api/localize", {
    method: "POST",
    body: JSON.stringify({
      reconstruction_id: reconstructionId,
      image_dir: imageDir,
      retrieval_top_k: retrievalTopK,
      ransac_threshold: ransacThreshold,
      use_chunking: useChunking,
      fov_deg: fovDeg,
    }),
  });
}

export function getLocalization(runId: string): Promise<LocalizationResult> {
  return request(`/api/localizations/${runId}`);
}

export interface LocalizationProgress {
  completed: number;
  total: number;
}

export function getLocalizationProgress(runId: string): Promise<LocalizationProgress> {
  return request(`/api/localizations/${runId}/progress`);
}

export function saveLocalizationTable(runId: string, outputPath: string): Promise<{ output_path: string; count: number }> {
  return request(`/api/localizations/${runId}/save-table`, {
    method: "POST",
    body: JSON.stringify({ output_path: outputPath }),
  });
}

export function saveLocalizationImages(
  runId: string,
  outputDir: string,
): Promise<{ output_dir: string; count: number; missing: number }> {
  return request(`/api/localizations/${runId}/save-images`, {
    method: "POST",
    body: JSON.stringify({ output_dir: outputDir }),
  });
}

export function exportPoses(reconstructionId: string, outputPath: string): Promise<{ output_path: string; count: number }> {
  return request("/api/tools/export-poses", {
    method: "POST",
    body: JSON.stringify({ reconstruction_id: reconstructionId, output_path: outputPath }),
  });
}

export function exportReconstructionZip(
  reconstructionId: string,
  outputPath: string,
): Promise<{ output_path: string; file_count: number; size_bytes: number }> {
  return request(`/api/reconstructions/${reconstructionId}/export-zip`, {
    method: "POST",
    body: JSON.stringify({ output_path: outputPath }),
  });
}

export interface BrowseDirectoryEntry {
  name: string;
  path: string;
}

export interface BrowseDirectoryResult {
  path: string;
  parent: string | null;
  entries: BrowseDirectoryEntry[];
  files: BrowseDirectoryEntry[]; // only populated when fileExtensions is given
}

// `path` omitted starts the browse at the server's home directory. `fileExtensions` (e.g.
// [".tar"]) also lists matching files, for picking a file rather than a folder.
export function browseDirectories(path?: string, fileExtensions?: string[]): Promise<BrowseDirectoryResult> {
  const params = new URLSearchParams();
  if (path) params.set("path", path);
  if (fileExtensions?.length) params.set("files", fileExtensions.join(","));
  const query = params.toString();
  return request(`/api/browse-directories${query ? `?${query}` : ""}`);
}

export interface PointCloud {
  positions: Float32Array;
  colors: Uint8Array;
  count: number;
  posePositions: Float32Array;
  poseOrientations: Float32Array; // xyzw quaternions, world_from_rig
  poseCount: number;
  // Capture frame id of each pose, or null for reconstructions written before poses were ordered.
  // Poses are in capture order; a frame id going backwards marks where one capture ends.
  frameIds: Float64Array | null;
}

// Parses the fixed binary layout `points` writes (see howard_test.py's `points` command docstring
// and dashboard/backend's /points passthrough):
//   point_count:u32, positions:f32[point_count*3], colors:u8[point_count*3],
//   pose_count:u32, pose_positions:f32[pose_count*3], pose_orientations(xyzw):f32[pose_count*4],
//   frame_ids:f64[pose_count]
// The frame ids are a later addition and sit last, so a payload from an older reconstruction ends
// after the orientations and is read without them.
export async function fetchPoints(reconstructionId: string): Promise<PointCloud> {
  const response = await fetch(`${API_BASE}/api/reconstructions/${reconstructionId}/points`);
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${body}`);
  }
  const buffer = await response.arrayBuffer();
  const view = new DataView(buffer);

  const count = view.getUint32(0, true);
  const positionsStart = 4;
  const positionsEnd = positionsStart + count * 3 * 4;
  const colorsEnd = positionsEnd + count * 3;

  const poseCount = view.getUint32(colorsEnd, true);
  const posePositionsStart = colorsEnd + 4;
  const posePositionsEnd = posePositionsStart + poseCount * 3 * 4;
  const poseOrientationsEnd = posePositionsEnd + poseCount * 4 * 4;
  const frameIdsEnd = poseOrientationsEnd + poseCount * 8;
  const hasFrameIds = buffer.byteLength >= frameIdsEnd && poseCount > 0;

  return {
    count,
    positions: new Float32Array(buffer.slice(positionsStart, positionsEnd)),
    colors: new Uint8Array(buffer.slice(positionsEnd, colorsEnd)),
    poseCount,
    posePositions: new Float32Array(buffer.slice(posePositionsStart, posePositionsEnd)),
    poseOrientations: new Float32Array(buffer.slice(posePositionsEnd, poseOrientationsEnd)),
    frameIds: hasFrameIds ? new Float64Array(buffer.slice(poseOrientationsEnd, frameIdsEnd)) : null,
  };
}

export interface ScreenshotResult {
  path: string;
}

export function saveScreenshot(
  plotTitle: string,
  imageBase64: string,
  localizationId?: string | null,
): Promise<ScreenshotResult> {
  return request("/api/screenshots", {
    method: "POST",
    body: JSON.stringify({ plot_title: plotTitle, image_base64: imageBase64, localization_id: localizationId ?? null }),
  });
}
