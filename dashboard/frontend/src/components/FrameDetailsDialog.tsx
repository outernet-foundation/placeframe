import { useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { getReconstructionFrameDetail, reconstructionImageUrl } from "../api";
import { errorText } from "../storage";
import type { ReconstructionFrame, ReconstructionFrameDetail } from "../types";
import { Summary, useLoadedImage } from "./DetailsDialog";

// One reconstruction frame's images at full size with their keypoints drawn over them. A plain
// canvas for the same reason as the localization Details dialog: thousands of dots and no
// hit-testing. A spherical frame has one image per rendered view, a stereo rig one per camera;
// a row of buttons picks which is shown.

const CANVAS_HEIGHT = 560;

const KINDS = {
  triangulated: { colour: "#4ade80", label: "triangulated (has a 3D point)" },
  untriangulated: { colour: "#60a5fa", label: "no 3D point" },
} as const;
type Kind = keyof typeof KINDS;

export function FrameDetailsDialog({
  reconstructionId,
  frame,
  onClose,
}: {
  reconstructionId: string;
  frame: ReconstructionFrame;
  onClose: () => void;
}) {
  const [detail, setDetail] = useState<ReconstructionFrameDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState(0);
  const [shown, setShown] = useState<Record<Kind, boolean>>({ triangulated: true, untriangulated: true });
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    setDetail(null);
    setError(null);
    getReconstructionFrameDetail(reconstructionId, frame.index)
      .then(setDetail)
      .catch((e: unknown) => setError(errorText(e)));
  }, [reconstructionId, frame.index]);

  const current = detail?.images[selected] ?? null;
  const image = useLoadedImage(current ? reconstructionImageUrl(reconstructionId, current.name) : null);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");
    if (!canvas || !context) return;
    context.fillStyle = "#14161a";
    context.fillRect(0, 0, canvas.width, canvas.height);
    if (!current || !image) return;

    const scale = Math.min(canvas.width / image.width, canvas.height / image.height);
    const width = image.width * scale;
    const height = image.height * scale;
    const x0 = (canvas.width - width) / 2;
    const y0 = (canvas.height - height) / 2;
    context.drawImage(image, x0, y0, width, height);

    // Keypoints are in the size COLMAP recorded; the served image can be larger (a Zed frame is
    // stored at 1920x1080 and reconstructed at 1820x1024), always by a uniform scale.
    const sx = width / (current.width || image.width);
    const sy = height / (current.height || image.height);
    const points = current.keypoints;
    for (const kind of ["untriangulated", "triangulated"] as Kind[]) {
      if (!shown[kind]) continue;
      context.fillStyle = KINDS[kind].colour;
      context.beginPath();
      for (let i = 0; i < points.length; i += 3) {
        if ((points[i + 2] >= 0) !== (kind === "triangulated")) continue;
        const px = x0 + points[i] * sx;
        const py = y0 + points[i + 1] * sy;
        context.moveTo(px + 2, py);
        context.arc(px, py, 2, 0, Math.PI * 2);
      }
      context.fill();
    }
  }, [current, image, shown]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const fit = () => {
      if (canvas.width !== canvas.clientWidth || canvas.height !== CANVAS_HEIGHT) {
        canvas.width = canvas.clientWidth;
        canvas.height = CANVAS_HEIGHT;
      }
      draw();
    };
    const observer = new ResizeObserver(fit);
    observer.observe(canvas);
    fit();
    return () => observer.disconnect();
  }, [draw]);

  const counts = (keypoints: number[]) => {
    let triangulated = 0;
    for (let i = 2; i < keypoints.length; i += 3) if (keypoints[i] >= 0) triangulated++;
    return { total: keypoints.length / 3, triangulated };
  };
  const currentCounts = current ? counts(current.keypoints) : null;

  // Portalled to <body> for the same reason as the localization Details dialog: opened from a
  // table row, it would otherwise be laid out against the table rather than the viewport.
  return createPortal(
    <div className="dialog-overlay" onClick={onClose}>
      <div className="dialog dialog-wide" onClick={(e) => e.stopPropagation()}>
        <h3>
          Frame {frame.index} · <span className="mono">{frame.filename}</span>
        </h3>

        {error && <div className="banner banner-error">{error}</div>}
        {!detail && !error && <div className="node-meta">Loading keypoints and images… (up to half a minute the first time for a map)</div>}

        {detail && current && currentCounts && (
          <>
            <div className="detail-summary">
              <Summary label="Images in frame" value={String(detail.images.length)} />
              <Summary label="Frame observations" value={frame.observations.toLocaleString()} />
              <Summary
                label="Reprojection (mean)"
                value={frame.reprojection_error_mean != null ? `${frame.reprojection_error_mean.toFixed(2)} px` : "—"}
                hint="over the tracks of the points this frame sees"
              />
              <Summary
                label="This image"
                value={`${currentCounts.triangulated.toLocaleString()} / ${currentCounts.total.toLocaleString()}`}
                hint={`triangulated / keypoints · ${current.width}×${current.height}`}
              />
            </div>

            {detail.images.length > 1 && (
              <div className="frame-images">
                {detail.images.map((img, i) => (
                  <button key={img.name} className={i === selected ? "tab-active" : undefined} onClick={() => setSelected(i)}>
                    {img.name.split("/").slice(-2, -1)[0] ?? img.name}
                  </button>
                ))}
              </div>
            )}

            <canvas ref={canvasRef} className="detail-canvas" style={{ height: CANVAS_HEIGHT }} />
            {!image && <div className="node-meta">Loading image…</div>}

            <div className="detail-legend">
              {(Object.keys(KINDS) as Kind[]).map((kind) => (
                <label key={kind} className="detail-legend-item">
                  <input
                    type="checkbox"
                    checked={shown[kind]}
                    onChange={(e) => setShown((prev) => ({ ...prev, [kind]: e.target.checked }))}
                  />
                  <span className="detail-swatch" style={{ background: KINDS[kind].colour }} />
                  {KINDS[kind].label}
                </label>
              ))}
              <span className="mono node-meta">{current.name}</span>
            </div>
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
