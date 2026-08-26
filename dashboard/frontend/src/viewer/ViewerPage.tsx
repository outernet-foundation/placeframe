import { useEffect, useRef, useState } from "react";
import { fetchPoints, getLocalization, saveScreenshot } from "../api";
import { DEFAULT_POINT_SIZE, PointCloudScene, type CameraMode, type PointSize } from "./PointCloudScene";
import "./viewer.css";

const POINT_SIZE_LEVELS = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];

function reconstructionIdFromUrl(): string {
  return new URLSearchParams(window.location.search).get("reconstruction") ?? "";
}

function localizationIdFromUrl(): string | null {
  return new URLSearchParams(window.location.search).get("localization");
}

export function ViewerPage() {
  const reconstructionId = reconstructionIdFromUrl();
  const localizationId = localizationIdFromUrl();
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<PointCloudScene | null>(null);

  const [title, setTitle] = useState(reconstructionId);
  const [titleDraft, setTitleDraft] = useState(reconstructionId);
  const [editingTitle, setEditingTitle] = useState(false);
  const [status, setStatus] = useState<"loading" | "ready" | "error">("loading");
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [hasCameraPoses, setHasCameraPoses] = useState(false);
  const [cameraMode, setCameraModeState] = useState<CameraMode>("frustum");
  const [pointSize, setPointSizeState] = useState<PointSize>(DEFAULT_POINT_SIZE);
  const [localizedPoseCount, setLocalizedPoseCount] = useState<number | null>(null);

  useEffect(() => {
    if (!containerRef.current || !reconstructionId) return;
    const scene = new PointCloudScene({ container: containerRef.current });
    sceneRef.current = scene;

    fetchPoints(reconstructionId)
      .then(({ positions, colors, count, posePositions, poseOrientations, poseCount }) => {
        scene.setPoints(positions, colors, count, posePositions, poseOrientations, poseCount);
        setHasCameraPoses(scene.hasCameraPoses());
        setStatus("ready");
        if (!localizationId) return null;
        return getLocalization(localizationId).then((result) => {
          const ok = result.images.filter((img) => img.status === "ok" && img.position && img.quaternion_xyzw);
          const positionsArray = new Float32Array(ok.length * 3);
          const orientationsArray = new Float32Array(ok.length * 4);
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
          scene.setLocalizedPoses(positionsArray, orientationsArray, ok.length);
          setLocalizedPoseCount(ok.length);
        });
      })
      .catch((err: unknown) => {
        setError(err instanceof Error ? err.message : String(err));
        setStatus("error");
      });

    return () => scene.dispose();
  }, [reconstructionId, localizationId]);

  function handleCameraModeChange(mode: CameraMode): void {
    setCameraModeState(mode);
    sceneRef.current?.setCameraMode(mode);
  }

  function handlePointSizeChange(size: PointSize): void {
    setPointSizeState(size);
    sceneRef.current?.setPointSize(size);
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
    saveScreenshot(title, base64)
      .then((result) => flashMessage(`Saved ${result.path}`))
      .catch((err: unknown) => flashMessage(err instanceof Error ? err.message : String(err)));
  }

  function openTitleDialog(): void {
    setTitleDraft(title);
    setEditingTitle(true);
  }

  function saveTitle(): void {
    setTitle(titleDraft.trim() || reconstructionId);
    setEditingTitle(false);
  }

  if (!reconstructionId) {
    return <div className="viewer-banner viewer-banner-error">No reconstruction id in URL (expected ?reconstruction=&lt;id&gt;)</div>;
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
              <option value="frustum">Camera: Frustum</option>
              <option value="arrows">Camera: Arrows</option>
              <option value="off">Camera: Off</option>
            </select>
          )}
          <button onClick={() => sceneRef.current?.recenter()}>Recenter</button>
          <button onClick={() => sceneRef.current?.setPlaneView("x", "y")}>XY</button>
          <button onClick={() => sceneRef.current?.setPlaneView("x", "z")}>XZ</button>
          <button onClick={() => sceneRef.current?.setPlaneView("y", "z")}>YZ</button>
          <button onClick={handleCapture} disabled={status !== "ready"}>
            Capture
          </button>
        </div>
      </header>

      {status === "loading" && <div className="viewer-banner">Loading point cloud…</div>}
      {status === "error" && <div className="viewer-banner viewer-banner-error">{error}</div>}
      {message && <div className="viewer-banner viewer-banner-success">{message}</div>}
      {localizedPoseCount !== null && (
        <div className="viewer-banner">Showing {localizedPoseCount} localized pose(s) in purple.</div>
      )}

      <div ref={containerRef} className="viewer-canvas" />

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
