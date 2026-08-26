import { useEffect, useState } from "react";
import { browseDirectories } from "../api";

interface DirectoryBrowserDialogProps {
  title: string;
  initialPath?: string;
  onSelect: (path: string) => void;
  onCancel: () => void;
}

// A server-local directory browser: the dashboard shells out to `howard-test` on the same
// machine, so a picked path has to be a real absolute filesystem path, which a browser's native
// `<input type=file webkitdirectory>` can't provide (it never exposes absolute paths, only a File
// list with paths relative to the picked root). This walks GET /api/browse-directories instead.
export function DirectoryBrowserDialog({ title, initialPath, onSelect, onCancel }: DirectoryBrowserDialogProps) {
  const [path, setPath] = useState(initialPath ?? "");
  const [parent, setParent] = useState<string | null>(null);
  const [entries, setEntries] = useState<{ name: string; path: string }[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function navigate(target: string | undefined): void {
    setLoading(true);
    setError(null);
    browseDirectories(target)
      .then((result) => {
        setPath(result.path);
        setParent(result.parent);
        setEntries(result.entries);
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    navigate(initialPath);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="dialog-overlay" onClick={onCancel}>
      <div className="dialog" onClick={(e) => e.stopPropagation()}>
        <h3>{title}</h3>
        <div className="mono" style={{ wordBreak: "break-all" }}>
          {path}
        </div>
        {error && <div className="banner banner-error">{error}</div>}
        <div style={{ maxHeight: 280, overflowY: "auto", border: "1px solid #3d4149", borderRadius: 4 }}>
          <div
            className="browse-row"
            onClick={() => parent && navigate(parent)}
            style={{ cursor: parent ? "pointer" : "default", opacity: parent ? 1 : 0.4 }}
          >
            .. (up)
          </div>
          {!loading &&
            entries.map((entry) => (
              <div key={entry.path} className="browse-row" onClick={() => navigate(entry.path)}>
                {entry.name}/
              </div>
            ))}
          {!loading && entries.length === 0 && (
            <div style={{ padding: "8px 10px", color: "#6b7280" }}>No subdirectories</div>
          )}
          {loading && <div style={{ padding: "8px 10px", color: "#6b7280" }}>Loading…</div>}
        </div>
        <div className="dialog-actions">
          <button onClick={onCancel}>Cancel</button>
          <button className="primary" onClick={() => onSelect(path)} disabled={!path}>
            Select this folder
          </button>
        </div>
      </div>
    </div>
  );
}
