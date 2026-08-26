import { useEffect, useState } from "react";
import { exportPoses, listReconstructions } from "../api";
import { DirectoryBrowserDialog } from "../components/DirectoryBrowserDialog";
import type { Reconstruction } from "../types";

const OUTPUT_DIR_STORAGE_KEY = "placeframe-dashboard.tools.exportPosesOutputDir";
const DEFAULT_FILENAME = "poses.json";

// localStorage can throw (private browsing, quota, disabled site data) or come back empty — either
// way, fall back to no remembered directory rather than breaking the tab.
function readStoredOutputDir(): string {
  try {
    return localStorage.getItem(OUTPUT_DIR_STORAGE_KEY) ?? "";
  } catch {
    return "";
  }
}

function storeOutputDir(path: string): void {
  try {
    localStorage.setItem(OUTPUT_DIR_STORAGE_KEY, path);
  } catch {
    // ignore — remembering the directory is a convenience, not required for the tab to work
  }
}

// Server-side join (the dashboard always runs on the same machine as the CLI, and every path here
// is a Linux path — same assumption the directory browser and image-dir field already make).
function joinPath(dir: string, filename: string): string {
  return `${dir.replace(/\/+$/, "")}/${filename}`;
}

export function ToolsTab() {
  const [reconstructions, setReconstructions] = useState<Reconstruction[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [reconstructionId, setReconstructionId] = useState("");
  const [outputDir, setOutputDirState] = useState(readStoredOutputDir);
  const [outputFilename, setOutputFilename] = useState(DEFAULT_FILENAME);
  const [browsingOutputDir, setBrowsingOutputDir] = useState(false);

  const [converting, setConverting] = useState(false);
  const [result, setResult] = useState<{ output_path: string; count: number } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const succeededReconstructions = reconstructions.filter((r) => r.status === "succeeded");

  function setOutputDir(path: string): void {
    setOutputDirState(path);
    storeOutputDir(path);
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

  function runExport(): void {
    if (!reconstructionId || !outputDir.trim() || !outputFilename.trim()) return;
    setConverting(true);
    setError(null);
    setResult(null);
    exportPoses(reconstructionId, joinPath(outputDir.trim(), outputFilename.trim()))
      .then(setResult)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setConverting(false));
  }

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Tools</h2>
        <button onClick={() => void refresh()} disabled={loading}>
          Refresh
        </button>
      </div>

      {loadError && <div className="banner banner-error">{loadError}</div>}

      <div className="dialog" style={{ width: "auto" }}>
        <h3 style={{ margin: 0 }}>Export reconstruction poses to localization-format JSON</h3>
        <label>
          Reconstruction
          <select value={reconstructionId} onChange={(e) => setReconstructionId(e.target.value)}>
            {succeededReconstructions.length === 0 && <option value="">No succeeded reconstructions</option>}
            {succeededReconstructions.map((r) => (
              <option key={r.id} value={r.id}>
                {r.id} ({r.registered_frame_count ?? "?"} frames)
              </option>
            ))}
          </select>
        </label>
        <label>
          Output directory
          <div style={{ display: "flex", gap: 8 }}>
            <input
              type="text"
              placeholder="/path/to/output/dir"
              value={outputDir}
              onChange={(e) => setOutputDir(e.target.value)}
              style={{ flex: 1 }}
            />
            <button type="button" onClick={() => setBrowsingOutputDir(true)}>
              Browse…
            </button>
          </div>
        </label>
        <label>
          Output filename
          <input
            type="text"
            placeholder={DEFAULT_FILENAME}
            value={outputFilename}
            onChange={(e) => setOutputFilename(e.target.value)}
          />
        </label>
        <div className="dialog-actions">
          <button
            className="primary"
            onClick={runExport}
            disabled={!reconstructionId || !outputDir.trim() || !outputFilename.trim() || converting}
          >
            {converting ? "Converting…" : "Convert"}
          </button>
        </div>
      </div>

      {error && <div className="banner banner-error">{error}</div>}
      {result && (
        <div className="banner banner-success">
          Wrote {result.count} pose(s) to {result.output_path}
        </div>
      )}

      {browsingOutputDir && (
        <DirectoryBrowserDialog
          title="Choose output directory"
          initialPath={outputDir || undefined}
          onSelect={(path) => {
            setOutputDir(path);
            setBrowsingOutputDir(false);
          }}
          onCancel={() => setBrowsingOutputDir(false)}
        />
      )}
    </div>
  );
}
