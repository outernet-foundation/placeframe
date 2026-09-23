import { useEffect, useState } from "react";
import { getLocalization } from "../api";
import { errorText } from "../storage";
import type { LocalizationResult } from "../types";

// A localization run's per-image table (thumbnail, status, pose), shown inline under the run.
// results.json is fetched once per run and cached for the page's lifetime.
const cache = new Map<string, LocalizationResult>();

export function RunResults({ runId }: { runId: string }) {
  const [result, setResult] = useState<LocalizationResult | null>(cache.get(runId) ?? null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (cache.has(runId)) return;
    getLocalization(runId)
      .then((r) => {
        cache.set(runId, r);
        setResult(r);
      })
      .catch((err: unknown) => setError(errorText(err)));
  }, [runId]);

  if (error) return <div className="banner banner-error">{error}</div>;
  if (!result) return <div className="node-meta">Loading results…</div>;
  return (
    <table className="data-table run-results">
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
  );
}
