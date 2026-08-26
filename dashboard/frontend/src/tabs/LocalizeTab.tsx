import { useEffect, useState } from "react";
import { getLocalization, listReconstructions, saveLocalizationImages, saveLocalizationTable, startLocalize } from "../api";
import { DirectoryBrowserDialog } from "../components/DirectoryBrowserDialog";
import type { LocalizationResult, Reconstruction } from "../types";
import { useJobPoll } from "../useJobPoll";
import { useLocalizationProgress } from "../useLocalizationProgress";

type SaveDialog = "table" | "images" | null;

const IMAGE_DIR_STORAGE_KEY = "placeframe-dashboard.localize.imageDir";

// localStorage can throw (private browsing, quota, disabled site data) or come back empty — either
// way, fall back to no remembered directory rather than breaking the tab.
function readStoredImageDir(): string {
  try {
    return localStorage.getItem(IMAGE_DIR_STORAGE_KEY) ?? "";
  } catch {
    return "";
  }
}

function storeImageDir(path: string): void {
  try {
    localStorage.setItem(IMAGE_DIR_STORAGE_KEY, path);
  } catch {
    // ignore — remembering the directory is a convenience, not required for the tab to work
  }
}

export function LocalizeTab() {
  const [reconstructions, setReconstructions] = useState<Reconstruction[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [reconstructionId, setReconstructionId] = useState("");
  const [imageDir, setImageDirState] = useState(readStoredImageDir);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [result, setResult] = useState<LocalizationResult | null>(null);
  const [resultError, setResultError] = useState<string | null>(null);

  const [saveDialog, setSaveDialog] = useState<SaveDialog>(null);
  const [savePath, setSavePath] = useState("");
  const [saveMessage, setSaveMessage] = useState<string | null>(null);

  const [browsingImageDir, setBrowsingImageDir] = useState(false);

  const job = useJobPoll<{ run_id: string }>(activeJobId);
  const jobRunning = activeJobId !== null && job !== null && job.status === "running";
  const progress = useLocalizationProgress(activeRunId, jobRunning);

  const succeededReconstructions = reconstructions.filter((r) => r.status === "succeeded");

  function setImageDir(path: string): void {
    setImageDirState(path);
    storeImageDir(path);
  }

  async function refresh(): Promise<void> {
    setLoading(true);
    setLoadError(null);
    try {
      const list = await listReconstructions();
      setReconstructions(list);
      const stillValid = list.some((r) => r.id === reconstructionId && r.status === "succeeded");
      if (!stillValid) {
        const firstSucceeded = list.find((r) => r.status === "succeeded");
        setReconstructionId(firstSucceeded?.id ?? "");
      }
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (job?.status !== "succeeded" || !job.result) return;
    const runId = job.result.run_id;
    setResultError(null);
    getLocalization(runId)
      .then(setResult)
      .catch((err: unknown) => setResultError(err instanceof Error ? err.message : String(err)));
  }, [job?.status, job?.result]);

  function runLocalize(): void {
    if (!reconstructionId || !imageDir.trim()) return;
    setResult(null);
    setResultError(null);
    startLocalize(reconstructionId, imageDir.trim(), null, null)
      .then(({ job_id, run_id }) => {
        setActiveJobId(job_id);
        setActiveRunId(run_id);
      })
      .catch((err: unknown) => setResultError(err instanceof Error ? err.message : String(err)));
  }

  function openSaveDialog(kind: SaveDialog): void {
    setSaveDialog(kind);
    setSavePath("");
  }

  async function submitSave(): Promise<void> {
    if (!result || !savePath.trim()) return;
    try {
      if (saveDialog === "table") {
        const { output_path, count } = await saveLocalizationTable(result.run_id, savePath.trim());
        setSaveMessage(`Saved ${count} rows to ${output_path}`);
      } else if (saveDialog === "images") {
        const { output_dir, count } = await saveLocalizationImages(result.run_id, savePath.trim());
        setSaveMessage(`Saved ${count} annotated images to ${output_dir}`);
      }
    } catch (err) {
      setSaveMessage(err instanceof Error ? err.message : String(err));
    } finally {
      setSaveDialog(null);
    }
  }

  function openViewer(): void {
    if (!result) return;
    window.open(
      `/viewer?reconstruction=${result.reconstruction_id}&localization=${result.run_id}`,
      "_blank",
      "width=1280,height=900",
    );
  }

  const jobFailed = job !== null && job.status === "failed";

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Localize</h2>
        <button onClick={() => void refresh()} disabled={loading}>
          Refresh
        </button>
      </div>

      {loadError && <div className="banner banner-error">{loadError}</div>}

      <div className="dialog" style={{ width: "auto" }}>
        <label>
          Reconstruction
          <select value={reconstructionId} onChange={(e) => setReconstructionId(e.target.value)}>
            {succeededReconstructions.length === 0 && <option value="">No succeeded reconstructions</option>}
            {succeededReconstructions.map((r) => (
              <option key={r.id} value={r.id}>
                {r.id} ({r.map_point_count ?? "?"} pts)
              </option>
            ))}
          </select>
        </label>
        <label>
          Image directory
          <div style={{ display: "flex", gap: 8 }}>
            <input
              type="text"
              placeholder="/path/to/query/images"
              value={imageDir}
              onChange={(e) => setImageDir(e.target.value)}
              style={{ flex: 1 }}
            />
            <button type="button" onClick={() => setBrowsingImageDir(true)}>
              Browse…
            </button>
          </div>
        </label>
        <div className="dialog-actions">
          <button className="primary" onClick={runLocalize} disabled={!reconstructionId || !imageDir.trim() || jobRunning}>
            {jobRunning ? "Localizing…" : "Run"}
          </button>
        </div>
      </div>

      {jobRunning && (
        <div className="banner banner-info">
          <div>Localizing images against reconstruction {reconstructionId}…</div>
          {progress && progress.total > 0 && (
            <>
              <div className="progress-bar">
                <div
                  className="progress-bar-fill"
                  style={{ width: `${Math.round((progress.completed / progress.total) * 100)}%` }}
                />
              </div>
              <div>
                {progress.completed} out of {progress.total} images
              </div>
            </>
          )}
        </div>
      )}
      {jobFailed && <div className="banner banner-error">Error: {job?.error ?? "unknown error"}</div>}
      {resultError && <div className="banner banner-error">{resultError}</div>}
      {saveMessage && <div className="banner banner-success">{saveMessage}</div>}

      {result && (
        <>
          <div className="panel-header">
            <h2>
              Run {result.run_id} — {result.images.length} images
            </h2>
            <div className="actions">
              <button onClick={() => openSaveDialog("table")}>Save table</button>
              <button onClick={() => openSaveDialog("images")}>Save images</button>
              <button onClick={openViewer}>Visualize poses</button>
            </div>
          </div>

          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Thumbnail</th>
                <th>Filename</th>
                <th>Status</th>
                <th>X</th>
                <th>Y</th>
                <th>Z</th>
                <th>Roll</th>
                <th>Pitch</th>
                <th>Yaw</th>
              </tr>
            </thead>
            <tbody>
              {result.images.map((img) => (
                <tr key={img.index}>
                  <td>{img.index}</td>
                  <td>
                    <img src={img.thumbnail_base64} alt={img.filename} style={{ width: 96, borderRadius: 4 }} />
                  </td>
                  <td className="mono">{img.filename}</td>
                  <td>{img.status}</td>
                  {img.status === "ok" && img.position && img.rpy_deg ? (
                    <>
                      <td>{img.position.x.toFixed(3)}</td>
                      <td>{img.position.y.toFixed(3)}</td>
                      <td>{img.position.z.toFixed(3)}</td>
                      <td>{img.rpy_deg.roll.toFixed(1)}</td>
                      <td>{img.rpy_deg.pitch.toFixed(1)}</td>
                      <td>{img.rpy_deg.yaw.toFixed(1)}</td>
                    </>
                  ) : (
                    <td colSpan={6}>{img.error ?? "failed"}</td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {browsingImageDir && (
        <DirectoryBrowserDialog
          title="Choose image directory"
          initialPath={imageDir || undefined}
          onSelect={(path) => {
            setImageDir(path);
            setBrowsingImageDir(false);
          }}
          onCancel={() => setBrowsingImageDir(false)}
        />
      )}

      {saveDialog && (
        <div className="dialog-overlay" onClick={() => setSaveDialog(null)}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <h3>{saveDialog === "table" ? "Save table to CSV" : "Save annotated images to directory"}</h3>
            <label>
              {saveDialog === "table" ? "Output file path" : "Output directory"}
              <input
                type="text"
                placeholder={saveDialog === "table" ? "/path/to/table.csv" : "/path/to/output_dir"}
                value={savePath}
                onChange={(e) => setSavePath(e.target.value)}
                autoFocus
              />
            </label>
            <div className="dialog-actions">
              <button onClick={() => setSaveDialog(null)}>Cancel</button>
              <button className="primary" onClick={() => void submitSave()} disabled={!savePath.trim()}>
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
