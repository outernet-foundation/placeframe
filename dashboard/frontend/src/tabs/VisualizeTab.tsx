import { useEffect, useState } from "react";
import { deleteReconstruction, listLocalizations, listReconstructions } from "../api";
import type { LocalizationSummary, Reconstruction } from "../types";

// Deletion is scoped to terminal, non-successful reconstructions: a `succeeded` reconstruction may
// have localization runs (and, server-side, a LocalizationMap) depending on it, and the API refuses
// to delete a reconstruction with an associated LocalizationMap anyway (see
// docker/api/src/routers/reconstructions.py) — surfacing that as a dashboard error is more
// confusing than just not offering the button for a status where it would almost always fail.
const DELETABLE_STATUSES = new Set(["failed", "cancelled"]);

export function VisualizeTab() {
  const [reconstructions, setReconstructions] = useState<Reconstruction[]>([]);
  const [localizations, setLocalizations] = useState<LocalizationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [deleteTarget, setDeleteTarget] = useState<Reconstruction | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  async function refresh(): Promise<void> {
    setLoading(true);
    setLoadError(null);
    try {
      const [reconstructionList, localizationList] = await Promise.all([listReconstructions(), listLocalizations()]);
      setReconstructions(reconstructionList);
      setLocalizations(localizationList);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  function openViewer(reconstructionId: string, localizationId?: string): void {
    const query = localizationId
      ? `reconstruction=${reconstructionId}&localization=${localizationId}`
      : `reconstruction=${reconstructionId}`;
    window.open(`/viewer?${query}`, "_blank", "width=1280,height=900");
  }

  async function confirmDelete(): Promise<void> {
    if (!deleteTarget) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      await deleteReconstruction(deleteTarget.id);
      setDeleteTarget(null);
      await refresh();
    } catch (err) {
      setDeleteError(err instanceof Error ? err.message : String(err));
    } finally {
      setDeleting(false);
    }
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Localizations</h2>
        <button onClick={() => void refresh()} disabled={loading}>
          Refresh
        </button>
      </div>

      {loadError && <div className="banner banner-error">{loadError}</div>}

      <table className="data-table">
        <thead>
          <tr>
            <th>Run ID</th>
            <th>Reconstruction ID</th>
            <th>Created</th>
            <th>Valid poses</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {localizations.map((run) => (
            <tr key={run.run_id}>
              <td className="mono">{run.run_id}</td>
              <td className="mono">{run.reconstruction_id ?? "—"}</td>
              <td>{run.created_at ? new Date(run.created_at).toLocaleString() : "—"}</td>
              <td>
                {run.valid_count}/{run.image_count}
              </td>
              <td className="actions">
                <button disabled={!run.reconstruction_id} onClick={() => openViewer(run.reconstruction_id as string, run.run_id)}>
                  View
                </button>
              </td>
            </tr>
          ))}
          {!loading && localizations.length === 0 && (
            <tr>
              <td colSpan={5} className="empty">
                No localization runs found.
              </td>
            </tr>
          )}
        </tbody>
      </table>

      <div className="panel-header">
        <h2>Reconstructions</h2>
      </div>

      {deleteError && <div className="banner banner-error">{deleteError}</div>}

      <table className="data-table">
        <thead>
          <tr>
            <th>Reconstruction ID</th>
            <th>Capture ID</th>
            <th>Status</th>
            <th>Created</th>
            <th>Frame type</th>
            <th>Frames used</th>
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
              <td>{r.is_stereo === null ? "—" : r.is_stereo ? "Stereo" : "Mono"}</td>
              <td>
                {r.registered_frame_count !== null && r.total_frame_count !== null
                  ? `${r.registered_frame_count}/${r.total_frame_count}`
                  : "—"}
              </td>
              <td>{r.map_point_count ?? "—"}</td>
              <td className="actions">
                <button disabled={r.status !== "succeeded"} onClick={() => openViewer(r.id)}>
                  View
                </button>
                {DELETABLE_STATUSES.has(r.status) && <button onClick={() => setDeleteTarget(r)}>Delete</button>}
              </td>
            </tr>
          ))}
          {!loading && reconstructions.length === 0 && (
            <tr>
              <td colSpan={8} className="empty">
                No reconstructions found.
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {deleteTarget && (
        <div className="dialog-overlay" onClick={() => (deleting ? null : setDeleteTarget(null))}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <h3>Delete reconstruction?</h3>
            <p>
              This permanently deletes reconstruction <span className="mono">{deleteTarget.id}</span> and its stored
              data (point cloud, poses). This cannot be undone.
            </p>
            <div className="dialog-actions">
              <button onClick={() => setDeleteTarget(null)} disabled={deleting}>
                Cancel
              </button>
              <button className="primary" onClick={() => void confirmDelete()} disabled={deleting}>
                {deleting ? "Deleting…" : "Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
