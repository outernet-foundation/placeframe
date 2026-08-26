import * as THREE from "three";

export type Axis = "x" | "y" | "z";

const AXIS_VECTORS: Record<Axis, THREE.Vector3> = {
  x: new THREE.Vector3(1, 0, 0),
  y: new THREE.Vector3(0, 1, 0),
  z: new THREE.Vector3(0, 0, 1),
};

// Standard RGB-per-axis convention: X=red, Y=green, Z=blue.
const AXIS_COLORS: Record<Axis, number> = {
  x: 0xdd3333,
  y: 0x33aa33,
  z: 0x3366dd,
};

const ROTATE_SPEED = 0.006;
const PAN_SPEED_FACTOR = 0.0015;
const ZOOM_SPEED = 0.0015;
const WORLD_UP = new THREE.Vector3(0, 1, 0);
const SCENE_BACKGROUND_COLOR = 0xf3f3f3;

// Every Nth pose gets a frame-number label and full-brightness marker color; the rest are dimmed
// (blended toward the background, not darkened — darkening a bright color reads as *higher*
// contrast against this light background, the opposite of "dim") so the labeled poses stand out.
const LABEL_EVERY_N = 10;
const DIM_BLEND_TOWARD_BACKGROUND = 0.72;

function dimColor(color: THREE.Color): THREE.Color {
  return color.clone().lerp(new THREE.Color(SCENE_BACKGROUND_COLOR), DIM_BLEND_TOWARD_BACKGROUND);
}

export type CameraMode = "frustum" | "arrows" | "off";
export type LocCameraMode = "frustum" | "axes" | "off";
export type PointSize = number | "off"; // 1-10, or "off"

// Point size at level N is cloudRadius * POINT_SIZE_UNIT * N; level 2 matches the viewer's old
// fixed default (cloudRadius * 0.004).
const POINT_SIZE_UNIT = 0.002;
export const DEFAULT_POINT_SIZE: PointSize = 2;

// Raw reconstruction data is OPENCV-world convention: +Y is physically *down* (confirmed against
// the ZED capture pipeline's COORDINATE_SYSTEM.IMAGE init and the reconstructor's gravity
// alignment to world [0,1,0]). Data stays untouched — only the camera's starting orientation is
// chosen so the initial/recenter view reads correctly, with world -Y (true physical up) rendered
// toward the top of the screen, and a pleasant oblique tilt rather than a flat top-down view.
function buildDefaultOrientation(): THREE.Quaternion {
  const trueUp = new THREE.Vector3(0, -1, 0);
  const back = new THREE.Vector3(0.55, -0.35, 0.75).normalize(); // camera sits above-and-to-the-side
  const right = new THREE.Vector3().crossVectors(trueUp, back).normalize();
  const up = new THREE.Vector3().crossVectors(back, right).normalize();
  const m = new THREE.Matrix4().makeBasis(right, up, back);
  return new THREE.Quaternion().setFromRotationMatrix(m);
}

const DEFAULT_ORIENTATION = buildDefaultOrientation();

// Camera orientation Q such that world `rightAxis` maps to the camera's local +X (screen right)
// and world `upAxis` maps to the camera's local +Y (screen up) — i.e. looking straight down the
// remaining axis. Reused directly as `cameraOrientation`, so plane views are exact and never hit
// a gimbal singularity (there's no azimuth/elevation state to go through).
function planeViewQuaternion(rightAxis: Axis, upAxis: Axis): THREE.Quaternion {
  const right = AXIS_VECTORS[rightAxis].clone();
  const up = AXIS_VECTORS[upAxis].clone();
  const back = new THREE.Vector3().crossVectors(right, up).normalize(); // camera's local +Z (points away from target)
  // Columns (right, up, back) are each unit and mutually orthogonal, so this basis matrix is
  // orthonormal — it *is* the camera orientation directly (world-axis images = camera's local
  // basis vectors), no inversion needed.
  const m = new THREE.Matrix4().makeBasis(right, up, back);
  return new THREE.Quaternion().setFromRotationMatrix(m);
}

