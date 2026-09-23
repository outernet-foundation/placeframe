import { useEffect, useState } from "react";
import { browseDirectories } from "../api";

interface DirectoryBrowserDialogProps {
  title: string;
  initialPath?: string;
  onSelect: (path: string) => void;
  onCancel: () => void;
  // File mode: list files with these suffixes (e.g. [".tar"]) and select one of them instead of a
  // folder. Omitted, the dialog picks a folder, as before.
  fileExtensions?: string[];
  // With fileExtensions, also allow choosing the folder itself — for Import, where
  // a folder of images and a file are both things to import.
  allowFolders?: boolean;
}

// A server-local directory browser: the dashboard shells out to `howard-test` on the same
// machine, so a picked path has to be a real absolute filesystem path, which a browser's native
// `<input type=file webkitdirectory>` can't provide (it never exposes absolute paths, only a File
// list with paths relative to the picked root). This walks GET /api/browse-directories instead.
export function DirectoryBrowserDialog({
  title,
  initialPath,
  onSelect,
  onCancel,
  fileExtensions,
  allowFolders,
}: DirectoryBrowserDialogProps) {
  const fileMode = (fileExtensions?.length ?? 0) > 0;
  const [path, setPath] = useState(initialPath ?? "");
  const [parent, setParent] = useState<string | null>(null);
  const [entries, setEntries] = useState<{ name: string; path: string }[]>([]);
  const [files, setFiles] = useState<{ name: string; path: string }[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  function navigate(target: string | undefined): void {
    setLoading(true);
    setError(null);
    setSelectedFile(null);
    browseDirectories(target, fileExtensions)
      .then((result) => {
        setPath(result.path);
        setParent(result.parent);
        setEntries(result.entries);
        setFiles(result.files ?? []);
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : String(err)))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    navigate(initialPath);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const empty = entries.length === 0 && (!fileMode || files.length === 0);

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
          {!loading &&
            fileMode &&
            files.map((file) => (
              <div
                key={file.path}
                className="browse-row mono"
                onClick={() => setSelectedFile(file.path)}
                onDoubleClick={() => onSelect(file.path)}
                style={file.path === selectedFile ? { background: "#2d4a7a" } : undefined}
              >
                {file.name}
              </div>
            ))}
          {!loading && empty && (
            <div style={{ padding: "8px 10px", color: "#6b7280" }}>
              {fileMode ? `No subdirectories or ${fileExtensions!.join("/")} files` : "No subdirectories"}
            </div>
          )}
          {loading && <div style={{ padding: "8px 10px", color: "#6b7280" }}>Loading…</div>}
        </div>
        <div className="dialog-actions">
          <button onClick={onCancel}>Cancel</button>
          {fileMode && allowFolders ? (
            <button className="primary" onClick={() => onSelect(selectedFile ?? path)} disabled={!path && !selectedFile}>
              {selectedFile ? "Select file" : "Select this folder"}
            </button>
          ) : fileMode ? (
            <button className="primary" onClick={() => selectedFile && onSelect(selectedFile)} disabled={!selectedFile}>
              Select file
            </button>
          ) : (
            <button className="primary" onClick={() => onSelect(path)} disabled={!path}>
              Select this folder
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
