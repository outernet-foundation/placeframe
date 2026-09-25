import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { fetchPoints, listReconstructions, saveAlignment, type AlignedMap, type PointCloud } from "../api";
import { errorText } from "../storage";
import type { Reconstruction } from "../types";
import "./align.css";

// Seen from above (X right, Z up the screen), which is the only view the placement needs: every
// map arrives gravity-aligned, so the free parameters are yaw about the up axis and translation.
// Height is perpendicular to this view and so cannot be dragged — it is typed instead, and for
// captures of one site it is usually already near zero.
//
// Deliberately a 2D canvas rather than the three.js viewer next door: with no camera to raycast
// through, a drag is a subtraction, and a few hundred thousand points draw as points.

// Shared with the 3D viewer's CAPTURE_COLORS so a map keeps its colour between the two, and used
// for a map's points and its poses alike — the whole point being to tell the maps apart at a
// glance, not the points from the poses.
const MAP_COLORS = ["#ff9500", "#4fc3f7", "#aed581", "#ba68c8", "#ffd54f", "#f06292"];

// Points are drawn every frame while dragging, so the cloud is thinned once on load rather than
// per frame. Poses are never thinned: there are a few hundred and they are what you aim with.
const MAX_POINTS_DRAWN = 60_000;

interface MapState {
  id: string;
  label: string;
  color: string;
  cloud: PointCloud | null;
  error: string | null;
  showPoints: boolean;
  showPoses: boolean;
  pointSize: number;
  yawDeg: number;
  tx: number;
  ty: number;
  tz: number;
  scale: number;
  // A stereo baseline already fixes metric scale, so scale is locked unless the map has no metric
  // anchor of its own. A free scale on a metric map can only move it away from correct.
  scaleLocked: boolean;
}

function place(m: MapState, x: number, z: number): [number, number] {
  const a = (m.yawDeg * Math.PI) / 180;
  const sx = m.scale * x;
  const sz = m.scale * z;
  return [sx * Math.cos(a) + sz * Math.sin(a) + m.tx, -sx * Math.sin(a) + sz * Math.cos(a) + m.tz];
}

function thin(positions: Float32Array, count: number): Float32Array {
  if (count <= MAX_POINTS_DRAWN) return positions;
  const step = Math.ceil(count / MAX_POINTS_DRAWN);
  const kept = new Float32Array(Math.ceil(count / step) * 3);
  let k = 0;
  for (let i = 0; i < count; i += step) {
    kept[k++] = positions[i * 3];
    kept[k++] = positions[i * 3 + 1];
    kept[k++] = positions[i * 3 + 2];
  }
  return kept.subarray(0, k);
}