function median(values: Float32Array): number {
  const sorted = values.slice().sort((a, b) => a - b);
  return sorted.length ? sorted[Math.floor(sorted.length / 2)] : 0;
}

function percentile(values: number[], p: number): number {
  if (values.length === 0) return 0;
  const sorted = [...values].sort((a, b) => a - b);
  const index = Math.min(sorted.length - 1, Math.floor((p / 100) * sorted.length));
  return sorted[index];
}

function buildAxes(length: number): THREE.Group {
  const group = new THREE.Group();
  (Object.keys(AXIS_VECTORS) as Axis[]).forEach((axis) => {
    const arrow = new THREE.ArrowHelper(
      AXIS_VECTORS[axis],
      new THREE.Vector3(0, 0, 0),
      length,
      AXIS_COLORS[axis],
      length * 0.15,
      length * 0.08,
    );
    group.add(arrow);
  });
  return group;
}

function buildCircle(radius: number, plane: "xy" | "xz" | "yz", color: number): THREE.Line {
  const segments = 96;
  const points: THREE.Vector3[] = [];
  for (let i = 0; i <= segments; i++) {
    const t = (i / segments) * Math.PI * 2;
    const a = Math.cos(t) * radius;
    const b = Math.sin(t) * radius;
    if (plane === "xy") points.push(new THREE.Vector3(a, b, 0));
    else if (plane === "xz") points.push(new THREE.Vector3(a, 0, b));
    else points.push(new THREE.Vector3(0, a, b));
  }
  const geometry = new THREE.BufferGeometry().setFromPoints(points);
  const material = new THREE.LineBasicMaterial({ color, transparent: true, opacity: 0.6 });
  return new THREE.Line(geometry, material);
}

// The rotation gizmo shown while left-dragging: a wireframe sphere plus three great circles, each
// circle colored by the axis it represents rotation *around* — e.g. the circle lying in the YZ
// plane (perpendicular to X) is colored red, matching the X-axis arrow.
function buildGizmo(radius: number): THREE.Group {
  const group = new THREE.Group();
  group.add(buildCircle(radius, "yz", AXIS_COLORS.x));
  group.add(buildCircle(radius, "xz", AXIS_COLORS.y));
  group.add(buildCircle(radius, "xy", AXIS_COLORS.z));
  const sphere = new THREE.Mesh(
    new THREE.SphereGeometry(radius, 24, 16),
    new THREE.MeshBasicMaterial({ color: 0x888888, wireframe: true, transparent: true, opacity: 0.15 }),
  );
  group.add(sphere);
  return group;
}

const CAMERA_POSE_COLOR = 0xff9500;
// Distinct from the reconstruction's own orange poses and from the RGB axis colors, so a handful
// of overlaid localized query poses read immediately as "a different dataset."
const LOCALIZED_POSE_COLOR = 0x9c27b0;

