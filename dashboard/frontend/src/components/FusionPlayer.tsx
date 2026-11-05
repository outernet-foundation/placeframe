import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { fusionFrameUrl, getFusionRun } from "../api";
import { errorText } from "../storage";
import type { FusionRequest, FusionRequestStatus, FusionResult } from "../types";

// An offline fusion run's rendered frames as a video: play, scrub with the slider, or step with the
// arrow keys. Ticks under the slider mark each VPS request (where its still was taken) and where its
// fix landed, coloured by what the filter made of it.

const STATUS_COLOR: Record<FusionRequestStatus, string> = {
  accepted: "#4ade80",
  rejected: "#f87171",
  failed: "#9ca3af",
  not_applied: "#6b7280",
};

// Frames fetched ahead of the playhead so playback doesn't stall on the network.
const PRELOAD_AHEAD = 45;

export function FusionPlayer({ runId, onClose }: { runId: string; onClose: () => void }) {
  const [run, setRun] = useState<FusionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const loaded = useRef(new Map<number, HTMLImageElement>());

  useEffect(() => {
    getFusionRun(runId)
      .then(setRun)
      .catch((err: unknown) => setError(errorText(err)));
  }, [runId]);

  const count = run?.frame_count ?? 0;

  const preload = useCallback(
    (from: number) => {
      for (let i = from; i < Math.min(count, from + PRELOAD_AHEAD); i++) {
        if (loaded.current.has(i)) continue;
        const image = new Image();
        image.src = fusionFrameUrl(runId, i);
        loaded.current.set(i, image);
      }
    },
    [count, runId],
  );

  useEffect(() => preload(index), [index, preload]);

  // Playback follows the frames' own timestamps, so dropped frames play at their real spacing.
  useEffect(() => {
    if (!playing || !run) return;
    const startIndex = index;
    const startT = run.frames[startIndex].t;
    const startWall = performance.now();
    let handle = 0;
    const step = () => {
      const target = startT + (performance.now() - startWall) / 1000;
      let next = startIndex;
      while (next + 1 < run.frames.length && run.frames[next + 1].t <= target) next++;
      const image = loaded.current.get(next);
      if (image && !image.complete) {
        handle = requestAnimationFrame(step);
        return;
      }
      setIndex(next);
      if (next >= run.frames.length - 1) {
        setPlaying(false);
        return;
      }
      handle = requestAnimationFrame(step);
    };
    handle = requestAnimationFrame(step);
    return () => cancelAnimationFrame(handle);
    // Restart only when play is toggled; the playhead itself is what this effect moves.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [playing, run]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "ArrowRight" || event.key === "ArrowLeft") {
        event.preventDefault();
        setPlaying(false);
        const delta = (event.key === "ArrowRight" ? 1 : -1) * (event.shiftKey ? 10 : 1);
        setIndex((i) => Math.max(0, Math.min(count - 1, i + delta)));
      } else if (event.key === " ") {
        event.preventDefault();
        setPlaying((p) => !p);
      } else if (event.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [count, onClose]);

  const frame = run?.frames[index];
  const lastApplied = useMemo(() => {
    if (!run) return null;
    for (let i = index; i >= 0; i--) {
      const applied = run.frames[i].vps_applied;
      if (applied.length > 0) return run.requests[applied[applied.length - 1]];
    }
    return null;
  }, [run, index]);

  return createPortal(
    <div className="dialog-overlay fusion-overlay" onClick={onClose}>
      <div className="fusion-player" onClick={(e) => e.stopPropagation()}>
        {error && <div className="banner banner-error">{error}</div>}
        {!run && !error && <div className="node-count">Loading…</div>}
        {run && frame && (
          <>
            <div className="fusion-stage">
              <img className="fusion-frame" src={fusionFrameUrl(runId, index)} alt={`Frame ${index}`} />
              <div className="fusion-side">
                <h3>Offline fusion</h3>
                <div className="node-count mono">{run.recording.slice(0, 8)} · {run.run_id.slice(0, 8)}</div>
                <dl className="fusion-facts">
                  <dt>Frame</dt>
                  <dd>
                    {index + 1} / {count}
                  </dd>
                  <dt>Time</dt>
                  <dd>{frame.t.toFixed(3)} s</dd>
                  <dt>Tracking</dt>
                  <dd>{frame.tracking_state}</dd>
                  <dt>Fix</dt>
                  <dd>
                    {frame.has_fix
                      ? `σ ${(frame.sigma_translation_m * 100).toFixed(1)} cm / ${frame.sigma_rotation_deg.toFixed(2)}°${frame.slewing ? " · slewing" : ""}`
                      : "none yet"}
                  </dd>
                  <dt>Correction</dt>
                  <dd title="How far this frame's change in the alignment moved the camera in the map, with its own motion taken out">
                    {frame.correction_m == null ? "—" : `${(frame.correction_m * 100).toFixed(1)} cm this frame`}
                  </dd>
                  <dt>Last VPS</dt>
                  <dd>{lastApplied ? requestSummary(lastApplied, frame.t) : "—"}</dd>
                </dl>
                <div className="node-count">
                  {run.requests.filter((r) => r.status === "accepted").length} accepted ·{" "}
                  {run.requests.filter((r) => r.status === "rejected").length} rejected ·{" "}
                  {run.requests.filter((r) => r.status === "failed").length} failed of {run.requests.length} requests
                </div>
                <div className="node-count">
                  VPS every {run.params.vps.interval_s} s, {run.params.vps.latency_s} s latency · gate χ² {run.params.fusion.gate_chi2} ·
                  slew {run.params.fusion.slew_s} s
                  {run.params.fusion.bypass_gate ? " · gate bypassed" : ""}
                  {run.params.fusion.bypass_kalman ? " · Kalman bypassed" : ""}
                </div>
                <div className="node-count">
                  Green dots: map points where the fused pose puts them. Yellow circles: features VPS matched, on the frame it
                  localized. ←/→ step (Shift ×10), Space plays.
                </div>
              </div>
            </div>
            <div className="fusion-controls">
              <button onClick={() => setPlaying((p) => !p)}>{playing ? "Pause" : "Play"}</button>
              <div className="fusion-track">
                <input
                  type="range"
                  min={0}
                  max={count - 1}
                  value={index}
                  onChange={(e) => {
                    setPlaying(false);
                    setIndex(Number(e.target.value));
                  }}
                />
                <div className="fusion-ticks">
                  {run.requests.map((request) => (
                    <RequestTicks key={request.index} request={request} run={run} onSeek={setIndex} />
                  ))}
                </div>
              </div>
              <button onClick={onClose}>Close</button>
            </div>
          </>
        )}
      </div>
    </div>,
    document.body,
  );
}

function requestSummary(request: FusionRequest, now: number): string {
  const ago = `${(now - request.apply_s).toFixed(1)} s ago`;
  if (request.status === "failed") return `#${request.index + 1} failed (${request.error ?? "no result"}), ${ago}`;
  const how = request.snapped ? ", snapped" : "";
  return `#${request.index + 1} ${request.status}${how}, m² ${request.mahalanobis_sq?.toFixed(2) ?? "—"}, ${request.num_inliers ?? "—"} inliers, ${ago}`;
}

// A request's still (hollow) and where its fix landed (filled), joined by a line: the latency.
function RequestTicks({ request, run, onSeek }: { request: FusionRequest; run: FusionResult; onSeek: (index: number) => void }) {
  const last = run.frames.length - 1;
  const applyFrame = run.frames.findIndex((f) => f.vps_applied.includes(request.index));
  const at = (frameIndex: number) => `${(frameIndex / Math.max(1, last)) * 100}%`;
  const color = STATUS_COLOR[request.status];
  return (
    <>
      <span
        className="fusion-tick fusion-tick-request"
        style={{ left: at(request.request_frame), borderColor: color }}
        title={`VPS #${request.index + 1} still at ${run.frames[request.request_frame].t.toFixed(2)} s`}
        onClick={() => onSeek(request.request_frame)}
      />
      {applyFrame >= 0 && (
        <>
          <span
            className="fusion-tick-span"
            style={{ left: at(request.request_frame), width: `calc(${at(applyFrame)} - ${at(request.request_frame)})`, background: color }}
          />
          <span
            className="fusion-tick fusion-tick-apply"
            style={{ left: at(applyFrame), background: color }}
            title={`VPS #${request.index + 1} ${request.status}${request.mahalanobis_sq != null ? `, m² ${request.mahalanobis_sq.toFixed(2)}` : ""}`}
            onClick={() => onSeek(applyFrame)}
          />
        </>
      )}
    </>
  );
}
