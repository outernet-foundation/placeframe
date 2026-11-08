import { useEffect, useRef, useState } from "react";
import { getReconstructionFrames, reconstructionFrameImageUrl } from "../api";
import { errorText } from "../storage";
import type { ReconstructionFrame, ReconstructionFrames as Frames } from "../types";
import { FrameDetailsDialog } from "./FrameDetailsDialog";
import { CHART_BLUE, CHART_ORANGE, SummaryCharts, type ChartSpec } from "./RunCharts";

// A reconstruction's registered frames: summary charts by frame number, then one frame at a time
// with its thumbnail and pose, picked with a slider (or by clicking a chart) and opened in full
// with Details. The listing is built server-side on first request and cached there; here it is
// fetched once per page.
const cache = new Map<string, Frames>();

// Previews fetched either side of the frame on show, so stepping or a short drag doesn't wait on
// the network.
const PRELOAD_AROUND = 8;

export function ReconstructionFrames({ reconstructionId }: { reconstructionId: string }) {
  const [result, setResult] = useState<Frames | null>(cache.get(reconstructionId) ?? null);
  const [error, setError] = useState<string | null>(null);
  const [inspecting, setInspecting] = useState<ReconstructionFrame | null>(null);
  // The slot (position in `frames`) on show, not the frame's own index.
  const [selected, setSelected] = useState(0);
  const preloaded = useRef(new Map<number, HTMLImageElement>());

  useEffect(() => {
    if (!result) return;
    const { frames } = result;
    for (let slot = Math.max(0, selected - PRELOAD_AROUND); slot <= Math.min(frames.length - 1, selected + PRELOAD_AROUND); slot++) {
      const frame = frames[slot];
      if (!frame.thumbnail_base64 || preloaded.current.has(frame.index)) continue;
      const image = new Image();
      image.src = reconstructionFrameImageUrl(reconstructionId, frame.index);
      preloaded.current.set(frame.index, image);
    }
  }, [result, selected, reconstructionId]);

  useEffect(() => {
    if (cache.has(reconstructionId)) return;
    getReconstructionFrames(reconstructionId)
      .then((r) => {
        cache.set(reconstructionId, r);
        setResult(r);
      })
      .catch((err: unknown) => setError(errorText(err)));
  }, [reconstructionId]);

  if (error) return <div className="banner banner-error">{error}</div>;
  if (!result) return <div className="node-meta">Loading frames… (the first time can take up to a minute for a large map)</div>;

  const { frames } = result;
  if (frames.length === 0) return <div className="node-empty">No registered frames.</div>;

  const metres = (value: number) => `${value.toFixed(3)} m`;
  const position = (axis: "x" | "y" | "z") => frames.map((f) => f.position[axis]);
  const charts: ChartSpec[] = [
    {
      title: "Observations and reprojection error",
      series: [
        {
          label: "Observations",
          colour: CHART_BLUE,
          values: frames.map((f) => f.observations),
          format: (value) => value.toFixed(0),
          axis: "left",
          axisTitle: "Observations",
        },
        {
          label: "Reproj error",
          colour: CHART_ORANGE,
          values: frames.map((f) => f.reprojection_error_mean),
          format: (value) => `${value.toFixed(2)} px`,
          axis: "right",
          axisTitle: "Reproj (px)",
        },
      ],
    },
    { title: "X", series: [{ label: "X", colour: CHART_BLUE, values: position("x"), format: metres, axis: "left" }] },
    { title: "Y", series: [{ label: "Y", colour: CHART_BLUE, values: position("y"), format: metres, axis: "left" }] },
    { title: "Z", series: [{ label: "Z", colour: CHART_BLUE, values: position("z"), format: metres, axis: "left" }] },
  ];

  const slot = Math.min(selected, frames.length - 1);
  const frame = frames[slot];
  const seek = (next: number) => setSelected(Math.max(0, Math.min(frames.length - 1, next)));

  return (
    <>
      <SummaryCharts
        charts={charts}
        indices={frames.map((f) => f.index)}
        failed={frames.map(() => false)}
        selected={slot}
        onSelect={seek}
      />
      <div className="frame-scrubber">
        <div className="frame-scrubber-stage">
          {frame.thumbnail_base64 ? (
            // One element across frames, so the browser holds the last preview until the next has
            // loaded rather than collapsing the box; the previews around this frame are preloaded,
            // so that wait is rarely seen. The thumbnail behind it covers the very first load.
            <img
              className="frame-scrubber-image"
              src={reconstructionFrameImageUrl(reconstructionId, frame.index)}
              alt={frame.filename}
              style={{ backgroundImage: `url(${frame.thumbnail_base64})` }}
            />
          ) : (
            <div className="frame-scrubber-image frame-scrubber-missing">No image</div>
          )}
          <div className="fusion-side">
            <dl className="fusion-facts">
              <dt>Frame</dt>
              <dd>
                {frame.index} ({slot + 1} / {frames.length})
              </dd>
              <dt>Filename</dt>
              <dd className="mono">{frame.filename}</dd>
              <dt title="Registered images in this frame: rendered views of a spherical frame, or a rig's cameras">Images</dt>
              <dd>{frame.image_count}</dd>
              <dt title="2D keypoints in this frame's images that belong to a triangulated 3D point">Observations</dt>
              <dd>{frame.observations.toLocaleString()}</dd>
              <dt title="Mean reprojection error of the 3D points this frame observes (each point's track error)">Reproj</dt>
              <dd>{frame.reprojection_error_mean != null ? `${frame.reprojection_error_mean.toFixed(2)} px` : "—"}</dd>
              <dt>Position</dt>
              <dd>
                {frame.position.x.toFixed(3)}, {frame.position.y.toFixed(3)}, {frame.position.z.toFixed(3)} m
              </dd>
              <dt>Roll / pitch / yaw</dt>
              <dd>
                {frame.rpy_deg.roll.toFixed(1)}°, {frame.rpy_deg.pitch.toFixed(1)}°, {frame.rpy_deg.yaw.toFixed(1)}°
              </dd>
            </dl>
            <div>
              <button onClick={() => setInspecting(frame)}>Details…</button>
            </div>
          </div>
        </div>
        <div className="fusion-controls">
          <button onClick={() => seek(slot - 1)} disabled={slot === 0} title="Previous frame">
            ‹
          </button>
          <div className="fusion-track">
            <input
              type="range"
              min={0}
              max={frames.length - 1}
              value={slot}
              onChange={(e) => seek(Number(e.target.value))}
              aria-label="Frame"
            />
          </div>
          <button onClick={() => seek(slot + 1)} disabled={slot === frames.length - 1} title="Next frame">
            ›
          </button>
        </div>
      </div>
      {inspecting && (
        <FrameDetailsDialog reconstructionId={reconstructionId} frame={inspecting} onClose={() => setInspecting(null)} />
      )}
    </>
  );
}