// One wireframe frustum per pose, merged into a single LineSegments geometry (a few hundred poses
// is trivial either way, but one draw call is simpler than managing per-pose objects). Local
// frustum shape is in OpenCV camera space (X right, Y down, Z forward) — apex at the camera
// center, base facing the direction the camera looks — then rotated/translated by each pose's
// world_from_rig quaternion/position (offset by the same recentering as the point cloud).
function buildCameraFrustums(
  posePositions: Float32Array,
  poseOrientations: Float32Array,
  poseCount: number,
  center: THREE.Vector3,
  size: number,
  color: number = CAMERA_POSE_COLOR,
  highlightEvery: number = LABEL_EVERY_N,
): THREE.LineSegments {
  const halfWidth = size * 0.5;
  const halfHeight = size * 0.35;
  const localCorners = [
    new THREE.Vector3(-halfWidth, -halfHeight, size),
    new THREE.Vector3(halfWidth, -halfHeight, size),
    new THREE.Vector3(halfWidth, halfHeight, size),
    new THREE.Vector3(-halfWidth, halfHeight, size),
  ];

  const vertices = new Float32Array(poseCount * 8 /* edges per frustum */ * 2 /* points per edge */ * 3);
  const colors = new Float32Array(vertices.length);
  const fullColor = new THREE.Color(color);
  const dimmedColor = dimColor(fullColor);
  const q = new THREE.Quaternion();
  const p = new THREE.Vector3();
  const apex = new THREE.Vector3();
  const corners = [new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3()];
  let vOffset = 0;
  let cOffset = 0;

  const pushEdge = (a: THREE.Vector3, b: THREE.Vector3, c: THREE.Color) => {
    vertices[vOffset++] = a.x;
    vertices[vOffset++] = a.y;
    vertices[vOffset++] = a.z;
    vertices[vOffset++] = b.x;
    vertices[vOffset++] = b.y;
    vertices[vOffset++] = b.z;
    for (let end = 0; end < 2; end++) {
      colors[cOffset++] = c.r;
      colors[cOffset++] = c.g;
      colors[cOffset++] = c.b;
    }
  };

  for (let i = 0; i < poseCount; i++) {
    q.set(poseOrientations[i * 4], poseOrientations[i * 4 + 1], poseOrientations[i * 4 + 2], poseOrientations[i * 4 + 3]);
    p.set(posePositions[i * 3] - center.x, posePositions[i * 3 + 1] - center.y, posePositions[i * 3 + 2] - center.z);
    apex.copy(p);
    for (let c = 0; c < 4; c++) {
      corners[c]
        .copy(localCorners[c])
        .applyQuaternion(q)
        .add(p);
    }
    const poseColor = i % highlightEvery === 0 ? fullColor : dimmedColor;
    for (let c = 0; c < 4; c++) pushEdge(apex, corners[c], poseColor);
    for (let c = 0; c < 4; c++) pushEdge(corners[c], corners[(c + 1) % 4], poseColor);
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(vertices, 3));
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  const material = new THREE.LineBasicMaterial({ vertexColors: true, transparent: true, opacity: 0.85 });
  return new THREE.LineSegments(geometry, material);
}

// A lighter per-pose orientation indicator than a full frustum: a tiny RGB axis triad (matching
// the world axes' color convention) at each camera center, merged into one LineSegments geometry
// for a single draw call. Plain colored segments rather than ArrowHelper's cone-capped arrows —
// at this size (a few % of cloudRadius) a cone tip is imperceptible, and a few hundred ArrowHelper
// object hierarchies is meaningfully more draw-call overhead than one merged buffer.
function buildCameraArrows(
  posePositions: Float32Array,
  poseOrientations: Float32Array,
  poseCount: number,
  center: THREE.Vector3,
  size: number,
  highlightEvery: number = LABEL_EVERY_N,
): THREE.LineSegments {
  const axes: Axis[] = ["x", "y", "z"];
  const axisRgbFull = axes.map((axis) => new THREE.Color(AXIS_COLORS[axis]));
  const axisRgbDimmed = axisRgbFull.map(dimColor);

  const vertices = new Float32Array(poseCount * axes.length * 2 * 3);
  const colors = new Float32Array(vertices.length);
  const q = new THREE.Quaternion();
  const p = new THREE.Vector3();
  const tip = new THREE.Vector3();
  let vOffset = 0;
  let cOffset = 0;

  for (let i = 0; i < poseCount; i++) {
    q.set(poseOrientations[i * 4], poseOrientations[i * 4 + 1], poseOrientations[i * 4 + 2], poseOrientations[i * 4 + 3]);
    p.set(posePositions[i * 3] - center.x, posePositions[i * 3 + 1] - center.y, posePositions[i * 3 + 2] - center.z);
    const axisRgb = i % highlightEvery === 0 ? axisRgbFull : axisRgbDimmed;

    axes.forEach((axis, axisIndex) => {
      tip.copy(AXIS_VECTORS[axis]).multiplyScalar(size).applyQuaternion(q).add(p);
      vertices[vOffset++] = p.x;
      vertices[vOffset++] = p.y;
      vertices[vOffset++] = p.z;
      vertices[vOffset++] = tip.x;
      vertices[vOffset++] = tip.y;
      vertices[vOffset++] = tip.z;
      const rgb = axisRgb[axisIndex];
      for (let end = 0; end < 2; end++) {
        colors[cOffset++] = rgb.r;
        colors[cOffset++] = rgb.g;
        colors[cOffset++] = rgb.b;
      }
    });
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(vertices, 3));
  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  const material = new THREE.LineBasicMaterial({ vertexColors: true, transparent: true, opacity: 0.9 });
  return new THREE.LineSegments(geometry, material);
}

