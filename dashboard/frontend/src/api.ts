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

export function listReconstructions(): Promise<Reconstruction[]> {
  return request("/api/reconstructions");
}

export function listLocalizations(): Promise<LocalizationSummary[]> {
  return request("/api/localizations");
}

// 204 No Content on success — no JSON body, so this bypasses `request()`'s response.json() call
// (which would throw on an empty body).
export async function deleteReconstruction(reconstructionId: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/reconstructions/${reconstructionId}`, { method: "DELETE" });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${body}`);
  }
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

export function startPoselessReconstruct(id: string, optionsJson: string | null): Promise<{ job_id: string }> {
  return request(`/api/poseless-sets/${id}/reconstruct`, {
    method: "POST",
    body: JSON.stringify({ options_json: optionsJson }),
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

export function saveLocalizationImages(runId: string, outputDir: string): Promise<{ output_dir: string; count: number }> {
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

export interface BrowseDirectoryEntry {
  name: string;
  path: string;
}

export interface BrowseDirectoryResult {
  path: string;
  parent: string | null;
  entries: BrowseDirectoryEntry[];
}

// `path` omitted starts the browse at the server's home directory.
export function browseDirectories(path?: string): Promise<BrowseDirectoryResult> {
  const query = path ? `?path=${encodeURIComponent(path)}` : "";
  return request(`/api/browse-directories${query}`);
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
