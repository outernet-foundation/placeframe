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
  useAllImages: boolean,
  optionsJson: string | null,
): Promise<{ job_id: string }> {
  return request(`/api/poseless-sets/${id}/reconstruct`, {
    method: "POST",
    body: JSON.stringify({ focal_length: focalLength, use_all_images: useAllImages, options_json: optionsJson }),
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
): Promise<{ job_id: string; run_id: string }> {
  return request("/api/localize", {
    method: "POST",
    body: JSON.stringify({
      reconstruction_id: reconstructionId,
      image_dir: imageDir,
      retrieval_top_k: retrievalTopK,
      ransac_threshold: ransacThreshold,
      use_chunking: useChunking,
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
}

// Parses the fixed binary layout `points` writes (see howard_test.py's `points` command docstring
// and dashboard/backend's /points passthrough):
//   point_count:u32, positions:f32[point_count*3], colors:u8[point_count*3],
//   pose_count:u32, pose_positions:f32[pose_count*3], pose_orientations(xyzw):f32[pose_count*4]
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

  return {
    count,
    positions: new Float32Array(buffer.slice(positionsStart, positionsEnd)),
    colors: new Uint8Array(buffer.slice(positionsEnd, colorsEnd)),
    poseCount,
    posePositions: new Float32Array(buffer.slice(posePositionsStart, posePositionsEnd)),
    poseOrientations: new Float32Array(buffer.slice(posePositionsEnd, poseOrientationsEnd)),
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