// A polyline through pose positions in array order — the order frame_poses.npz was written in,
// which follows the reconstructor's frame registration order (temporally coherent in practice for
// incremental SfM over a continuous walk, though not guaranteed to be strictly sorted).
function buildTrajectory(posePositions: Float32Array, poseCount: number, center: THREE.Vector3): THREE.Line {
  const vertices = new Float32Array(poseCount * 3);
  for (let i = 0; i < poseCount; i++) {
    vertices[i * 3] = posePositions[i * 3] - center.x;
    vertices[i * 3 + 1] = posePositions[i * 3 + 1] - center.y;
    vertices[i * 3 + 2] = posePositions[i * 3 + 2] - center.z;
  }
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(vertices, 3));
  const material = new THREE.LineBasicMaterial({ color: CAMERA_POSE_COLOR, transparent: true, opacity: 0.45 });
  return new THREE.Line(geometry, material);
}

// Wide canvas (not square) so multi-digit frame numbers aren't cramped; resolution only — the
// on-screen size is set via sprite.scale below.
const LABEL_CANVAS_WIDTH = 96;
const LABEL_CANVAS_HEIGHT = 48;
// Constant on-screen size regardless of zoom: sizeAttenuation:false makes a sprite's `scale` a
// screen-space (not world-space/perspective) size, so it doesn't shrink or grow with distance.
// Kept small and deliberately un-boxed (a halo outline, not a filled badge) so a cluster of labels
// near a looping trajectory doesn't turn into a wall of overlapping circles.
const LABEL_SCREEN_HEIGHT = 0.022;
const LABEL_SCREEN_WIDTH = LABEL_SCREEN_HEIGHT * (LABEL_CANVAS_WIDTH / LABEL_CANVAS_HEIGHT);

function buildLabelTexture(text: string): THREE.CanvasTexture {
  const canvas = document.createElement("canvas");
  canvas.width = LABEL_CANVAS_WIDTH;
  canvas.height = LABEL_CANVAS_HEIGHT;
  const ctx = canvas.getContext("2d");
  if (ctx) {
    const cx = LABEL_CANVAS_WIDTH / 2;
    const cy = LABEL_CANVAS_HEIGHT / 2;
    ctx.font = "bold 30px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    // White halo (thick stroke) behind dark fill keeps the number legible over both the point
    // cloud and the light background, without a filled badge shape adding visual weight.
    ctx.lineWidth = 7;
    ctx.strokeStyle = "rgba(255, 255, 255, 0.9)";
    ctx.strokeText(text, cx, cy + 1);
    ctx.fillStyle = "#222222";
    ctx.fillText(text, cx, cy + 1);
  }
  const texture = new THREE.CanvasTexture(canvas);
  texture.needsUpdate = true;
  return texture;
}

// A frame-number label (a screen-space-sized sprite, so it reads the same at any zoom) at every
// Nth pose, offset toward true physical up (world -Y — see buildDefaultOrientation) so it sits
// just above rather than on top of that pose's frustum/arrow marker — close enough that it's
// unambiguous which marker a given label belongs to even when several poses are near each other.
// depthTest is off so labels stay legible even when a marker is behind the point cloud.
function buildPoseLabels(
  posePositions: Float32Array,
  poseCount: number,
  center: THREE.Vector3,
  size: number,
  labelEvery: number = LABEL_EVERY_N,
  labelText: (index: number) => string = (index) => String(index),
): THREE.Group {
  const group = new THREE.Group();
  const upOffset = size * 0.85;
  for (let i = 0; i < poseCount; i += labelEvery) {
    const texture = buildLabelTexture(labelText(i));
    const material = new THREE.SpriteMaterial({ map: texture, sizeAttenuation: false, depthTest: false });
    const sprite = new THREE.Sprite(material);
    sprite.renderOrder = 10;
    sprite.scale.set(LABEL_SCREEN_WIDTH, LABEL_SCREEN_HEIGHT, 1);
    sprite.position.set(
      posePositions[i * 3] - center.x,
      posePositions[i * 3 + 1] - center.y - upOffset,
      posePositions[i * 3 + 2] - center.z,
    );
    group.add(sprite);
  }
  return group;
}

