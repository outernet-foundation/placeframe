import { useEffect, useState } from "react";
import { listReconstructions, pngUrl, startVisualize } from "../api";
import type { Reconstruction, VisualizeResult } from "../types";
import { useJobPoll } from "../useJobPoll";

export function VisualizeTab() {
  const [reconstructions, setReconstructions] = useState<Reconstruction[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [shownReconstructionId, setShownReconstructionId] = useState<string | null>(null);
  const [imageNonce, setImageNonce] = useState(0);

  const job = useJobPoll<VisualizeResult>(activeJobId);

  async function refresh(): Promise<void> {
    setLoading(true);
    setLoadError(null);
    try {
      setReconstructions(await listReconstructions());
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  useEffect(() => {
    if (job?.status === "succeeded" && job.result) {
      setShownReconstructionId(job.result.reconstruction_id);
      setImageNonce((n) => n + 1);
      void refresh();
    }
  }, [job]);

  async function createPng(reconstructionId: string): Promise<void> {
    const { job_id } = await startVisualize(reconstructionId);
    setActiveJobId(job_id);
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Reconstructions</h2>
        <button onClick={() => void refresh()} disabled={loading}>
          Refresh
        </button>
      </div>

      {loadError && <div className="banner banner-error">{loadError}</div>}

      <table className="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Capture ID</th>
            <th>Status</th>
            <th>Created</th>
            <th>Map points</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {reconstructions.map((r) => (
            <tr key={r.id}>
              <td className="mono">{r.id}</td>
              <td className="mono">{r.capture_session_id ?? "—"}</td>
              <td>{r.status}</td>
              <td>{new Date(r.created_at).toLocaleString()}</td>
              <td>{r.map_point_count ?? "—"}</td>
              <td className="actions">
                <button
                  disabled={r.status !== "succeeded" || (job?.status === "running" && activeJobId !== null)}
                  onClick={() => void createPng(r.id)}
                >
                  Create PNG
                </button>
                <button disabled title="Coming soon">
                  Interactive
                </button>
                {r.cached_png_path && (
                  <button onClick={() => { setShownReconstructionId(r.id); setImageNonce((n) => n + 1); }}>
                    View
                  </button>
                )}
              </td>
            </tr>
          ))}
          {!loading && reconstructions.length === 0 && (
            <tr>
              <td colSpan={6} className="empty">
                No reconstructions found.
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {activeJobId && job?.status === "running" && <div className="banner banner-info">Rendering point cloud…</div>}
      {job?.status === "failed" && <div className="banner banner-error">Error: {job.error}</div>}

      {shownReconstructionId && (
        <div className="panel-header">
          <h2>Point cloud — {shownReconstructionId}</h2>
        </div>
      )}
      {shownReconstructionId && (
        // eslint-disable-next-line jsx-a11y/img-redundant-alt
        <img
          key={imageNonce}
          className="pointcloud-image"
          src={pngUrl(shownReconstructionId)}
          alt={`Point cloud for reconstruction ${shownReconstructionId}`}
        />
      )}
    </div>
  );
}
