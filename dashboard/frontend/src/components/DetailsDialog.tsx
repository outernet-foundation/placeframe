import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { getLocalizationDetail, localizationPairImageUrl, localizationQueryImageUrl } from "../api";
import { errorText } from "../storage";
import { MATCH_INLIER, MATCH_NO_POINT3D, MATCH_OUTLIER } from "../types";
import type { LocalizationDetail, LocalizationImage, PairDetail } from "../types";

// Why a plain 2D canvas rather than SVG or a library: the same reason AlignPage draws its
// top-down view by hand. A busy pair runs to ~500 correspondence lines, which is a lot of DOM
// nodes for something that never needs hit-testing, and the codebase has no drawing dependency.

const CANVAS_HEIGHT = 460;
const GUTTER = 8;

const STATUS_STYLE: Record<number, { colour: string; label: string }> = {
  [MATCH_INLIER]: { colour: "#4ade80", label: "inlier" },
  [MATCH_OUTLIER]: { colour: "#f87171", label: "outlier (RANSAC)" },
  [MATCH_NO_POINT3D]: { colour: "#60a5fa", label: "no 3D point" },
};

function useLoadedImage(url: string | null): HTMLImageElement | null {
  const [image, setImage] = useState<HTMLImageElement | null>(null);
  useEffect(() => {
    if (!url) {
      setImage(null);
      return;
    }
    const element = new Image();
    // The backend is a different origin (:8010) from this dev server, so without this the
    // canvas becomes tainted the moment an image is drawn and can never be read back or
    // exported. The backend already sends permissive CORS headers.
    element.crossOrigin = "anonymous";
    let cancelled = false;
    element.onload = () => {
      if (!cancelled) setImage(element);
    };
    element.onerror = () => {
      if (!cancelled) setImage(null);
    };
    element.src = url;
    return () => {
      cancelled = true;
    };
  }, [url]);
  return image;
}

function formatNumber(value: number | null, digits = 2): string {
  return value === null || Number.isNaN(value) ? "—" : value.toFixed(digits);
}