export interface PointCloudSceneOptions {
  container: HTMLElement;
}

/**
 * A CloudCompare-style point cloud viewer. The point cloud, world axes, and rotation gizmo are
 * all fixed in world space (world axes "always shown" and meaningful as an orientation reference);
 * dragging orbits/pans/dollies the *camera* around them. This is the standard trackball-orbit
 * model — implementing it the other way (rotating the object in front of a fixed camera) would
 * leave whichever world axis happens to point along the fixed view direction permanently
 * foreshortened to an unreadable dot, no matter how the user "rotates" the cloud.
 */
export class PointCloudScene {
  private readonly container: HTMLElement;
  private readonly renderer: THREE.WebGLRenderer;
  private readonly scene: THREE.Scene;
  private readonly camera: THREE.PerspectiveCamera;
  private readonly resizeObserver: ResizeObserver;

  private axesGroup: THREE.Group | null = null;
  private gizmoGroup: THREE.Group | null = null;
  private pointsObject: THREE.Points | null = null;
  private cameraFrustums: THREE.LineSegments | null = null;
  private cameraArrows: THREE.LineSegments | null = null;
  private cameraTrajectory: THREE.Line | null = null;
  private poseLabels: THREE.Group | null = null;
  private localizedFrustums: THREE.LineSegments | null = null;
  private localizedAxes: THREE.LineSegments | null = null;
  private localizedLabels: THREE.Group | null = null;

  // The recentering offset setPoints computed (the point cloud's median center) — reused by
  // setLocalizedPoses so overlaid poses line up with the already-recentered scene.
  private recenterOffset = new THREE.Vector3(0, 0, 0);
  private cloudRadius = 1;
  private cameraMode: CameraMode = "frustum";
  private locCameraMode: LocCameraMode = "frustum";
  private pointSize: PointSize = DEFAULT_POINT_SIZE;

  private cameraOrientation = DEFAULT_ORIENTATION.clone();
  private target = new THREE.Vector3(0, 0, 0);
  private distance = 5;
  private initialDistance = 5;
  private minDistance = 0.05;
  private maxDistance = 100;

  private dragButton: number | null = null;
  private lastX = 0;
  private lastY = 0;
  private disposed = false;
  private animationHandle = 0;

  constructor({ container }: PointCloudSceneOptions) {
    this.container = container;

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(SCENE_BACKGROUND_COLOR);

    this.camera = new THREE.PerspectiveCamera(50, 1, 0.001, 100000);

    this.renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(this.renderer.domElement);

    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(container);
    this.resize();
    this.updateCamera();

    this.attachPointerHandlers();
    this.animate();
  }

