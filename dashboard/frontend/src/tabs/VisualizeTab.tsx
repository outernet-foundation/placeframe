import { useEffect, useState } from "react";
import { deleteReconstruction, exportReconstructionZip, listLocalizations, listReconstructions } from "../api";
import { DirectoryBrowserDialog } from "../components/DirectoryBrowserDialog";
import type { LocalizationSummary, Reconstruction } from "../types";

// Deletion is scoped to terminal, non-successful reconstructions: a `succeeded` reconstruction may
// have localization runs (and, server-side, a LocalizationMap) depending on it, and the API refuses
// to delete a reconstruction with an associated LocalizationMap anyway (see
// docker/api/src/routers/reconstructions.py) — surfacing that as a dashboard error is more
// confusing than just not offering the button for a status where it would almost always fail.
const DELETABLE_STATUSES = new Set(["failed", "cancelled"]);

const EXPORT_DIR_STORAGE_KEY = "placeframe-dashboard.visualize.exportZipOutputDir";

// localStorage can throw (private browsing, quota, disabled site data) or come back empty — either
// way, fall back to no remembered directory rather than breaking the tab. Same pattern as the
// Tools tab's export-poses output directory.
function readStoredExportDir(): string {
  try {
    return localStorage.getItem(EXPORT_DIR_STORAGE_KEY) ?? "";
  } catch {
    return "";
  }
}

function storeExportDir(path: string): void {
  try {
    localStorage.setItem(EXPORT_DIR_STORAGE_KEY, path);
  } catch {
    // ignore — remembering the directory is a convenience, not required for the tab to work
  }
}

// Server-side join (the dashboard always runs on the same machine as the CLI, and every path here
// is a Linux path — same assumption ToolsTab's joinPath makes).
function joinPath(dir: string, filename: string): string {
  return `${dir.replace(/\/+$/, "")}/${filename}`;
}

export function VisualizeTab() {
  const [reconstructions, setReconstructions] = useState<Reconstruction[]>([]);
  const [localizations, setLocalizations] = useState<LocalizationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [deleteTarget, setDeleteTarget] = useState<Reconstruction | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const [exportTarget, setExportTarget] = useState<Reconstruction | null>(null);
  const [exportDir, setExportDirState] = useState(readStoredExportDir);
  const [exportFilename, setExportFilename] = useState("");
  const [browsingExportDir, setBrowsingExportDir] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportResult, setExportResult] = useState<{ output_path: string; file_count: number } | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  function setExportDir(path: string): void {
    setExportDirState(path);
    storeExportDir(path);
  }

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

  function openExportDialog(r: Reconstruction): void {
    setExportTarget(r);
    setExportFilename(`${r.id}.zip`);
    setExportResult(null);
    setExportError(null);
  }

  async function confirmExport(): Promise<void> {
    if (!exportTarget || !exportDir.trim() || !exportFilename.trim()) return;
    setExporting(true);
    setExportError(null);
    try {
      const result = await exportReconstructionZip(exportTarget.id, joinPath(exportDir.trim(), exportFilename.trim()));
      setExportResult(result);
      setExportTarget(null);
    } catch (err) {
      setExportError(err instanceof Error ? err.message : String(err));
    } finally {
      setExporting(false);
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
      {exportError && <div className="banner banner-error">{exportError}</div>}
      {exportResult && (
        <div className="banner banner-success">
          Wrote {exportResult.file_count} file(s) to {exportResult.output_path}
        </div>
      )}

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
                {r.status === "succeeded" && <button onClick={() => openExportDialog(r)}>Export</button>}
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

      {exportTarget && (
        <div className="dialog-overlay" onClick={() => (exporting ? null : setExportTarget(null))}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <h3>Export reconstruction as .zip</h3>
            <p>
              Exports the map data (point cloud, camera poses, features) for reconstruction{" "}
              <span className="mono">{exportTarget.id}</span>.
            </p>
            <label>
              Output directory
              <div style={{ display: "flex", gap: 8 }}>
                <input
                  type="text"
                  placeholder="/path/to/output/dir"
                  value={exportDir}
                  onChange={(e) => setExportDir(e.target.value)}
                  style={{ flex: 1 }}
                />
                <button type="button" onClick={() => setBrowsingExportDir(true)}>
                  Browse…
                </button>
              </div>
            </label>
            <label>
              Output filename
              <input type="text" value={exportFilename} onChange={(e) => setExportFilename(e.target.value)} />
            </label>
            <div className="dialog-actions">
              <button onClick={() => setExportTarget(null)} disabled={exporting}>
                Cancel
              </button>
              <button
                className="primary"
                onClick={() => void confirmExport()}
                disabled={exporting || !exportDir.trim() || !exportFilename.trim()}
              >
                {exporting ? "Exporting…" : "Export"}
              </button>
            </div>
          </div>
        </div>
      )}

      {browsingExportDir && (
        <DirectoryBrowserDialog
          title="Choose output directory"
          initialPath={exportDir || undefined}
          onSelect={(path) => {
            setExportDir(path);
            setBrowsingExportDir(false);
          }}
          onCancel={() => setBrowsingExportDir(false)}
        />
      )}
    </div>
  );
}
