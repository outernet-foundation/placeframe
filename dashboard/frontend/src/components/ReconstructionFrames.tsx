import { useEffect, useState } from "react";
import { getReconstructionFrames } from "../api";
import { errorText } from "../storage";
import type { ReconstructionFrame, ReconstructionFrames as Frames } from "../types";
import { FrameDetailsDialog } from "./FrameDetailsDialog";
import { CHART_BLUE, CHART_ORANGE, SummaryCharts, type ChartSpec } from "./RunCharts";

// A reconstruction's registered frames shown the way a localization run's images are: summary
// charts by frame number, then one row per frame with its thumbnail and pose. The listing is
// built server-side on first request and cached there; here it is fetched once per page.
const cache = new Map<string, Frames>();

export function ReconstructionFrames({ reconstructionId }: { reconstructionId: string }) {
  const [result, setResult] = useState<Frames | null>(cache.get(reconstructionId) ?? null);
  const [error, setError] = useState<string | null>(null);
  const [inspecting, setInspecting] = useState<ReconstructionFrame | null>(null);

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

  return (
    <>
      <SummaryCharts charts={charts} indices={frames.map((f) => f.index)} failed={frames.map(() => false)} />
      <table className="data-table run-results">
        <thead>
          <tr>
            <th>#</th>
            <th>Thumbnail</th>
            <th>Filename</th>
            <th title="Registered images in this frame: rendered views of a spherical frame, or a rig's cameras">Images</th>
            <th title="2D keypoints in this frame's images that belong to a triangulated 3D point">Observations</th>
            <th title="Mean reprojection error of the 3D points this frame observes (each point's track error)">Reproj</th>
            <th>X</th>
            <th>Y</th>
            <th>Z</th>
            <th>Roll</th>
            <th>Pitch</th>
            <th>Yaw</th>
            <th />
          </tr>
        </thead>
        <tbody>
          {frames.map((f) => (
            <tr key={f.index}>
              <td>{f.index}</td>
              <td>
                {f.thumbnail_base64 ? (
                  <img src={f.thumbnail_base64} alt={f.filename} loading="lazy" style={{ width: 96, borderRadius: 4 }} />
                ) : (
                  "—"
                )}
              </td>
              <td className="mono">{f.filename}</td>
              <td>{f.image_count}</td>
              <td>{f.observations.toLocaleString()}</td>
              <td>{f.reprojection_error_mean != null ? f.reprojection_error_mean.toFixed(2) : "—"}</td>
              <td>{f.position.x.toFixed(3)}</td>
              <td>{f.position.y.toFixed(3)}</td>
              <td>{f.position.z.toFixed(3)}</td>
              <td>{f.rpy_deg.roll.toFixed(1)}</td>
              <td>{f.rpy_deg.pitch.toFixed(1)}</td>
              <td>{f.rpy_deg.yaw.toFixed(1)}</td>
              <td>
                <button onClick={() => setInspecting(f)}>Details…</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {inspecting && (
        <FrameDetailsDialog reconstructionId={reconstructionId} frame={inspecting} onClose={() => setInspecting(null)} />
      )}
    </>
  );
}