  setPoints(
    rawPositions: Float32Array,
    rawColors: Uint8Array,
    count: number,
    posePositions: Float32Array = new Float32Array(0),
    poseOrientations: Float32Array = new Float32Array(0),
    poseCount = 0,
  ): void {
    const xs = new Float32Array(count);
    const ys = new Float32Array(count);
    const zs = new Float32Array(count);
    for (let i = 0; i < count; i++) {
      xs[i] = rawPositions[i * 3];
      ys[i] = rawPositions[i * 3 + 1];
      zs[i] = rawPositions[i * 3 + 2];
    }
    const centerX = median(xs);
    const centerY = median(ys);
    const centerZ = median(zs);
    this.recenterOffset.set(centerX, centerY, centerZ);

    // Recenter at load so the cloud's own visual center of mass sits at the world origin — the
    // same point the world axes, gizmo, and orbit target are all anchored to.
    const positions = new Float32Array(rawPositions.length);
    const distances: number[] = new Array(count);
    for (let i = 0; i < count; i++) {
      const x = xs[i] - centerX;
      const y = ys[i] - centerY;
      const z = zs[i] - centerZ;
      positions[i * 3] = x;
      positions[i * 3 + 1] = y;
      positions[i * 3 + 2] = z;
      distances[i] = Math.sqrt(x * x + y * y + z * z);
    }
    // Median + 90th percentile, not max: a handful of stray SfM points far from the map body
    // would otherwise blow out the framing (same rationale as the static PNG renderer).
    this.cloudRadius = percentile(distances, 90) || 1;
    const cloudRadius = this.cloudRadius;

    const colors = new Float32Array(rawColors.length);
    for (let i = 0; i < rawColors.length; i++) colors[i] = rawColors[i] / 255;

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    const material = new THREE.PointsMaterial({ vertexColors: true, sizeAttenuation: true });

    if (this.pointsObject) {
      this.scene.remove(this.pointsObject);
      this.pointsObject.geometry.dispose();
      (this.pointsObject.material as THREE.Material).dispose();
    }
    this.pointsObject = new THREE.Points(geometry, material);
    this.scene.add(this.pointsObject);
    this.setPointSize(this.pointSize);

    if (this.axesGroup) this.scene.remove(this.axesGroup);
    this.axesGroup = buildAxes(cloudRadius * 1.3);
    this.scene.add(this.axesGroup);

    if (this.gizmoGroup) this.scene.remove(this.gizmoGroup);
    this.gizmoGroup = buildGizmo(cloudRadius * 1.15);
    this.gizmoGroup.visible = false;
    this.scene.add(this.gizmoGroup);

    if (this.cameraFrustums) this.scene.remove(this.cameraFrustums);
    if (this.cameraArrows) this.scene.remove(this.cameraArrows);
    if (this.cameraTrajectory) this.scene.remove(this.cameraTrajectory);
    if (this.poseLabels) this.scene.remove(this.poseLabels);
    if (this.localizedFrustums) this.scene.remove(this.localizedFrustums);
    if (this.localizedAxes) this.scene.remove(this.localizedAxes);
    if (this.localizedLabels) this.scene.remove(this.localizedLabels);
    this.cameraFrustums = null;
    this.cameraArrows = null;
    this.cameraTrajectory = null;
    this.poseLabels = null;
    this.localizedFrustums = null;
    this.localizedAxes = null;
    this.localizedLabels = null;
    if (poseCount > 0) {
      const center = new THREE.Vector3(centerX, centerY, centerZ);
      const markerSize = Math.max(cloudRadius * 0.05, 0.005);
      this.cameraFrustums = buildCameraFrustums(posePositions, poseOrientations, poseCount, center, markerSize);
      this.cameraArrows = buildCameraArrows(posePositions, poseOrientations, poseCount, center, markerSize);
      this.cameraTrajectory = buildTrajectory(posePositions, poseCount, center);
      this.poseLabels = buildPoseLabels(posePositions, poseCount, center, markerSize);
      this.scene.add(this.cameraFrustums, this.cameraArrows, this.cameraTrajectory, this.poseLabels);
    }
    this.setCameraMode(this.cameraMode);

    this.distance = cloudRadius * 3;
    this.initialDistance = this.distance;
    this.minDistance = cloudRadius * 0.02;
    this.maxDistance = cloudRadius * 50;
    this.updateCamera();
  }

  recenter(): void {
    this.cameraOrientation.copy(DEFAULT_ORIENTATION);
    this.target.set(0, 0, 0);
    this.distance = this.initialDistance;
    this.updateCamera();
  }

  setPlaneView(rightAxis: Axis, upAxis: Axis): void {
    this.cameraOrientation.copy(planeViewQuaternion(rightAxis, upAxis));
    this.target.set(0, 0, 0);
    this.updateCamera();
  }

  hasCameraPoses(): boolean {
    return this.cameraFrustums !== null;
  }

