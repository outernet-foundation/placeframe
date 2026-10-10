import { useEffect, useRef, useState } from "react";
import { fetchPoints, getLocalization, listReconstructions, saveScreenshot } from "../api";
import type { Reconstruction } from "../types";
import {
  DEFAULT_POINT_SIZE,
  PointCloudScene,
  overlayCameraColor,
  type CameraMode,
  type LocCameraMode,
  type PointSize,
  type Projection,
} from "./PointCloudScene";
import "./viewer.css";

const POINT_SIZE_LEVELS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

// One id, or several comma-separated: `?reconstruction=a,b` overlays both in the frame they share.
function reconstructionIdsFromUrl(): string[] {
  const raw = new URLSearchParams(window.location.search).get("reconstruction") ?? "";
  return raw
    .split(",")
    .map((id) => id.trim())
    .filter(Boolean);
}

function localizationIdFromUrl(): string | null {
  return new URLSearchParams(window.location.search).get("localization");
}

// What the legend calls a map: its capture, then its label (an aligned copy says what it was
// aligned to) or the short id.
function layerName(id: string, reconstructions: Reconstruction[]): string {
  const r = reconstructions.find((x) => x.id === id);
  if (!r) return id.slice(0, 8);
  const capture = r.capture_name ?? "";
  const label = r.label ?? r.id.slice(0, 8);
  return capture ? `${capture} · ${label}` : label;
}

interface Layer {
  id: string;
  name: string;
  points: number;
  poses: number;
  showPoints: boolean;
  showCameras: boolean;
  cameraColor: string;
}