export function AlignPage() {
  const [available, setAvailable] = useState<Reconstruction[]>([]);
  const [maps, setMaps] = useState<MapState[]>([]);
  const [referenceId, setReferenceId] = useState<string>("");
  const [status, setStatus] = useState<string | null>(null);
  const [saved, setSaved] = useState<string | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const thinned = useRef<Map<string, Float32Array>>(new Map());
  const view = useRef({ scale: 4, ox: 0, oz: 0 });
  const drag = useRef<{ id: string | null; mode: "move" | "rotate" | "pan"; x: number; y: number } | null>(null);

  useEffect(() => {
    listReconstructions()
      .then((all) => setAvailable(all.filter((r) => r.status === "succeeded")))
      .catch((err: unknown) => setStatus(errorText(err)));
  }, []);

  const addMap = useCallback(
    (r: Reconstruction) => {
      if (maps.some((m) => m.id === r.id)) return;
      const color = MAP_COLORS[maps.length % MAP_COLORS.length];
      const label = r.capture_name ?? r.id.slice(0, 8);
      setMaps((prev) => [
        ...prev,
        {
          id: r.id, label, color, cloud: null, error: null,
          showPoints: true, showPoses: true, pointSize: 1,
          yawDeg: 0, tx: 0, ty: 0, tz: 0, scale: 1,
          // A stereo baseline fixes metric scale, and so does a position prior that bundle
          // adjustment actually used. A poseless capture has neither -- its trajectory is
          // synthetic and the prior deliberately neutralised -- so only that case is scale-free.
          scaleLocked: r.is_stereo === true || priorSigma(r) < 100,
        },
      ]);
      if (!referenceId) setReferenceId(r.id);
      fetchPoints(r.id)
        .then((cloud) => {
          thinned.current.set(r.id, thin(cloud.positions, cloud.count));
          setMaps((prev) => prev.map((m) => (m.id === r.id ? { ...m, cloud } : m)));
        })
        .catch((err: unknown) =>
          setMaps((prev) => prev.map((m) => (m.id === r.id ? { ...m, error: errorText(err) } : m))),
        );
    },
    [maps, referenceId],
  );

  const update = (id: string, patch: Partial<MapState>) =>
    setMaps((prev) => prev.map((m) => (m.id === id ? { ...m, ...patch } : m)));

  // How many of the other maps' poses land near this one's, at the current placement. The point of
  // aligning coarsely is that something downstream can pair frames by proximity, so the number
  // that matters is how many pairs that would actually find — not whether the overlay looks right.
  const neighbourCounts = useMemo(() => {
    const out = new Map<string, number>();
    const ref = maps.find((m) => m.id === referenceId);
    if (!ref?.cloud) return out;
    const refPoses: [number, number][] = [];
    for (let i = 0; i < ref.cloud.poseCount; i++) {
      refPoses.push(place(ref, ref.cloud.posePositions[i * 3], ref.cloud.posePositions[i * 3 + 2]));
    }
    for (const m of maps) {
      if (m.id === referenceId || !m.cloud) continue;
      let near = 0;
      for (let i = 0; i < m.cloud.poseCount; i++) {
        const [x, z] = place(m, m.cloud.posePositions[i * 3], m.cloud.posePositions[i * 3 + 2]);
        if (refPoses.some((p) => (p[0] - x) ** 2 + (p[1] - z) ** 2 < 100)) near++;
      }
      out.set(m.id, near);
    }
    return out;
  }, [maps, referenceId]);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const { width, height } = canvas;
    ctx.fillStyle = "#12161c";
    ctx.fillRect(0, 0, width, height);
    const { scale, ox, oz } = view.current;
    const toScreen = (x: number, z: number): [number, number] => [
      width / 2 + (x - ox) * scale,
      height / 2 - (z - oz) * scale,
    ];

    for (const m of maps) {
      if (!m.cloud) continue;
      if (m.showPoints) {
        const pts = thinned.current.get(m.id);
        if (pts) {
          ctx.fillStyle = m.color;
          ctx.globalAlpha = 0.5;
          for (let i = 0; i < pts.length; i += 3) {
            const [wx, wz] = place(m, pts[i], pts[i + 2]);
            const [sx, sy] = toScreen(wx, wz);
            if (sx < 0 || sy < 0 || sx > width || sy > height) continue;
            ctx.fillRect(sx, sy, m.pointSize, m.pointSize);
          }
          ctx.globalAlpha = 1;
        }
      }
      if (m.showPoses) {
        ctx.strokeStyle = m.color;
        ctx.lineWidth = 2;
        ctx.beginPath();
        for (let i = 0; i < m.cloud.poseCount; i++) {
          const [wx, wz] = place(m, m.cloud.posePositions[i * 3], m.cloud.posePositions[i * 3 + 2]);
          const [sx, sy] = toScreen(wx, wz);
          if (i === 0) ctx.moveTo(sx, sy);
          else ctx.lineTo(sx, sy);
        }
        ctx.stroke();
      }
    }
  }, [maps]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const resize = () => {
      canvas.width = canvas.clientWidth;
      canvas.height = canvas.clientHeight;
      draw();
    };
    resize();
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, [draw]);

  useEffect(draw, [draw]);

  const onPointerDown = (e: React.PointerEvent<HTMLCanvasElement>) => {
    const selected = maps.find((m) => m.id !== referenceId && m.id === selectedId);
    const mode = e.button === 1 || e.shiftKey ? "pan" : e.altKey ? "rotate" : "move";
    drag.current = { id: selected?.id ?? null, mode, x: e.clientX, y: e.clientY };
    (e.target as HTMLCanvasElement).setPointerCapture(e.pointerId);
  };

  const onPointerMove = (e: React.PointerEvent<HTMLCanvasElement>) => {
    const d = drag.current;
    if (!d) return;
    const dx = e.clientX - d.x;
    const dy = e.clientY - d.y;
    d.x = e.clientX;
    d.y = e.clientY;
    if (d.mode === "pan" || !d.id) {
      view.current.ox -= dx / view.current.scale;
      view.current.oz += dy / view.current.scale;
      draw();
      return;
    }
    const m = maps.find((x) => x.id === d.id);
    if (!m) return;
    if (d.mode === "rotate") update(d.id, { yawDeg: m.yawDeg + dx * 0.3 });
    else update(d.id, { tx: m.tx + dx / view.current.scale, tz: m.tz - dy / view.current.scale });
  };

  const onPointerUp = () => {
    drag.current = null;
  };

  const onWheel = (e: React.WheelEvent<HTMLCanvasElement>) => {
    view.current.scale *= e.deltaY < 0 ? 1.1 : 1 / 1.1;
    draw();
  };

  const [selectedId, setSelectedId] = useState<string>("");

  const submit = () => {
    const payload: AlignedMap[] = maps.map((m) => ({
      reconstruction_id: m.id,
      yaw_deg: m.yawDeg,
      translation: [m.tx, m.ty, m.tz],
      scale: m.scale,
    }));
    saveAlignment(payload, referenceId, null)
      .then((r) => setSaved(r.id))
      .catch((err: unknown) => setStatus(errorText(err)));
  };

  return (
    <div className="align-page">
      <div className="align-side">
        <h2>Align maps</h2>
        {status && <div className="banner banner-error">{status}</div>}
        {saved && <div className="banner banner-success">Alignment saved as {saved}.</div>}

        <label>
          Add a map
          <select
            value=""
            onChange={(e) => {
              const r = available.find((x) => x.id === e.target.value);
              if (r) addMap(r);
            }}
          >
            <option value="">Choose a reconstruction…</option>
            {available
              .filter((r) => !maps.some((m) => m.id === r.id))
              .map((r) => (
                <option key={r.id} value={r.id}>
                  {r.capture_name ?? r.id.slice(0, 8)} — {r.map_image_count ?? "?"} images
                </option>
              ))}
          </select>
        </label>

        <table className="align-table">
          <thead>
            <tr>
              <th>Map</th><th>Ref</th><th>Pts</th><th>Size</th><th>Poses</th>
              <th>Yaw°</th><th>X</th><th>Y</th><th>Z</th><th>Scale</th><th>Near</th>
            </tr>
          </thead>
          <tbody>
            {maps.map((m) => (
              <tr
                key={m.id}
                className={m.id === selectedId ? "selected" : ""}
                onClick={() => setSelectedId(m.id)}
              >
                <td>
                  <span className="swatch" style={{ background: m.color }} />
                  {m.label}
                  {m.error && <div className="align-error">{m.error}</div>}
                  {!m.cloud && !m.error && <div className="align-hint">loading…</div>}
                </td>
                <td><input type="radio" checked={m.id === referenceId} onChange={() => setReferenceId(m.id)} /></td>
                <td><input type="checkbox" checked={m.showPoints} onChange={(e) => update(m.id, { showPoints: e.target.checked })} /></td>
                <td><input type="number" min={1} max={6} value={m.pointSize} onChange={(e) => update(m.id, { pointSize: Number(e.target.value) })} /></td>
                <td><input type="checkbox" checked={m.showPoses} onChange={(e) => update(m.id, { showPoses: e.target.checked })} /></td>
                <td><input type="number" step={0.5} value={round(m.yawDeg)} disabled={m.id === referenceId} onChange={(e) => update(m.id, { yawDeg: Number(e.target.value) })} /></td>
                <td><input type="number" step={0.5} value={round(m.tx)} disabled={m.id === referenceId} onChange={(e) => update(m.id, { tx: Number(e.target.value) })} /></td>
                <td><input type="number" step={0.5} value={round(m.ty)} disabled={m.id === referenceId} onChange={(e) => update(m.id, { ty: Number(e.target.value) })} /></td>
                <td><input type="number" step={0.5} value={round(m.tz)} disabled={m.id === referenceId} onChange={(e) => update(m.id, { tz: Number(e.target.value) })} /></td>
                <td>
                  <input
                    type="number" step={0.01} value={round(m.scale)}
                    disabled={m.scaleLocked || m.id === referenceId}
                    title={m.scaleLocked ? "Metric already: a stereo baseline fixes this map's scale" : undefined}
                    onChange={(e) => update(m.id, { scale: Number(e.target.value) })}
                  />
                </td>
                <td className="align-near">{m.id === referenceId ? "—" : (neighbourCounts.get(m.id) ?? 0)}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="align-hint">
          Click a row to pick the map you are placing, then drag on the canvas to move it, alt-drag
          to turn it. Shift-drag pans the view and the wheel zooms. Height (Y) is perpendicular to
          this view, so it is typed rather than dragged. <b>Near</b> counts how many of that map's
          poses land within 10 m of one of the reference's — the quantity that decides whether
          anything downstream can pair the two by proximity.
        </div>

        <button className="primary" disabled={maps.length < 2 || !referenceId} onClick={submit}>
          Submit alignment
        </button>
      </div>
      <canvas
        ref={canvasRef}
        className="align-canvas"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onWheel={onWheel}
      />
    </div>
  );
}

// How much the reconstruction was allowed to trust its position priors. The poseless paths set
// this to 1000 precisely to keep a fabricated trajectory out of bundle adjustment, which also
// means nothing anchored the map's scale.
function priorSigma(r: Reconstruction): number {
  const value = r.options?.["pose_prior_position_sigma_m"];
  return typeof value === "number" ? value : 0;
}

function round(value: number): number {
  return Math.round(value * 100) / 100;
}
