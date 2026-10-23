import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { fetchPoints, listReconstructions, saveAlignment, startIcpMatch, type AlignedMap, type PointCloud } from "../api";
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
  // The capture a transformed copy lands under, which is where its row appears on the captures page.
  captureSessionId: string | null;
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
  // Whether the map looks metric already, which only warns: scale stays editable on every map
  // but the reference. The page cannot tell reliably -- a spherical map's 12 views are a
  // multi-camera rig, whose priors stay out of bundle adjustment, yet it carries the default
  // prior sigma, and is_stereo is null in the stats-free listing this page reads -- and a lock
  // that guesses wrong leaves no way to scale an Insta360 map onto a Zed one.
  looksMetric: boolean;
}

// What a confirmation dialog is asking about: both actions start work that outlives this tab.
type Confirm = { kind: "merge"; name: string } | { kind: "icp"; fitScale: Record<string, boolean> };

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
  // What was started from here, said once it is under way. The work runs in the backend, so this
  // tab may be closed; the captures page shows its progress.
  const [started, setStarted] = useState<string | null>(null);
  // One start at a time, and none after: pressing again would queue a second copy of the same job
  // with nothing to say it happened.
  const [busy, setBusy] = useState(false);
  const [confirm, setConfirm] = useState<Confirm | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const thinned = useRef<Map<string, Float32Array>>(new Map());
  const view = useRef({ scale: 4, ox: 0, oz: 0 });
  const drag = useRef<{ id: string | null; mode: "move" | "rotate" | "pan"; x: number; y: number } | null>(null);

  useEffect(() => {
    // stats=false: the full listing streams through every capture tar to report stereo-ness and
    // frame counts, which takes minutes on a stack holding large captures and times out while a
    // reconstruction is running. None of it is needed here -- scale locking falls back to the
    // prior sigma, which the options carry either way.
    listReconstructions(false)
      .then((all) => setAvailable(all.filter((r) => r.status === "succeeded")))
      .catch((err: unknown) => setStatus(errorText(err)));
  }, []);

  // Which maps have been taken on. Kept in a ref rather than decided inside the state updater:
  // React runs an updater eagerly only while its queue is empty, so a flag set in there is still
  // unset for every map after the first of a batch -- and the fetch guarded by it never ran, which
  // left those maps on "loading..." for ever, with no error because nothing had failed.
  const requested = useRef<Set<string>>(new Set());
  const addMap = useCallback(
    (r: Reconstruction) => {
      if (requested.current.has(r.id)) return;
      requested.current.add(r.id);
      setMaps((prev) => {
        if (prev.some((m) => m.id === r.id)) return prev;
        const color = MAP_COLORS[prev.length % MAP_COLORS.length];
        const label = r.capture_name ?? r.id.slice(0, 8);
        return [
        ...prev,
        {
          id: r.id, label, captureSessionId: r.capture_session_id, color, cloud: null, error: null,
          showPoints: true, showPoses: true, pointSize: 1,
          yawDeg: 0, tx: 0, ty: 0, tz: 0, scale: 1,
          // A stereo baseline fixes metric scale, and so does a position prior that bundle
          // adjustment actually used. A poseless capture has neither -- its trajectory is
          // synthetic and the prior deliberately neutralised.
          looksMetric: r.is_stereo === true || priorSigma(r) < 100,
        },
        ];
      });
      setReferenceId((prev) => prev || r.id);
      fetchPoints(r.id)
        .then((cloud) => {
          thinned.current.set(r.id, thin(cloud.positions, cloud.count));
          setMaps((prev) => prev.map((m) => (m.id === r.id ? { ...m, cloud } : m)));
        })
        .catch((err: unknown) =>
          setMaps((prev) => prev.map((m) => (m.id === r.id ? { ...m, error: errorText(err) } : m))),
        );
    },
    [],
  );

  // Opened from the captures tree with a selection: the maps to place are named in the URL, so the
  // page arrives ready rather than asking for them again.
  // Abandons the placement and returns to the tree the maps were chosen in. Nothing is kept: a
  // placement only exists in memory until Save placement, so leaving is the whole undo.
  const cancel = useCallback(() => {
    window.location.href = "/";
  }, []);

  const preloaded = useRef(false);
  useEffect(() => {
    if (preloaded.current || available.length === 0) return;
    const wanted = new URLSearchParams(window.location.search).get("maps")?.split(",").filter(Boolean) ?? [];
    const found = wanted.map((id) => available.find((r) => r.id === id)).filter((r): r is Reconstruction => !!r);
    if (found.length === 0) return;
    preloaded.current = true;
    found.forEach(addMap);
  }, [available, addMap]);

  const update = (id: string, patch: Partial<MapState>) =>
    setMaps((prev) => prev.map((m) => (m.id === id ? { ...m, ...patch } : m)));

  // How many of a map's poses land near *any other* map's, at the current placement. The point of
  // aligning coarsely is that something downstream can pair frames by proximity, so the number that
  // matters is how many pairs that would actually find — not whether the overlay looks right.
  //
  // Against any other map, not just the reference: maps of one site often form a chain rather than
  // a star, and a map that overlaps its neighbour perfectly while never touching the reference is
  // correctly placed. Counting only against the reference reports 0 for it, which reads as badly
  // placed and is the opposite of the truth.
  const neighbourCounts = useMemo(() => {
    const placed = maps
      .filter((m) => m.cloud)
      .map((m) => {
        const poses: [number, number][] = [];
        for (let i = 0; i < m.cloud!.poseCount; i++) {
          poses.push(place(m, m.cloud!.posePositions[i * 3], m.cloud!.posePositions[i * 3 + 2]));
        }
        return { id: m.id, poses };
      });
    const out = new Map<string, number>();
    for (const a of placed) {
      let near = 0;
      for (const p of a.poses) {
        const hit = placed.some(
          (b) => b.id !== a.id && b.poses.some((q) => (q[0] - p[0]) ** 2 + (q[1] - p[1]) ** 2 < 100),
        );
        if (hit) near++;
      }
      out.set(a.id, near);
    }
    return out;
  }, [maps]);

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

  const reference = maps.find((m) => m.id === referenceId);
  const candidates = maps.filter((m) => m.id !== referenceId && m.cloud);
  const ready = !busy && !started && maps.length >= 2 && !!reference?.cloud && candidates.length > 0;

  const startMerge = (name: string) => {
    const payload: AlignedMap[] = maps.map((m) => ({
      reconstruction_id: m.id,
      yaw_deg: m.yawDeg,
      translation: [m.tx, m.ty, m.tz],
      scale: m.scale,
    }));
    setStatus(null);
    setBusy(true);
    saveAlignment(payload, referenceId, name, true)
      .then(() =>
        setStarted(
          `Merging "${name}" has started. You can close this tab: progress shows as a new row at the top of the ` +
            `main Placeframe window, and the merged capture and its reconstruction appear there when they exist.`,
        ),
      )
      .catch((err: unknown) => setStatus(errorText(err)))
      .finally(() => setBusy(false));
  };

  // One job per candidate, each against the reference: a placement of several maps is several
  // independent fits, and each copy lands under its own capture.
  const startIcp = (fitScale: Record<string, boolean>) => {
    if (!reference) return;
    setStatus(null);
    setBusy(true);
    Promise.all(
      candidates.map((m) =>
        startIcpMatch({
          reference_id: reference.id,
          candidate_id: m.id,
          yaw_deg: m.yawDeg,
          translation: [m.tx, m.ty, m.tz],
          scale: m.scale,
          fit_scale: fitScale[m.id] ?? true,
          candidate_capture_session_id: m.captureSessionId,
          candidate_label: m.label,
          reference_label: reference.label,
        }),
      ),
    )
      .then(() =>
        setStarted(
          `ICP matching has started. You can close this tab: progress shows in the main Placeframe window, as a new ` +
            `row under ${candidates.map((m) => m.label).join(", ")}, which becomes the transformed reconstruction when it is done.`,
        ),
      )
      .catch((err: unknown) => setStatus(errorText(err)))
      .finally(() => setBusy(false));
  };

  return (
    <div className="align-page">
      <div className="align-side">
        <h2>Align maps</h2>
        {status && <div className="banner banner-error">{status}</div>}
        {started && <div className="banner banner-success">{started}</div>}

        {/* The maps to place are chosen in the captures tree and arrive in the URL, so there is no
            picker here: this page does one thing, and changing the selection means going back. */}

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
                    disabled={m.id === referenceId}
                    title={
                      m.looksMetric && m.id !== referenceId
                        ? "This map looks metric already (stereo, or position priors); change its scale only if it has none, e.g. a spherical capture"
                        : undefined
                    }
                    onChange={(e) => update(m.id, { scale: Number(e.target.value) })}
                  />
                </td>
                <td className="align-near">{neighbourCounts.get(m.id) ?? 0}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <div className="align-hint">
          Click a row to pick the map you are placing, then drag on the canvas to move it, alt-drag
          to turn it. Shift-drag pans the view and the wheel zooms. Height (Y) is perpendicular to
          this view, so it is typed rather than dragged. <b>Near</b> counts how many of that map's
          poses land within 10 m of <i>any other</i> map's — the quantity that decides whether
          anything downstream can pair them by proximity. Maps of one site often form a chain, so a
          map that never touches the reference can still be perfectly placed against its neighbour.
        </div>

        {/* One action per row, each with what it does next to it, and leaving last: the two start
            different jobs, and reading both before choosing is the point. */}
        <div className="align-actions">
          <button
            className="primary"
            disabled={!ready || maps.length !== 2}
            title={maps.length !== 2 ? "ICP matches one map to the reference: open exactly two maps" : undefined}
            onClick={() =>
              setConfirm({ kind: "icp", fitScale: Object.fromEntries(candidates.map((m) => [m.id, !m.looksMetric])) })
            }
          >
            ICP match…
          </button>
          <div className="align-hint">
            For two maps of the same place: refines the placement shown against the reference's point
            cloud (scale too, for a map with no metric scale of its own) and makes a transformed copy of
            the other map, in the reference's frame and units. The original is untouched.
          </div>
          <button
            disabled={!ready}
            onClick={() => setConfirm({ kind: "merge", name: maps.map((m) => m.label).join(" + ") })}
          >
            {busy ? "Starting…" : "Merge and reconstruct…"}
          </button>
          <div className="align-hint">
            Restates every capture's poses in this frame and reconstructs from all of them at once,
            pairing frames of different captures that the placement puts within 15 m. That proximity is
            the whole point of placing them: it is evidence retrieval does not have, and without it two
            walks through the same corner can share almost nothing.
          </div>
          <button disabled={busy} onClick={cancel}>
            {started ? "Back to captures" : "Cancel"}
          </button>
        </div>
      </div>
      {confirm?.kind === "merge" && (
        <div className="dialog-overlay" onClick={() => setConfirm(null)}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <h3>Merge and reconstruct</h3>
            <div className="align-hint">
              The captures behind {maps.map((m) => m.label).join(", ")} will be merged into one new capture, each
              placed as shown here, and reconstructed from all of them at once. Frames of different captures that
              the placement puts within 15 m of each other are paired. This takes a while; the originals are
              untouched.
            </div>
            <div className="align-hint">
              The merge becomes a capture of its own, and the reconstruction built from it takes the same name.
              Naming it for the walks that went in is what makes it findable later.
            </div>
            <label>
              Name
              <input
                autoFocus
                type="text"
                value={confirm.name}
                onChange={(e) => setConfirm({ kind: "merge", name: e.target.value })}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && confirm.name.trim()) {
                    setConfirm(null);
                    startMerge(confirm.name.trim());
                  }
                  if (e.key === "Escape") setConfirm(null);
                }}
              />
            </label>
            <div className="dialog-actions">
              <button onClick={() => setConfirm(null)}>Cancel</button>
              <button
                className="primary"
                disabled={!confirm.name.trim()}
                onClick={() => {
                  const chosen = confirm.name.trim();
                  setConfirm(null);
                  startMerge(chosen);
                }}
              >
                Merge and reconstruct
              </button>
            </div>
          </div>
        </div>
      )}
      {confirm?.kind === "icp" && reference && (
        <div className="dialog-overlay" onClick={() => setConfirm(null)}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <h3>ICP match</h3>
            {candidates.map((m) => (
              <div key={m.id} className="align-hint">
                <b>{m.label}</b> will be transformed to match the reference <b>{reference.label}</b> using ICP,
                starting from the placement shown. The result is a new reconstruction under {m.label}&apos;s capture,
                in {reference.label}&apos;s frame and units; {m.label} itself is untouched.
                <label style={{ flexDirection: "row", alignItems: "center", gap: 8, marginTop: 6 }}>
                  <input
                    type="checkbox"
                    checked={confirm.fitScale[m.id] ?? true}
                    onChange={(e) => setConfirm({ kind: "icp", fitScale: { ...confirm.fitScale, [m.id]: e.target.checked } })}
                  />
                  Let ICP adjust the scale
                  {m.looksMetric && " (this map looks metric already, e.g. stereo)"}
                </label>
              </div>
            ))}
            <div className="align-hint">
              ICP needs the maps roughly in place already: within a couple of metres and a few degrees.
            </div>
            <div className="dialog-actions">
              <button onClick={() => setConfirm(null)}>Cancel</button>
              <button
                className="primary"
                autoFocus
                onClick={() => {
                  const fitScale = confirm.fitScale;
                  setConfirm(null);
                  startIcp(fitScale);
                }}
              >
                Start ICP match
              </button>
            </div>
          </div>
        </div>
      )}
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