  setCameraMode(mode: CameraMode): void {
    this.cameraMode = mode;
    if (this.cameraFrustums) this.cameraFrustums.visible = mode === "frustum";
    if (this.cameraArrows) this.cameraArrows.visible = mode === "arrows";
    if (this.cameraTrajectory) this.cameraTrajectory.visible = mode !== "off";
    if (this.poseLabels) this.poseLabels.visible = mode !== "off";
  }

  setPointSize(size: PointSize): void {
    this.pointSize = size;
    if (!this.pointsObject) return;
    if (size === "off") {
      this.pointsObject.visible = false;
      return;
    }
    this.pointsObject.visible = true;
    (this.pointsObject.material as THREE.PointsMaterial).size = Math.max(
      this.cloudRadius * POINT_SIZE_UNIT * size,
      0.0005,
    );
  }

  // Overlays localized query poses (from the Localize tab's "Visualize poses" button, or the
  // Visualize tab's Localizations table) as a distinctly-colored frustum/axes set with a label on
  // every pose — unlike the reconstruction's own camera trail, localized-query counts are
  // typically a handful of images, so no dimming/interval is needed. Positions/orientations must
  // already be in the same world frame as the reconstruction (world_from_camera, xyzw) — see
  // LocalizationImage.position/quaternion_xyzw in the dashboard API. `labels[i]` (typically the
  // image's original results.json index, which can differ from `i` once failed localizations are
  // filtered out) is shown on pose `i`; falls back to `i` itself if omitted.
  setLocalizedPoses(positions: Float32Array, orientations: Float32Array, count: number, labels: string[] = []): void {
    if (this.localizedFrustums) this.scene.remove(this.localizedFrustums);
    if (this.localizedAxes) this.scene.remove(this.localizedAxes);
    if (this.localizedLabels) this.scene.remove(this.localizedLabels);
    this.localizedFrustums = null;
    this.localizedAxes = null;
    this.localizedLabels = null;
    if (count === 0) return;

    // Larger than the reconstruction's own pose markers so a handful of overlaid poses stand out
    // rather than blending into a dense trajectory.
    const markerSize = Math.max(this.cloudRadius * 0.09, 0.01);
    this.localizedFrustums = buildCameraFrustums(
      positions,
      orientations,
      count,
      this.recenterOffset,
      markerSize,
      LOCALIZED_POSE_COLOR,
      1,
    );
    this.localizedAxes = buildCameraArrows(positions, orientations, count, this.recenterOffset, markerSize, 1);
    this.localizedLabels = buildPoseLabels(positions, count, this.recenterOffset, markerSize, 1, (i) => labels[i] ?? String(i));
    this.scene.add(this.localizedFrustums, this.localizedAxes, this.localizedLabels);
    this.setLocCameraMode(this.locCameraMode);
  }

  hasLocalizedPoses(): boolean {
    return this.localizedFrustums !== null;
  }

  setLocCameraMode(mode: LocCameraMode): void {
    this.locCameraMode = mode;
    if (this.localizedFrustums) this.localizedFrustums.visible = mode === "frustum";
    if (this.localizedAxes) this.localizedAxes.visible = mode === "axes";
    if (this.localizedLabels) this.localizedLabels.visible = mode !== "off";
  }

  capturePng(): string {
    this.renderer.render(this.scene, this.camera);
    return this.renderer.domElement.toDataURL("image/png");
  }

  dispose(): void {
    this.disposed = true;
    cancelAnimationFrame(this.animationHandle);
    this.resizeObserver.disconnect();
    this.detachPointerHandlers();
    this.renderer.dispose();
    if (this.renderer.domElement.parentElement === this.container) {
      this.container.removeChild(this.renderer.domElement);
    }
  }

  // Camera position/orientation are both fully determined by (cameraOrientation, target,
  // distance): position = target + (camera-local +Z, i.e. "back") * distance, since a camera
  // looks down its local -Z. Directly assigning camera.quaternion (rather than camera.lookAt)
  // means there is no internal Euler/az-el conversion anywhere, so no gimbal lock is possible.
  private updateCamera(): void {
    const back = new THREE.Vector3(0, 0, 1).applyQuaternion(this.cameraOrientation);
    this.camera.position.copy(this.target).addScaledVector(back, this.distance);
    this.camera.quaternion.copy(this.cameraOrientation);
  }

