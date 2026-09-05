import { useEffect, useState } from "react";
import { listCaptures, listPoselessSets, registerPoselessSet, renamePoselessSet, startPoselessReconstruct, startReconstruct } from "../api";
import { DirectoryBrowserDialog } from "../components/DirectoryBrowserDialog";
import type { CaptureSession, PoselessImageSet, Reconstruction } from "../types";
import { TERMINAL_STATUSES } from "../types";
import { useJobPoll } from "../useJobPoll";

function formatSize(bytes: number): string {
  const units = ["B", "KB", "MB", "GB"];
  let size = bytes;
  let unit = 0;
  while (size >= 1024 && unit < units.length - 1) {
    size /= 1024;
    unit += 1;
  }
  return `${size.toFixed(1)} ${units[unit]}`;
}

export function ReconstructTab() {
  const [captures, setCaptures] = useState<CaptureSession[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [dialogCaptureId, setDialogCaptureId] = useState<string | null>(null);
  const [optionsJson, setOptionsJson] = useState("");
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  const [poselessSets, setPoselessSets] = useState<PoselessImageSet[]>([]);
  const [poselessLoading, setPoselessLoading] = useState(true);
  const [poselessLoadError, setPoselessLoadError] = useState<string | null>(null);
  const [showDirectoryPicker, setShowDirectoryPicker] = useState(false);
  const [editingNameId, setEditingNameId] = useState<string | null>(null);
  const [editingNameValue, setEditingNameValue] = useState("");
  const [poselessActiveJobId, setPoselessActiveJobId] = useState<string | null>(null);

  const job = useJobPoll<Reconstruction>(activeJobId);
  const poselessJob = useJobPoll<Reconstruction>(poselessActiveJobId);

  async function refresh(): Promise<void> {
    setLoading(true);
    setLoadError(null);
    try {
      setCaptures(await listCaptures());
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function refreshPoseless(): Promise<void> {
    setPoselessLoading(true);
    setPoselessLoadError(null);
    try {
      setPoselessSets(await listPoselessSets());
    } catch (err) {
      setPoselessLoadError(err instanceof Error ? err.message : String(err));
    } finally {
      setPoselessLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
    void refreshPoseless();
  }, []);

  async function onSelectDirectory(path: string): Promise<void> {
    setShowDirectoryPicker(false);
    try {
      await registerPoselessSet(path);
      await refreshPoseless();
    } catch (err) {
      setPoselessLoadError(err instanceof Error ? err.message : String(err));
    }
  }

  function startEditingName(set: PoselessImageSet): void {
    setEditingNameId(set.id);
    setEditingNameValue(set.name);
  }

  async function commitEditingName(): Promise<void> {
    if (!editingNameId) return;
    const id = editingNameId;
    const name = editingNameValue.trim();
    setEditingNameId(null);
    if (!name) return;
    try {
      await renamePoselessSet(id, name);
      await refreshPoseless();
    } catch (err) {
      setPoselessLoadError(err instanceof Error ? err.message : String(err));
    }
  }

  async function reconstructPoseless(id: string): Promise<void> {
    const { job_id } = await startPoselessReconstruct(id, null);
    setPoselessActiveJobId(job_id);
  }

  function openDialog(captureId: string): void {
    setDialogCaptureId(captureId);
    setOptionsJson("");
  }

  async function submitReconstruct(): Promise<void> {
    if (!dialogCaptureId) return;
    const { job_id } = await startReconstruct(dialogCaptureId, optionsJson.trim() || null);
    setActiveJobId(job_id);
    setDialogCaptureId(null);
  }

  const jobDone = job !== null && job.status !== "running";
  const reconstruction = job?.result ?? null;

  const poselessJobDone = poselessJob !== null && poselessJob.status !== "running";
  const poselessReconstruction = poselessJob?.result ?? null;

  return (
    <>
    <div className="panel">
      <div className="panel-header">
        <h2>Captures</h2>
        <button onClick={() => void refresh()} disabled={loading}>
          Refresh
        </button>
      </div>

      {loadError && <div className="banner banner-error">{loadError}</div>}

      <table className="data-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Device</th>
            <th>Size</th>
            <th>Recorded</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {captures.map((c) => (
            <tr key={c.id}>
              <td className="mono">{c.id}</td>
              <td>{c.name}</td>
              <td>{c.device_type}</td>
              <td>{formatSize(c.size_bytes)}</td>
              <td>{new Date(c.recorded_at).toLocaleString()}</td>
              <td>
                <button onClick={() => openDialog(c.id)}>Reconstruct</button>
              </td>
            </tr>
          ))}
          {!loading && captures.length === 0 && (
            <tr>
              <td colSpan={6} className="empty">
                No captures found.
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {activeJobId && (
        <div className={`banner ${jobDone ? (job?.status === "succeeded" ? "banner-success" : "banner-error") : "banner-info"}`}>
          {job === null && <span>Starting…</span>}
          {job !== null && (
            <>
              <div>
                Reconstruction {job.reconstruction_id ?? "…"} — {reconstruction?.status ?? job.status}
                {reconstruction?.queue_position != null && ` (queue ${reconstruction.queue_position}/${reconstruction.queue_depth})`}
              </div>
              {reconstruction?.progress_total != null && (
                <div>
                  Progress: {reconstruction.progress_current}/{reconstruction.progress_total}
                </div>
              )}
              {reconstruction?.status === "succeeded" && (
                <div>Map points: {reconstruction.map_point_count}, images: {reconstruction.map_image_count}</div>
              )}
              {(job.error || (reconstruction && TERMINAL_STATUSES.has(reconstruction.status) && reconstruction.status !== "succeeded")) && (
                <div>Error: {job.error ?? reconstruction?.error ?? "unknown error"}</div>
              )}
            </>
          )}
        </div>
      )}

      {dialogCaptureId && (
        <div className="dialog-overlay" onClick={() => setDialogCaptureId(null)}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <h3>New reconstruction</h3>
            <label>
              Capture
              <select value={dialogCaptureId} onChange={(e) => setDialogCaptureId(e.target.value)}>
                {captures.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name} ({c.id})
                  </option>
                ))}
              </select>
            </label>
            <label>
              Options (JSON, optional overrides for ReconstructionOptions)
              <textarea
                rows={6}
                placeholder='{"ransac_max_error": 2.0}'
                value={optionsJson}
                onChange={(e) => setOptionsJson(e.target.value)}
              />
            </label>
            <div className="dialog-actions">
              <button onClick={() => setDialogCaptureId(null)}>Cancel</button>
              <button className="primary" onClick={() => void submitReconstruct()}>
                Reconstruct
              </button>
            </div>
          </div>
        </div>
      )}
    </div>

    <div className="panel" style={{ marginTop: 32 }}>
      <div className="panel-header">
        <h2>Poseless Image Sets</h2>
        <button onClick={() => setShowDirectoryPicker(true)}>Upload</button>
      </div>

      {poselessLoadError && <div className="banner banner-error">{poselessLoadError}</div>}

      <table className="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Number of images</th>
            <th>Recorded</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {poselessSets.map((s) => (
            <tr key={s.id}>
              <td>
                {editingNameId === s.id ? (
                  <input
                    autoFocus
                    value={editingNameValue}
                    onChange={(e) => setEditingNameValue(e.target.value)}
                    onBlur={() => void commitEditingName()}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") void commitEditingName();
                      if (e.key === "Escape") setEditingNameId(null);
                    }}
                  />
                ) : (
                  <span className="editable-name" onClick={() => startEditingName(s)} title="Click to rename">
                    {s.name}
                  </span>
                )}
              </td>
              <td>{s.image_count}</td>
              <td>{new Date(s.recorded_at).toLocaleString()}</td>
              <td>
                <button onClick={() => void reconstructPoseless(s.id)}>Reconstruct</button>
              </td>
            </tr>
          ))}
          {!poselessLoading && poselessSets.length === 0 && (
            <tr>
              <td colSpan={4} className="empty">
                No poseless image sets yet — click Upload to pick a folder of sequentially-ordered images.
              </td>
            </tr>
          )}
        </tbody>
      </table>

      {poselessActiveJobId && (
        <div
          className={`banner ${
            poselessJobDone ? (poselessJob?.status === "succeeded" ? "banner-success" : "banner-error") : "banner-info"
          }`}
        >
          {poselessJob === null && <span>Starting…</span>}
          {poselessJob !== null && (
            <>
              <div>
                Reconstruction {poselessJob.reconstruction_id ?? "…"} — {poselessReconstruction?.status ?? poselessJob.status}
                {poselessReconstruction?.queue_position != null &&
                  ` (queue ${poselessReconstruction.queue_position}/${poselessReconstruction.queue_depth})`}
              </div>
              {poselessReconstruction?.progress_total != null && (
                <div>
                  Progress: {poselessReconstruction.progress_current}/{poselessReconstruction.progress_total}
                </div>
              )}
              {poselessReconstruction?.status === "succeeded" && (
                <div>
                  Map points: {poselessReconstruction.map_point_count}, images: {poselessReconstruction.map_image_count}
                </div>
              )}
              {(poselessJob.error ||
                (poselessReconstruction &&
                  TERMINAL_STATUSES.has(poselessReconstruction.status) &&
                  poselessReconstruction.status !== "succeeded")) && (
                <div>Error: {poselessJob.error ?? poselessReconstruction?.error ?? "unknown error"}</div>
              )}
            </>
          )}
        </div>
      )}

      {showDirectoryPicker && (
        <DirectoryBrowserDialog
          title="Select a folder of images"
          onSelect={(path) => void onSelectDirectory(path)}
          onCancel={() => setShowDirectoryPicker(false)}
        />
      )}
    </div>
    </>
  );
}