export function DetailsDialog({
  runId,
  image,
  onClose,
}: {
  runId: string;
  image: LocalizationImage;
  onClose: () => void;
}) {
  const [detail, setDetail] = useState<LocalizationDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selectedRank, setSelectedRank] = useState(0);
  const [shown, setShown] = useState<Record<number, boolean>>({
    [MATCH_INLIER]: true,
    [MATCH_OUTLIER]: false,
    [MATCH_NO_POINT3D]: false,
  });
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    getLocalizationDetail(runId, image.index)
      .then(setDetail)
      .catch((err: unknown) => setError(errorText(err)));
  }, [runId, image.index]);

  const pair: PairDetail | null = detail?.pairs[selectedRank] ?? null;
  const queryImage = useLoadedImage(localizationQueryImageUrl(runId, image.index));
  const pairImage = useLoadedImage(pair ? localizationPairImageUrl(runId, image.index, pair.rank) : null);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context || !detail) return;

    context.fillStyle = "#14161a";
    context.fillRect(0, 0, canvas.width, canvas.height);
    if (!queryImage || !pairImage || !pair) return;

    // Each pane gets half the canvas; the image is letterboxed into it.
    const paneWidth = (canvas.width - GUTTER) / 2;
    const fit = (source: HTMLImageElement, offsetX: number) => {
      const scale = Math.min(paneWidth / source.width, canvas.height / source.height);
      const width = source.width * scale;
      const height = source.height * scale;
      return { x: offsetX + (paneWidth - width) / 2, y: (canvas.height - height) / 2, width, height, scale };
    };
    const left = fit(queryImage, 0);
    const right = fit(pairImage, paneWidth + GUTTER);

    context.drawImage(queryImage, left.x, left.y, left.width, left.height);
    context.drawImage(pairImage, right.x, right.y, right.width, right.height);

    // Keypoints live in the frame the pipeline canonicalized to (short side 1024), not in the
    // frame of the pixels being displayed. Mapping through the reported intrinsics rather than
    // the loaded image's natural size is what keeps the dots on the features.
    const queryScale = left.width / detail.camera.width;
    const databaseScale = right.width / pair.width;

    const order = [MATCH_NO_POINT3D, MATCH_OUTLIER, MATCH_INLIER];
    for (const status of order) {
      if (!shown[status]) continue;
      context.strokeStyle = STATUS_STYLE[status].colour;
      context.fillStyle = STATUS_STYLE[status].colour;
      context.lineWidth = 1;
      context.globalAlpha = status === MATCH_INLIER ? 0.75 : 0.45;
      for (let i = 0; i < pair.status.length; i += 1) {
        if (pair.status[i] !== status) continue;
        const qx = left.x + pair.query_xy[i][0] * queryScale;
        const qy = left.y + pair.query_xy[i][1] * queryScale;
        const dx = right.x + pair.database_xy[i][0] * databaseScale;
        const dy = right.y + pair.database_xy[i][1] * databaseScale;
        context.beginPath();
        context.moveTo(qx, qy);
        context.lineTo(dx, dy);
        context.stroke();
        context.beginPath();
        context.arc(qx, qy, 1.6, 0, Math.PI * 2);
        context.fill();
        context.beginPath();
        context.arc(dx, dy, 1.6, 0, Math.PI * 2);
        context.fill();
      }
    }
    context.globalAlpha = 1;

    context.fillStyle = "#e6e6e6";
    context.font = "12px system-ui, sans-serif";
    context.fillText("query", left.x + 4, 14);
    context.fillText(pair.name, right.x + 4, 14);
  }, [detail, pair, pairImage, queryImage, shown]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const resize = () => {
      // Only resize when it actually changed: assigning to canvas.width clears the canvas, so
      // doing it unconditionally on every draw would fight the draw itself.
      if (canvas.width !== canvas.clientWidth || canvas.height !== CANVAS_HEIGHT) {
        canvas.width = canvas.clientWidth;
        canvas.height = CANVAS_HEIGHT;
      }
      draw();
    };
    resize();
    // A ResizeObserver rather than window.resize: this canvas sits inside a dialog whose width
    // is settled by layout after mount, so the window never resizes but the canvas does. Without
    // this the backing store stays at its first-measured width and the drawing comes out
    // stretched across the real one.
    const observer = new ResizeObserver(resize);
    observer.observe(canvas);
    return () => observer.disconnect();
  }, [draw]);

  useEffect(draw, [draw]);

  const counts = useMemo(() => {
    if (!pair) return null;
    return {
      [MATCH_INLIER]: pair.num_inliers,
      [MATCH_OUTLIER]: pair.num_correspondences - pair.num_inliers,
      [MATCH_NO_POINT3D]: pair.num_matches - pair.num_correspondences,
    } as Record<number, number>;
  }, [pair]);

  // Portalled to <body> rather than rendered where it is used. This dialog is opened from a row
  // inside the results table, and an overlay rendered there is laid out against its ancestors
  // instead of the viewport -- which pinned it to the table's width (~420px) no matter what
  // `.dialog-wide` asked for. Every other dialog in this app is mounted at page level and never
  // hit this; portalling keeps the component self-contained without that constraint.
  return createPortal(
    <div className="dialog-overlay" onClick={onClose}>
      <div className="dialog dialog-wide" onClick={(e) => e.stopPropagation()}>
        <h3>
          Image {image.index} · <span className="mono">{image.filename}</span>
        </h3>

        {error && <div className="banner banner-error">{error}</div>}
        {!detail && !error && <div className="node-meta">Loading detail…</div>}

        {detail && (
          <>
            {detail.failure_reason && (
              <div className="banner banner-error">Localization failed: {detail.failure_reason}</div>
            )}

            <div className="detail-summary">
              <Summary label="Query keypoints" value={detail.num_query_keypoints.toLocaleString()} />
              <Summary label="Retrieved" value={`top ${detail.retrieval_top_k}`} />
              <Summary label="RANSAC threshold" value={`${detail.ransac_threshold} px`} />
              <Summary
                label="Intrinsics used"
                value={`${detail.camera.width}×${detail.camera.height} · f=${detail.camera.fx.toFixed(0)} px`}
                hint={`${((2 * Math.atan(detail.camera.width / 2 / detail.camera.fx) * 180) / Math.PI).toFixed(1)}° horizontal`}
              />
              {detail.metrics && (
                <>
                  <Summary
                    label="Inliers"
                    value={`${detail.metrics.num_inliers} / ${detail.metrics.num_correspondences}`}
                    hint={`${(detail.metrics.inlier_ratio * 100).toFixed(1)}% · ${detail.metrics.num_matches} raw matches`}
                  />
                  <Summary
                    label="Reprojection (median)"
                    value={`${detail.metrics.reprojection_error_median.toFixed(2)} px`}
                  />
                  <Summary
                    label="Inlier coverage"
                    value={`${(detail.metrics.inlier_coverage * 100).toFixed(1)}%`}
                    hint="spread of inliers across the frame"
                  />
                </>
              )}
              {detail.gate && detail.metrics && (
                <Summary
                  label="Confidence gate"
                  value={detail.gate.passed ? "passed" : "REJECTED"}
                  hint={`loose ${detail.metrics.confidence_loose.toFixed(3)} / min ${detail.gate.loose_min} · tight ${detail.metrics.confidence_tight.toFixed(3)} / min ${detail.gate.tight_min}`}
                />
              )}
              <Summary
                label="Time"
                value={`${(detail.timings_ms.total ?? 0).toFixed(0)} ms`}
                hint={Object.entries(detail.timings_ms)
                  .filter(([stage]) => stage !== "total")
                  .map(([stage, ms]) => `${stage} ${ms.toFixed(0)}`)
                  .join(" · ")}
              />
            </div>

            <canvas ref={canvasRef} className="detail-canvas" style={{ height: CANVAS_HEIGHT }} />

            <div className="detail-legend">
              {[MATCH_INLIER, MATCH_OUTLIER, MATCH_NO_POINT3D].map((status) => (
                <label key={status} className="detail-legend-item">
                  <input
                    type="checkbox"
                    checked={shown[status]}
                    onChange={(e) => setShown((prev) => ({ ...prev, [status]: e.target.checked }))}
                  />
                  <span className="detail-swatch" style={{ background: STATUS_STYLE[status].colour }} />
                  {STATUS_STYLE[status].label}
                  {counts && ` (${counts[status]})`}
                </label>
              ))}
            </div>

            <table className="data-table detail-pairs">
              <thead>
                <tr>
                  <th>#</th>
                  <th>Database image</th>
                  <th>Score</th>
                  <th>Matches</th>
                  <th>2D-3D</th>
                  <th>Inliers</th>
                  <th>Ratio</th>
                  <th>Reproj</th>
                  <th>Dist</th>
                  <th>Angle</th>
                </tr>
              </thead>
              <tbody>
                {detail.pairs.map((row) => (
                  <tr
                    key={row.rank}
                    onClick={() => setSelectedRank(row.rank)}
                    className={row.rank === selectedRank ? "selected" : undefined}
                    style={{ cursor: "pointer" }}
                  >
                    <td>{row.rank}</td>
                    <td className="mono">{row.name}</td>
                    <td>{row.retrieval_score.toFixed(3)}</td>
                    <td>{row.num_matches}</td>
                    <td>{row.num_correspondences}</td>
                    <td>{row.num_inliers}</td>
                    <td>{(row.inlier_ratio * 100).toFixed(1)}%</td>
                    <td>{formatNumber(row.reprojection_error_median)}</td>
                    <td>{formatNumber(row.distance_m, 1)}</td>
                    <td>{formatNumber(row.view_angle_deg, 0)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}

        <div className="dialog-actions">
          <button onClick={onClose}>Close</button>
        </div>
      </div>
    </div>,
    document.body,
  );
}

function Summary({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="detail-summary-item">
      <div className="detail-summary-label">{label}</div>
      <div className="detail-summary-value">{value}</div>
      {hint && <div className="detail-summary-hint">{hint}</div>}
    </div>
  );
}