  private resize(): void {
    const width = this.container.clientWidth || 1;
    const height = this.container.clientHeight || 1;
    this.renderer.setSize(width, height);
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
  }

  private animate = (): void => {
    if (this.disposed) return;
    this.renderer.render(this.scene, this.camera);
    this.animationHandle = requestAnimationFrame(this.animate);
  };

  private handlePointerDown = (event: PointerEvent): void => {
    if (event.button !== 0 && event.button !== 2) return;
    this.dragButton = event.button;
    this.lastX = event.clientX;
    this.lastY = event.clientY;
    this.renderer.domElement.setPointerCapture(event.pointerId);
    if (event.button === 0 && this.gizmoGroup) this.gizmoGroup.visible = true;
  };

  private handlePointerMove = (event: PointerEvent): void => {
    if (this.dragButton === null) return;
    const dx = event.clientX - this.lastX;
    const dy = event.clientY - this.lastY;
    this.lastX = event.clientX;
    this.lastY = event.clientY;

    if (this.dragButton === 0) {
      // Orbit: yaw about the fixed world-up axis, pitch about the camera's current local-right
      // axis. Composed as incremental quaternions (premultiply), never converted to Euler angles,
      // so there is no pole/gimbal singularity at any orientation.
      const cameraRight = new THREE.Vector3(1, 0, 0).applyQuaternion(this.cameraOrientation);
      const qYaw = new THREE.Quaternion().setFromAxisAngle(WORLD_UP, -dx * ROTATE_SPEED);
      const qPitch = new THREE.Quaternion().setFromAxisAngle(cameraRight, -dy * ROTATE_SPEED);
      this.cameraOrientation.premultiply(qPitch).premultiply(qYaw);
      this.updateCamera();
    } else if (this.dragButton === 2) {
      const right = new THREE.Vector3(1, 0, 0).applyQuaternion(this.cameraOrientation);
      const up = new THREE.Vector3(0, 1, 0).applyQuaternion(this.cameraOrientation);
      const panSpeed = this.distance * PAN_SPEED_FACTOR;
      this.target.addScaledVector(right, -dx * panSpeed).addScaledVector(up, dy * panSpeed);
      this.updateCamera();
    }
  };

  private handlePointerUp = (event: PointerEvent): void => {
    if (this.dragButton === 0 && this.gizmoGroup) this.gizmoGroup.visible = false;
    this.dragButton = null;
    if (this.renderer.domElement.hasPointerCapture(event.pointerId)) {
      this.renderer.domElement.releasePointerCapture(event.pointerId);
    }
  };

  private handleWheel = (event: WheelEvent): void => {
    event.preventDefault();
    const factor = Math.exp(event.deltaY * ZOOM_SPEED);
    this.distance = Math.min(this.maxDistance, Math.max(this.minDistance, this.distance * factor));
    this.updateCamera();
  };

  private handleContextMenu = (event: Event): void => {
    event.preventDefault();
  };

  private attachPointerHandlers(): void {
    const el = this.renderer.domElement;
    el.addEventListener("pointerdown", this.handlePointerDown);
    el.addEventListener("pointermove", this.handlePointerMove);
    el.addEventListener("pointerup", this.handlePointerUp);
    el.addEventListener("pointerleave", this.handlePointerUp);
    el.addEventListener("wheel", this.handleWheel, { passive: false });
    el.addEventListener("contextmenu", this.handleContextMenu);
  }

  private detachPointerHandlers(): void {
    const el = this.renderer.domElement;
    el.removeEventListener("pointerdown", this.handlePointerDown);
    el.removeEventListener("pointermove", this.handlePointerMove);
    el.removeEventListener("pointerup", this.handlePointerUp);
    el.removeEventListener("pointerleave", this.handlePointerUp);
    el.removeEventListener("wheel", this.handleWheel);
    el.removeEventListener("contextmenu", this.handleContextMenu);
  }
}