export function ViewerPage() {
  const reconstructionIds = reconstructionIdsFromUrl();
  const reconstructionKey = reconstructionIds.join(",");
  const localizationId = localizationIdFromUrl();
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<PointCloudScene | null>(null);

  const [title, setTitle] = useState(reconstructionKey);
  const [titleDraft, setTitleDraft] = useState(reconstructionKey);
  const [editingTitle, setEditingTitle] = useState(false);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [hasCameraPoses, setHasCameraPoses] = useState(false);
  const [cameraMode, setCameraModeState] = useState<CameraMode>("frustum");
  const [projection, setProjectionState] = useState<Projection>("perspective");
  const [pointSize, setPointSizeState] = useState<PointSize>(DEFAULT_POINT_SIZE);
  const [hasLocalizedPoses, setHasLocalizedPoses] = useState(false);
  const [locCameraMode, setLocCameraModeState] = useState<LocCameraMode>("frustum");
  const [layers, setLayers] = useState<Layer[]>([]);

  useEffect(() => {
    if (!containerRef.current || reconstructionIds.length === 0) return;
    const scene = new PointCloudScene({ container: containerRef.current });
    sceneRef.current = scene;

    // The listing only names the layers; the geometry does not wait for it, and a failed listing
    // leaves the legend on short ids.
    const names = listReconstructions(false).catch((): Reconstruction[] => []);
    Promise.all(reconstructionIds.map((id) => fetchPoints(id)))
      .then(async (clouds) => {
        scene.setClouds(
          clouds.map((c, i) => ({
            id: reconstructionIds[i],
            positions: c.positions,
            colors: c.colors,
            count: c.count,
            posePositions: c.posePositions,
            poseOrientations: c.poseOrientations,
            poseCount: c.poseCount,
            rigIndices: c.rigIndices,
          })),
        );
        setHasCameraPoses(scene.hasCameraPoses());
        setStatus("ready");
        const reconstructions = await names;
        setLayers(
          clouds.map((c, i) => ({
            id: reconstructionIds[i],
            name: layerName(reconstructionIds[i], reconstructions),
            points: c.count,
            poses: c.poseCount,
            showPoints: true,
            showCameras: true,
            cameraColor: `#${overlayCameraColor(i).toString(16).padStart(6, "0")}`,
          })),
        );
        if (reconstructionIds.length === 1) {
          const name = layerName(reconstructionIds[0], reconstructions);
          setTitle((t) => (t === reconstructionKey ? name : t));
          setTitleDraft((t) => (t === reconstructionKey ? name : t));
        }
        if (!localizationId) return;
        const result = await getLocalization(localizationId);
        const ok = result.images.filter((img) => img.status === "ok" && img.position && img.quaternion_xyzw);
        const positionsArray = new Float32Array(ok.length * 3);
        const orientationsArray = new Float32Array(ok.length * 4);
        // Label pose i with the image's *original* results.json index, not its position in this
        // filtered array — those diverge as soon as any image in the run failed to localize.
        const labels = ok.map((img) => String(img.index));
        ok.forEach((img, i) => {
          const p = img.position as { x: number; y: number; z: number };
          const q = img.quaternion_xyzw as [number, number, number, number];
          positionsArray[i * 3] = p.x;
          positionsArray[i * 3 + 1] = p.y;
          positionsArray[i * 3 + 2] = p.z;
          orientationsArray[i * 4] = q[0];
          orientationsArray[i * 4 + 1] = q[1];
          orientationsArray[i * 4 + 2] = q[2];
          orientationsArray[i * 4 + 3] = q[3];
        });
        scene.setLocalizedPoses(positionsArray, orientationsArray, ok.length, labels);
        setHasLocalizedPoses(scene.hasLocalizedPoses());
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : String(err));
        setStatus("error");
      });

    return () => scene.dispose();
    // The ids come from the URL; their joined string is the dependency that matters.
  }, [reconstructionKey, localizationId]);

  function handleCameraModeChange(mode: CameraMode): void {
    setCameraModeState(mode);
    sceneRef.current?.setCameraMode(mode);
  }

  function handleLocCameraModeChange(mode: LocCameraMode): void {
    setLocCameraModeState(mode);
    sceneRef.current?.setLocCameraMode(mode);
  }

  function handlePointSizeChange(size: PointSize): void {
    setPointSizeState(size);
    sceneRef.current?.setPointSize(size);
  }

  function toggleLayer(id: string, what: "points" | "cameras"): void {
    setLayers((all) =>
      all.map((layer) => {
        if (layer.id !== id) return layer;
        const next = what === "points" ? { ...layer, showPoints: !layer.showPoints } : { ...layer, showCameras: !layer.showCameras };
        sceneRef.current?.setLayerVisibility(id, { points: next.showPoints, cameras: next.showCameras });
        return next;
      }),
    );
  }

  function flashMessage(text: string): void {
    setMessage(text);
    window.setTimeout(() => setMessage(null), 4000);
  }

  function handleCapture(): void {
    const scene = sceneRef.current;
    if (!scene) return;
    const dataUrl = scene.capturePng();
    const base64 = dataUrl.split(",")[1] ?? "";
    saveScreenshot(title, base64, localizationId)
      .then((result) => flashMessage(`Saved ${result.path}`))
      .catch((err: unknown) => flashMessage(err instanceof Error ? err.message : String(err)));
  }

  function openTitleDialog(): void {
    setTitleDraft(title);
    setEditingTitle(true);
  }

  function saveTitle(): void {
    setTitle(titleDraft.trim() || reconstructionKey);
    setEditingTitle(false);
  }

  if (reconstructionIds.length === 0) {
    return (
      <div className="viewer-banner viewer-banner-error">
        No reconstruction id in URL (expected ?reconstruction=&lt;id&gt; or ?reconstruction=&lt;id&gt;,&lt;id&gt;)
      </div>
    );
  }

  return (
    <div className="viewer">
      <header className="viewer-toolbar">
        <button className="viewer-title" onClick={openTitleDialog} title="Click to edit plot title">
          {title}
        </button>
        <div className="viewer-actions">
          <select
            value={pointSize}
            onChange={(e) => handlePointSizeChange(e.target.value === "off" ? "off" : Number(e.target.value))}
          >
            <option value="off">Points: Off</option>
            {POINT_SIZE_LEVELS.map((level) => (
              <option key={level} value={level}>
                Points: {level}
              </option>
            ))}
          </select>
          {hasCameraPoses && (
            <select value={cameraMode} onChange={(e) => handleCameraModeChange(e.target.value as CameraMode)}>
              <option value="frustum">Map cam: Frustum</option>
              <option value="arrows">Map cam: Arrows</option>
              <option value="off">Map cam: Off</option>
            </select>
          )}
          {hasLocalizedPoses && (
            <select value={locCameraMode} onChange={(e) => handleLocCameraModeChange(e.target.value as LocCameraMode)}>
              <option value="frustum">Loc cam: Frustum</option>
              <option value="axes">Loc cam: Axes</option>
              <option value="off">Loc cam: Off</option>
            </select>
          )}
          <button onClick={() => sceneRef.current?.recenter()}>Recenter</button>
          <button onClick={() => sceneRef.current?.setPlaneView("x", "y")}>XY</button>
          <button onClick={() => sceneRef.current?.setPlaneView("x", "z")}>XZ</button>
          <button onClick={() => sceneRef.current?.setPlaneView("y", "z")}>YZ</button>
          {/* Orthographic is what an axis-on view is usually for: with no perspective divide a
              plane parallel to the view direction projects to a line, so a wall reads as an edge
              you can judge. Left as a toggle rather than tied to the XY/XZ/YZ buttons, so the two
              projections can be compared on the same viewpoint. */}
          <select
            value={projection}
            onChange={(e) => {
              const next = e.target.value as Projection;
              setProjectionState(next);
              sceneRef.current?.setProjection(next);
            }}
            title="Orthographic squashes planes parallel to the view direction into lines"
          >
            <option value="perspective">Perspective</option>
            <option value="orthographic">Orthographic</option>
          </select>
          <button onClick={handleCapture} disabled={status !== "ready"}>
            Capture
          </button>
        </div>
      </header>

      {status === "loading" && <div className="viewer-banner">Loading point cloud{reconstructionIds.length > 1 ? "s" : ""}…</div>}
      {status === "error" && <div className="viewer-banner viewer-banner-error">{error}</div>}
      {message && <div className="viewer-banner viewer-banner-success">{message}</div>}

      <div ref={containerRef} className="viewer-canvas" />

      {/* The legend: one row per overlaid map, with its own switches for the cloud and the
          camera trail. Shown for a single map too, since the counts are useful there as well. */}
      {layers.length > 0 && (
        <div className="viewer-legend">
          {layers.map((layer, i) => (
            <div className="viewer-legend-row" key={layer.id}>
              <span
                className="viewer-legend-swatch"
                style={{ background: i === 0 && layer.poses > 0 ? "#ff9500" : layer.cameraColor }}
                title="Camera trail colour"
              />
              <span className="viewer-legend-name" title={layer.id}>
                {layer.name}
              </span>
              <label>
                <input type="checkbox" checked={layer.showPoints} onChange={() => toggleLayer(layer.id, "points")} />
                points ({layer.points.toLocaleString()})
              </label>
              <label className={layer.poses === 0 ? "viewer-legend-muted" : undefined}>
                <input
                  type="checkbox"
                  checked={layer.showCameras}
                  disabled={layer.poses === 0}
                  onChange={() => toggleLayer(layer.id, "cameras")}
                />
                cameras ({layer.poses.toLocaleString()})
              </label>
            </div>
          ))}
        </div>
      )}

      {editingTitle && (
        <div className="dialog-overlay" onClick={() => setEditingTitle(false)}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <h3>Plot title</h3>
            <label>
              Used as the Capture folder/file name prefix
              <input value={titleDraft} onChange={(e) => setTitleDraft(e.target.value)} autoFocus />
            </label>
            <div className="dialog-actions">
              <button onClick={() => setEditingTitle(false)}>Cancel</button>
              <button className="primary" onClick={saveTitle}>
                Save
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
