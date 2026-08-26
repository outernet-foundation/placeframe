import { useEffect, useState } from "react";
import { listReconstructions } from "../api";
import type { Reconstruction } from "../types";

export function VisualizeTab() {
  const [reconstructions, setReconstructions] = useState<Reconstruction[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

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

  function openViewer(reconstructionId: string): void {
    window.open(`/viewer?reconstruction=${reconstructionId}`, "_blank", "width=1280,height=900");
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
                <button disabled={r.status !== "succeeded"} onClick={() => openViewer(r.id)}>
                  View
                </button>
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
    </div>
  );
}
