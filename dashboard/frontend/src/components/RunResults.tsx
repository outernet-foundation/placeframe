import { useEffect, useState } from "react";
import { getLocalization } from "../api";
import { errorText } from "../storage";
import type { LocalizationImage, LocalizationResult } from "../types";
import { DetailsDialog } from "./DetailsDialog";

// A localization run's per-image table (thumbnail, status, pose, match quality), shown inline
// under the run. results.json is fetched once per run and cached for the page's lifetime.
const cache = new Map<string, LocalizationResult>();

export function RunResults({ runId }: { runId: string }) {
  const [result, setResult] = useState<LocalizationResult | null>(cache.get(runId) ?? null);
  const [error, setError] = useState<string | null>(null);
  const [inspecting, setInspecting] = useState<LocalizationImage | null>(null);

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

  // Runs localized before --detail existed have nothing to inspect; the column is dropped
  // entirely rather than showing a row of dead buttons.
  const anyDetail = result.images.some((img) => img.has_detail);

  return (
    <>
      {!anyDetail && (
        <div className="node-meta">
          No per-image diagnostics in this run — re-run the localization with Detail enabled to inspect
          feature matches.
        </div>
      )}
      <table className="data-table run-results">
        <thead>
          <tr>
            <th>#</th>
            <th>Thumbnail</th>
            <th>Filename</th>
            <th>Status</th>
            <th>Inliers</th>
            <th>Ratio</th>
            <th>Reproj</th>
            <th>X</th>
            <th>Y</th>
            <th>Z</th>
            <th>Roll</th>
            <th>Pitch</th>
            <th>Yaw</th>
            {anyDetail && <th />}
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
              <td>{img.metrics ? `${img.metrics.num_inliers}/${img.metrics.num_correspondences}` : "—"}</td>
              <td>{img.metrics ? `${(img.metrics.inlier_ratio * 100).toFixed(1)}%` : "—"}</td>
              <td>{img.metrics ? img.metrics.reprojection_error_median.toFixed(2) : "—"}</td>
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
              {anyDetail && (
                <td>
                  {img.has_detail && <button onClick={() => setInspecting(img)}>Details…</button>}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
      {inspecting && (
        <DetailsDialog runId={runId} image={inspecting} onClose={() => setInspecting(null)} />
      )}
    </>
  );
}
