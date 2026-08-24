import type { CaptureSession, Job, Reconstruction } from "./types";

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

export function startReconstruct(captureId: string, optionsJson: string | null): Promise<{ job_id: string }> {
  return request("/api/reconstruct", {
    method: "POST",
    body: JSON.stringify({ capture_id: captureId, options_json: optionsJson }),
  });
}

export function startVisualize(reconstructionId: string): Promise<{ job_id: string }> {
  return request("/api/visualize", {
    method: "POST",
    body: JSON.stringify({ reconstruction_id: reconstructionId }),
  });
}

export function getJob<TResult = unknown>(jobId: string): Promise<Job<TResult>> {
  return request(`/api/jobs/${jobId}`);
}

export function pngUrl(reconstructionId: string): string {
  return `${API_BASE}/api/reconstructions/${reconstructionId}/png?t=${Date.now()}`;
}
