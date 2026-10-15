import { useEffect, useState, type ReactNode } from "react";
import {
  exportCaptureViews,
  exportPoses,
  exportReconstructionZip,
  getCaptureInfo,
  importPath,
  saveLocalizationImages,
  saveLocalizationTable,
  startLocalize,
  startPoselessReconstruct,
  startReconstruct,
} from "../api";
import type { ImportResult, SphericalOptions, VideoInfo, VideoSettings } from "../api";
import { estimateVideoCapture } from "../api";
import { errorText, joinPath, parentDir, readStored, store, STORAGE_KEYS } from "../storage";
import type { CaptureSession, PoselessImageSet, Reconstruction } from "../types";
import { DirectoryBrowserDialog } from "./DirectoryBrowserDialog";

// ── Shared pieces ───────────────────────────────────────────────────────────

function Modal({ title, busy, onClose, children }: { title: string; busy?: boolean; onClose: () => void; children: ReactNode }) {
  return (
    <div className="dialog-overlay" onClick={() => !busy && onClose()}>
      <div className="dialog" onClick={(e) => e.stopPropagation()}>
        <h3>{title}</h3>
        {children}
      </div>
    </div>
  );
}

function Actions({ busy, disabled, label, busyLabel, onCancel, onSubmit }: {
  busy: boolean;
  disabled?: boolean;
  label: string;
  busyLabel: string;
  onCancel: () => void;
  onSubmit: () => void;
}) {
  return (
    <div className="dialog-actions">
      <button onClick={onCancel} disabled={busy}>
        Cancel
      </button>
      <button className="primary" onClick={onSubmit} disabled={busy || disabled}>
        {busy ? busyLabel : label}
      </button>
    </div>
  );
}

// A server-local path with a Browse… button (folders, or files when `fileExtensions` is given).
function PathField({ label, value, onChange, placeholder, browseTitle, fileExtensions, allowFolders }: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  browseTitle: string;
  fileExtensions?: string[];
  allowFolders?: boolean;
}) {
  const [browsing, setBrowsing] = useState(false);
  const start = fileExtensions ? parentDir(value.trim()) : value.trim() || undefined;
  return (
    <>
      <label>
        {label}
        <div style={{ display: "flex", gap: 8 }}>
          <input type="text" placeholder={placeholder} value={value} onChange={(e) => onChange(e.target.value)} style={{ flex: 1 }} />
          <button type="button" onClick={() => setBrowsing(true)}>
            Browse…
          </button>
        </div>
      </label>
      {browsing && (
        <DirectoryBrowserDialog
          title={browseTitle}
          initialPath={start}
          fileExtensions={fileExtensions}
          allowFolders={allowFolders}
          onSelect={(path) => {
            onChange(path);
            setBrowsing(false);
          }}
          onCancel={() => setBrowsing(false)}
        />
      )}
    </>
  );
}

function useRemembered(key: string, fallback = ""): [string, (value: string) => void] {
  const [value, setValue] = useState(() => readStored(key, fallback));
  return [
    value,
    (next: string) => {
      setValue(next);
      store(key, next);
    },
  ];
}

// Submits `action`; on success calls `onDone` with its result, on failure shows the error in place.
function useSubmit<T>(action: () => Promise<T>, onDone: (result: T) => void) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  async function submit(): Promise<void> {
    setBusy(true);
    setError(null);
    try {
      onDone(await action());
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }
  return { busy, error, submit };
}

const HINT = { fontSize: 13, color: "#a8adb8" } as const;

// howard_test.py's POSELESS_POSE_PRIOR_SIGMA_M: an image folder's synthetic trajectory gets a pose
// prior this weak so that feature matches, not the fake poses, decide the geometry.
const POSELESS_PRIOR_SIGMA_M = 1000;

export function formatOptionValue(value: unknown): string {
  if (Array.isArray(value)) return `${value.length} items`;
  return typeof value === "number" ? String(Number(value.toPrecision(6))) : JSON.stringify(value);
}

export function optionsSummary(r: Reconstruction): string {
  const diff = Object.entries(r.options_diff ?? {});
  return diff.length ? diff.map(([k, v]) => `${k}=${formatOptionValue(v)}`).join(", ") : "default options";
}

// ── Reconstruct a capture ───────────────────────────────────────────────────

// Options that differ between a spherical capture and a camera capture. A camera capture keeps
// ReconstructionOptions' own defaults (core/reconstruction_options.py), the values from before
// spherical captures existed. A spherical capture gets what its best maps were built with:
// twelve narrow views, sequential pairs only between neighbouring views, twice the keypoints, and
// the pose-consistency checks off, because an imported video's poses are a made-up straight line
// that never turns. howard_test.py's SPHERICAL_RECONSTRUCTION_DEFAULTS is the CLI's copy.
interface MatchingOptions {
  maxKeypoints: number;
  maxRotationDeg: number;
  maxTranslationDeg: number;
}

interface ViewOptions {
  layout: string;
  viewFovDeg: number;
  pairing: string;
}

const CAMERA_MATCHING: MatchingOptions = { maxKeypoints: 2500, maxRotationDeg: 25, maxTranslationDeg: 60 };
const SPHERICAL_MATCHING: MatchingOptions = { maxKeypoints: 5000, maxRotationDeg: 180, maxTranslationDeg: 180 };
const SPHERICAL_VIEWS: ViewOptions = { layout: "dodecahedron", viewFovDeg: 80, pairing: "neighbouring" };

const LAYOUTS: { value: string; label: string }[] = [
  { value: "dodecahedron", label: "Dodecahedron — 12 views" },
  { value: "cube", label: "Cube — 6 views" },
  { value: "hexring", label: "Hexring — 6 views" },
  { value: "tetrahedron", label: "Tetrahedron — 4 views" },
];
// Each list starts at the narrowest view that still covers the whole sphere; the second value is
// the one a layout change selects.
const LAYOUT_FOVS: Record<string, number[]> = {
  tetrahedron: [141, 150],
  hexring: [120, 150],
  cube: [110, 120],
  dodecahedron: [75, 80],
};
const PAIRINGS: { value: string; label: string }[] = [
  { value: "neighbouring", label: "Neighbouring views" },
  { value: "all", label: "All views" },
  { value: "same", label: "Same view only" },
];
const KEYPOINT_CHOICES = [2500, 5000, 8000];
const ROTATION_CHOICES = [25, 45, 90, 180];
const TRANSLATION_CHOICES = [60, 90, 180];

const degrees = (value: number): string => (value >= 180 ? "180° (off)" : `${value}°`);

// A list of choices that still shows a value it does not offer, so nothing is silently replaced.
function withValue(choices: number[], value: number): number[] {
  return choices.includes(value) ? choices : [...choices, value].sort((a, b) => a - b);
}

function Choice({ label, value, options, disabled, onChange }: {
  label: string;
  value: string;
  options: { value: string; label: string }[];
  disabled?: boolean;
  onChange: (value: string) => void;
}) {
  return (
    <label style={{ flex: 1 }}>
      {label}
      <select value={disabled ? "" : value} disabled={disabled} onChange={(e) => onChange(e.target.value)}>
        {disabled ? <option value="">—</option> : options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </label>
  );
}

function MatchingFields({ matching, onChange }: { matching: MatchingOptions; onChange: (m: MatchingOptions) => void }) {
  const numbers = (choices: number[], value: number, format: (n: number) => string) =>
    withValue(choices, value).map((n) => ({ value: String(n), label: format(n) }));
  return (
    <>
      <Choice
        label="Max keypoints per image"
        value={String(matching.maxKeypoints)}
        options={numbers(KEYPOINT_CHOICES, matching.maxKeypoints, String)}
        onChange={(v) => onChange({ ...matching, maxKeypoints: Number(v) })}
      />
      <div style={{ display: "flex", gap: 12 }}>
        <Choice
          label="Max rotation disagreement"
          value={String(matching.maxRotationDeg)}
          options={numbers(ROTATION_CHOICES, matching.maxRotationDeg, degrees)}
          onChange={(v) => onChange({ ...matching, maxRotationDeg: Number(v) })}
        />
        <Choice
          label="Max translation direction"
          value={String(matching.maxTranslationDeg)}
          options={numbers(TRANSLATION_CHOICES, matching.maxTranslationDeg, degrees)}
          onChange={(v) => onChange({ ...matching, maxTranslationDeg: Number(v) })}
        />
      </div>
    </>
  );
}

function matchingOptions(matching: MatchingOptions): Record<string, unknown> {
  return {
    max_keypoints_per_image: matching.maxKeypoints,
    pair_vio_em_max_rotation_disagreement_deg: matching.maxRotationDeg,
    pair_vio_em_max_translation_direction_deg: matching.maxTranslationDeg,
  };
}

// Typed fields first, hand-written JSON over the top: the same precedence the CLI gives
// --options-json over its own flags, so the textarea stays the way to win an argument.
function mergedOptions(typed: Record<string, unknown>, optionsJson: string): string {
  const written = optionsJson.trim() ? (JSON.parse(optionsJson) as Record<string, unknown>) : {};
  return JSON.stringify({ ...typed, ...written });
}

export function ReconstructDialog({ captureName, captureId, isSpherical: listedSpherical, siblings, onClose, onStarted }: {
  captureName: string;
  captureId: string;
  // From the capture listing; null or undefined when it could not tell, and then the dialog asks.
  isSpherical: boolean | null | undefined;
  siblings: Reconstruction[];
  onClose: () => void;
  onStarted: (jobId: string) => void;
}) {
  // A capture uploaded from an image folder (before folders were linked to their captures) carries
  // a fabricated straight-line trajectory; its reconstructions were built with the pose prior made
  // negligible, and a new one needs the same or the fake poses would steer bundle adjustment.
  const fromImageFolder = siblings.some((r) => Number(r.options_diff?.pose_prior_position_sigma_m) >= POSELESS_PRIOR_SIGMA_M);
  const [optionsJson, setOptionsJson] = useState(
    fromImageFolder ? JSON.stringify({ pose_prior_position_sigma_m: POSELESS_PRIOR_SIGMA_M }) : "",
  );
  // The listing usually knows whether the capture is spherical. When it does not, the manifest
  // lookup takes several seconds, and Reconstruct waits for it rather than start with the wrong
  // defaults; a failed lookup falls back to a camera capture.
  const [spherical, setSpherical] = useState<boolean | null>(typeof listedSpherical === "boolean" ? listedSpherical : null);
  const [matching, setMatching] = useState<MatchingOptions>(spherical ? SPHERICAL_MATCHING : CAMERA_MATCHING);
  const [views, setViews] = useState<ViewOptions>(SPHERICAL_VIEWS);
  useEffect(() => {
    if (typeof listedSpherical === "boolean") return;
    let live = true;
    const settle = (value: boolean) => {
      if (!live) return;
      setSpherical(value);
      setMatching(value ? SPHERICAL_MATCHING : CAMERA_MATCHING);
    };
    getCaptureInfo(captureId)
      .then((info) => settle(info.is_spherical))
      .catch(() => settle(false));
    return () => {
      live = false;
    };
  }, [captureId, listedSpherical]);

  const { busy, error, submit } = useSubmit(
    () => {
      const typed = {
        ...(spherical
          ? { spherical_layout: views.layout, spherical_view_fov_deg: views.viewFovDeg, spherical_sequential_views: views.pairing }
          : {}),
        ...matchingOptions(matching),
      };
      return startReconstruct(captureId, mergedOptions(typed, optionsJson));
    },
    ({ job_id }) => onStarted(job_id),
  );
  const notSpherical = spherical !== true;
  return (
    <Modal title={`Reconstruct ${captureName}`} busy={busy} onClose={onClose}>
      <div style={{ display: "flex", gap: 12 }}>
        <Choice
          label="Views rendered"
          value={views.layout}
          options={LAYOUTS}
          disabled={notSpherical}
          onChange={(layout) => setViews({ ...views, layout, viewFovDeg: LAYOUT_FOVS[layout]?.at(-1) ?? views.viewFovDeg })}
        />
        <Choice
          label="View FoV"
          value={String(views.viewFovDeg)}
          options={withValue(LAYOUT_FOVS[views.layout] ?? [], views.viewFovDeg).map((n) => ({ value: String(n), label: `${n}°` }))}
          disabled={notSpherical}
          onChange={(v) => setViews({ ...views, viewFovDeg: Number(v) })}
        />
      </div>
      <Choice
        label="View pairing"
        value={views.pairing}
        options={PAIRINGS}
        disabled={notSpherical}
        onChange={(pairing) => setViews({ ...views, pairing })}
      />
      <MatchingFields matching={matching} onChange={setMatching} />
      <label>
        Options (JSON, optional overrides for ReconstructionOptions)
        <textarea rows={4} placeholder='{"ransac_max_error": 2.0}' value={optionsJson} onChange={(e) => setOptionsJson(e.target.value)} />
      </label>
      {siblings.length > 0 && (
        <div style={HINT}>
          Existing reconstructions of this capture:
          <ul style={{ margin: "4px 0 0", paddingLeft: 18 }}>
            {siblings.map((r) => (
              <li key={r.id} className="mono" style={{ fontSize: 12 }}>
                {r.id.slice(0, 8)} ({r.status}): {optionsSummary(r)}
              </li>
            ))}
          </ul>
        </div>
      )}
      {error && <div className="banner banner-error">{error}</div>}
      <Actions
        busy={busy}
        disabled={spherical === null}
        label={spherical === null ? "Checking capture…" : "Reconstruct"}
        busyLabel="Starting…"
        onCancel={onClose}
        onSubmit={() => void submit()}
      />
    </Modal>
  );
}

// ── Reconstruct an image folder (poseless) ──────────────────────────────────

export function PoselessReconstructDialog({ set, onClose, onStarted }: {
  set: PoselessImageSet;
  onClose: () => void;
  onStarted: (jobId: string) => void;
}) {
  const [rememberedFocal, setRememberedFocal] = useRemembered(STORAGE_KEYS.focalLength);
  const [focalLength, setFocalLength] = useState(set.focal_length != null ? String(set.focal_length) : rememberedFocal);
  const [targetKeyframes, setTargetKeyframes] = useState<number | null>(null);
  const [optionsJson, setOptionsJson] = useState("");
  const [matching, setMatching] = useState<MatchingOptions>(CAMERA_MATCHING);
  const focal = Number(focalLength);
  const reuses = set.capture_session_id != null && set.focal_length === focal;
  const { busy, error, submit } = useSubmit(
    () => startPoselessReconstruct(set.id, focal, targetKeyframes, mergedOptions(matchingOptions(matching), optionsJson)),
    ({ job_id }) => onStarted(job_id),
  );
  return (
    <Modal title={`Reconstruct ${set.name}`} busy={busy} onClose={onClose}>
      <label>
        Focal length (pixels, used for both fx and fy)
        <input
          type="number"
          placeholder="e.g. 1350"
          value={focalLength}
          onChange={(e) => {
            setFocalLength(e.target.value);
            setRememberedFocal(e.target.value);
          }}
        />
      </label>
      <label>
        Image usage
        <select
          value={targetKeyframes == null ? "all" : String(targetKeyframes)}
          onChange={(e) => setTargetKeyframes(e.target.value === "all" ? null : Number(e.target.value))}
        >
          <option value="all">Every image in the folder</option>
          <option value="30">Thin to about 30 keyframes</option>
        </select>
      </label>
      <MatchingFields matching={matching} onChange={setMatching} />
      <label>
        Options (JSON, optional overrides for ReconstructionOptions)
        <textarea rows={4} placeholder='{"ransac_max_error": 2.0}' value={optionsJson} onChange={(e) => setOptionsJson(e.target.value)} />
      </label>
      <div style={HINT}>
        {reuses
          ? "Reuses this folder's uploaded capture."
          : set.capture_session_id != null
            ? `The focal length differs from the uploaded capture's (${set.focal_length}), so the folder is uploaded as a new capture.`
            : "The folder is uploaded as a capture first; later reconstructions reuse it."}
      </div>
      {error && <div className="banner banner-error">{error}</div>}
      <Actions
        busy={busy}
        disabled={!focalLength.trim() || !(focal > 0)}
        label="Reconstruct"
        busyLabel="Starting…"
        onCancel={onClose}
        onSubmit={() => void submit()}
      />
    </Modal>
  );
}

// ── Localize images against a reconstruction ────────────────────────────────

export function LocalizeDialog({ reconstructionLabel, reconstructionId, onClose, onStarted }: {
  reconstructionLabel: string;
  reconstructionId: string;
  onClose: () => void;
  onStarted: (runId: string) => void;
}) {
  const [imageDir, setImageDir] = useRemembered(STORAGE_KEYS.localizeImageDir);
  const [useChunking, setUseChunking] = useState(true);
  const [fovDeg, setFovDeg] = useRemembered(STORAGE_KEYS.localizeFovDeg);
  const [detail, setDetail] = useState(true);
  const { busy, error, submit } = useSubmit(
    () => startLocalize(reconstructionId, imageDir.trim(), null, null, useChunking, Number(fovDeg) || null, detail),
    ({ run_id }) => onStarted(run_id),
  );
  return (
    <Modal title={`Localize against ${reconstructionLabel}`} busy={busy} onClose={onClose}>
      <PathField
        label="Image directory"
        value={imageDir}
        onChange={setImageDir}
        placeholder="/path/to/query/images"
        browseTitle="Choose image directory"
      />
      <label>
        Query image field of view (degrees, horizontal)
        <input type="number" placeholder="e.g. 120" value={fovDeg} onChange={(e) => setFovDeg(e.target.value)} />
      </label>
      <div style={{ ...HINT, marginTop: -8 }}>
        The lens the query images were taken with. Leave empty to borrow the map capture's own camera, which is
        right only when the queries came from that same camera; a spherical map has no pinhole camera to borrow.
      </div>
      <label style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
        <input type="checkbox" checked={useChunking} onChange={(e) => setUseChunking(e.target.checked)} />
        Use chunking
      </label>
      <div style={{ ...HINT, marginTop: -8 }}>
        Matches each query image against retrieval candidates in small batches instead of one large batch, capping
        peak GPU memory per image. Recommended; disable only to reproduce the pre-fix behavior for comparison.
      </div>
      <label style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
        <input type="checkbox" checked={detail} onChange={(e) => setDetail(e.target.checked)} />
        Record per-image diagnostics
      </label>
      <div style={{ ...HINT, marginTop: -8 }}>
        Keeps which database images retrieval chose, how each one matched, and where every correspondence landed,
        so each row gets a Details view. Costs roughly 50-200 KB per image on disk; kept for failed queries too,
        which are the ones most worth looking at.
      </div>
      {error && <div className="banner banner-error">{error}</div>}
      <Actions busy={busy} disabled={!imageDir.trim()} label="Run" busyLabel="Starting…" onCancel={onClose} onSubmit={() => void submit()} />
    </Modal>
  );
}

// ── Import: a folder of images, a reconstruction tar, or a spherical video ──

const VIDEO_SUFFIXES = [".mp4", ".mov", ".m4v", ".insv"];

function formatBytes(bytes: number): string {
  if (bytes >= 1e9) return `${(bytes / 1e9).toFixed(2)} GB`;
  if (bytes >= 1e6) return `${Math.round(bytes / 1e6)} MB`;
  return `${Math.round(bytes / 1e3)} kB`;
}

type EstimateState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ok"; info: VideoInfo }
  | { status: "error"; message: string };

/** Price the capture these settings would build, re-asked as the settings change. */
function useCaptureEstimate(path: string, settings: Pick<VideoSettings, "stride" | "maxWidth">): EstimateState {
  const [state, setState] = useState<EstimateState>({ status: "idle" });
  const { stride, maxWidth } = settings;
  useEffect(() => {
    if (!path) {
      setState({ status: "idle" });
      return;
    }
    let live = true;
    setState({ status: "loading" });
    // Each estimate decodes frames, so settle before asking rather than firing per keystroke.
    const timer = setTimeout(() => {
      estimateVideoCapture(path, { stride, maxWidth })
        .then((info) => live && setState({ status: "ok", info }))
        .catch((err: unknown) => live && setState({ status: "error", message: errorText(err) }));
    }, 400);
    return () => {
      live = false;
      clearTimeout(timer);
    };
  }, [path, stride, maxWidth]);
  return state;
}

function CaptureEstimateLine({ estimate }: { estimate: EstimateState }) {
  if (estimate.status === "idle") return null;
  if (estimate.status === "loading") return <div style={{ ...HINT, marginTop: -8 }}>Measuring…</div>;
  if (estimate.status === "error") return <div className="banner banner-error">{estimate.message}</div>;
  const { capture, limit_bytes } = estimate.info;
  if (!capture) {
    return <div className="banner banner-error">This video declares no spherical projection, so it cannot be imported.</div>;
  }
  // The arithmetic in full, so an over-limit setting is visible before it costs an extraction.
  const line = `${capture.frames} frames x ${formatBytes(capture.bytes_per_frame)} at ${capture.width}x${capture.height} = ${formatBytes(capture.total_bytes)}`;
  const limit = `limit ${formatBytes(limit_bytes)}`;
  // Over the limit is not a refusal: import-spherical stores such a capture straight into the stack's
  // storage and creates its row without a body, so the API's request limit never sees it. That path
  // needs the stack's containers on this machine, which the dashboard's development use assumes.
  return capture.over_limit ? (
    <div style={{ ...HINT, marginTop: -8 }}>
      {line} — over the {limit} for an upload through the API, so it will be stored directly in the stack's storage
      instead (development stack only). Halving the width or doubling the stride would bring it under the limit.
    </div>
  ) : (
    <div style={{ ...HINT, marginTop: -8 }}>
      {line} ({limit})
    </div>
  );
}

export function ImportDialog({ onClose, onImported }: {
  onClose: () => void;
  onImported: (result: ImportResult, path: string) => void;
}) {
  const [path, setPath] = useRemembered(STORAGE_KEYS.importTar);
  const [newId, setNewId] = useState(false);
  const [stride, setStride] = useState("");
  const [maxWidth, setMaxWidth] = useState("");
  const settings: VideoSettings = {
    stride: Number(stride) || null,
    maxWidth: maxWidth === "" ? null : Number(maxWidth),
  };
  const { busy, error, submit } = useSubmit(
    () => importPath(path.trim(), newId, settings),
    (result) => onImported(result, path.trim()),
  );
  const trimmed = path.trim().toLowerCase();
  const isTar = trimmed.endsWith(".tar");
  const isVideo = VIDEO_SUFFIXES.some((suffix) => trimmed.endsWith(suffix));
  const estimate = useCaptureEstimate(isVideo ? path.trim() : "", settings);
  return (
    <Modal title="Import" busy={busy} onClose={onClose}>
      <PathField
        label="Folder or file"
        value={path}
        onChange={setPath}
        placeholder="/path/to/images, /path/to/reconstruction.tar, or /path/to/360-video.mp4"
        browseTitle="Choose a folder or file to import"
        fileExtensions={[".tar", ".mp4", ".mov", ".m4v", ".insv"]}
        allowFolders
      />
      <div style={HINT}>
        <ul style={{ margin: 0, paddingLeft: 18 }}>
          <li>
            <b>A folder of images</b> — sequentially ordered stills with no poses. Registered here, then reconstructed
            from its row with a focal length you supply.
          </li>
          <li>
            <b>A capture tar</b> — <span className="mono">manifest.json</span> plus the frames, as a device
            records them. It lands in the tree ready to reconstruct, like one uploaded from a phone.
          </li>
          <li>
            <b>A reconstruction tar</b> — <span className="mono">metadata.json</span> plus a reconstruction's
            artifacts, as produced by an export. It arrives ready to localize against, under its own capture.
          </li>
          <li>
            <b>A spherical (360) video</b> — its frames become a capture and a reconstruction starts straight away.
            The video has to declare that it is spherical; an ordinary video is not supported yet.
          </li>
        </ul>
      </div>
      {isVideo && (
        <>
          <div style={{ display: "flex", gap: 12 }}>
            <label style={{ flex: 1 }}>
              Keep every Nth frame
              <input type="number" min={1} placeholder="5" value={stride} onChange={(e) => setStride(e.target.value)} />
            </label>
            <label style={{ flex: 1 }}>
              Max frame width (0 = camera's own)
              <input type="number" min={0} placeholder="3840" value={maxWidth} onChange={(e) => setMaxWidth(e.target.value)} />
            </label>
          </div>
          <div style={{ ...HINT, marginTop: -8 }}>
            These are the capture: which frames it keeps, and how wide they are. Importing stops there — the views a
            sphere is cut into are chosen when you reconstruct it, and again when you export the views themselves, so
            one import can serve several of each.
          </div>
          <CaptureEstimateLine estimate={estimate} />
        </>
      )}
      {isTar && (
        <label style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
          <input type="checkbox" checked={newId} onChange={(e) => setNewId(e.target.checked)} />
          Import as a separate copy
        </label>
      )}
      {isTar && (
        <div style={{ ...HINT, marginTop: -8 }}>
          A reconstruction tar carries one fixed id, so it imports once; tick the box to import it again alongside
          the existing one.
          Importing also creates the reconstruction's localization map; removing the reconstruction later needs that
          map deleted first.
        </div>
      )}
      {error && <div className="banner banner-error">{error}</div>}
      <Actions busy={busy} disabled={!path.trim()} label="Import" busyLabel="Importing…" onCancel={onClose} onSubmit={() => void submit()} />
    </Modal>
  );
}

// ── Export a reconstruction: zip archive, or its poses as localization-format JSON ─

export type ExportKind = "zip" | "poses";

export function ExportDialog({ kind, reconstruction, onClose, onDone }: {
  kind: ExportKind;
  reconstruction: Reconstruction;
  onClose: () => void;
  onDone: (message: string) => void;
}) {
  const [dir, setDir] = useRemembered(kind === "zip" ? STORAGE_KEYS.exportZipDir : STORAGE_KEYS.exportPosesDir);
  const [filename, setFilename] = useState(kind === "zip" ? `${reconstruction.id}.zip` : "poses.json");
  const outputPath = joinPath(dir.trim(), filename.trim());
  const { busy, error, submit } = useSubmit<string>(
    async () => {
      if (kind === "zip") {
        const result = await exportReconstructionZip(reconstruction.id, outputPath);
        return `Exported ${result.file_count} files to ${result.output_path}`;
      }
      const result = await exportPoses(reconstruction.id, outputPath);
      return `Wrote ${result.count} pose(s) to ${result.output_path}`;
    },
    onDone,
  );
  return (
    <Modal title={kind === "zip" ? "Export reconstruction as .zip" : "Export poses as JSON"} busy={busy} onClose={onClose}>
      <div style={HINT}>
        {kind === "zip"
          ? "The map data (point cloud, camera poses, features) of "
          : "The map's own camera poses, in the same JSON shape as a localization run's results (e.g. as ground truth), from "}
        <span className="mono">{reconstruction.id}</span>.
      </div>
      <PathField label="Output directory" value={dir} onChange={setDir} placeholder="/path/to/output/dir" browseTitle="Choose output directory" />
      <label>
        Output filename
        <input type="text" value={filename} onChange={(e) => setFilename(e.target.value)} />
      </label>
      {error && <div className="banner banner-error">{error}</div>}
      <Actions
        busy={busy}
        disabled={!dir.trim() || !filename.trim()}
        label="Export"
        busyLabel="Exporting…"
        onCancel={onClose}
        onSubmit={() => void submit()}
      />
    </Modal>
  );
}

// ── Export a spherical capture's rendered views ─────────────────────────────

// Rendering belongs to the capture: which views exist is decided by the layout and field of view
// alone, so a reconstruction of it has no say and every reconstruction would render the same images.
// The views a spherical reconstruction renders by default; view size is ReconstructionOptions' own.
const EXPORT_VIEWS: SphericalOptions = {
  layout: SPHERICAL_VIEWS.layout,
  viewFovDeg: SPHERICAL_VIEWS.viewFovDeg,
  viewSize: 1600,
  sequentialViews: SPHERICAL_VIEWS.pairing,
};

export function ExportViewsDialog({ capture, onClose, onDone }: {
  capture: CaptureSession;
  onClose: () => void;
  onDone: (message: string) => void;
}) {
  const [dir, setDir] = useRemembered(STORAGE_KEYS.exportViewsDir);
  const [folder, setFolder] = useState(`${capture.name}-views`);
  const [spherical, setSpherical] = useState<SphericalOptions>(EXPORT_VIEWS);
  const outputDir = joinPath(dir.trim(), folder.trim());
  const { busy, error, submit } = useSubmit<string>(async () => {
    const result = await exportCaptureViews(capture.id, outputDir, spherical);
    return `Rendered ${result.images} image(s) of ${result.frames} frame(s) across ${result.views.length} view(s) (${result.layout}, ${result.view_fov_deg}°, ${result.size}px) to ${result.output_dir}`;
  }, onDone);
  return (
    <Modal title={`Export views of ${capture.name}`} busy={busy} onClose={onClose}>
      <div style={HINT}>
        One folder per view, plus a cameras.json giving the shared fisheye intrinsics and where each view points. Every
        frame the capture holds is rendered; no reconstruction is involved, so this works before you have one.
      </div>
      <div style={{ display: "flex", gap: 12 }}>
        <label style={{ flex: 1 }}>
          Views rendered from each sphere
          <select value={spherical.layout} onChange={(e) => setSpherical({ ...spherical, layout: e.target.value })}>
            <option value="tetrahedron">Tetrahedron — 4 views, covers the sphere at 141°+</option>
            <option value="hexring">Hexring — 6 level-ish views, better for level queries</option>
            <option value="cube">Cube — 6 faces, covers the sphere at 110°+</option>
            <option value="dodecahedron">Dodecahedron — 12 narrow views, Zed-like resolution at 75°</option>
          </select>
        </label>
        <label style={{ width: 110 }}>
          View field of view
          <input
            type="number"
            min={1}
            max={179}
            value={spherical.viewFovDeg}
            onChange={(e) => setSpherical({ ...spherical, viewFovDeg: Number(e.target.value) })}
          />
        </label>
        <label style={{ width: 110 }}>
          View size (px)
          <input
            type="number"
            min={64}
            value={spherical.viewSize}
            onChange={(e) => setSpherical({ ...spherical, viewSize: Number(e.target.value) })}
          />
        </label>
      </div>
      <PathField label="Output directory" value={dir} onChange={setDir} placeholder="/path/to/output/dir" browseTitle="Choose output directory" />
      <label>
        Output folder name
        <input type="text" value={folder} onChange={(e) => setFolder(e.target.value)} />
      </label>
      {error && <div className="banner banner-error">{error}</div>}
      <Actions
        busy={busy}
        disabled={!dir.trim() || !folder.trim()}
        label="Export"
        busyLabel="Rendering…"
        onCancel={onClose}
        onSubmit={() => void submit()}
      />
    </Modal>
  );
}

// ── Save a localization run's table (CSV) or annotated images ───────────────

export function SaveRunDialog({ kind, runId, onClose, onDone }: {
  kind: "table" | "images";
  runId: string;
  onClose: () => void;
  onDone: (message: string, tone: "success" | "error") => void;
}) {
  const [path, setPath] = useState("");
  const { busy, error, submit } = useSubmit<[string, "success" | "error"]>(
    async () => {
      if (kind === "table") {
        const { output_path, count } = await saveLocalizationTable(runId, path.trim());
        return [`Saved ${count} rows to ${output_path}`, "success"];
      }
      // Annotating redraws each original image, so images whose source file is gone (a moved or
      // deleted query folder) are skipped — a save of nothing is reported as a failure, not a tick.
      const { output_dir, count, missing } = await saveLocalizationImages(runId, path.trim());
      const skipped = missing ? ` (${missing} source image${missing === 1 ? "" : "s"} no longer exist)` : "";
      return count === 0
        ? [`No images saved${skipped || " — the run has no images"}.`, "error"]
        : [`Saved ${count} annotated images to ${output_dir}${skipped}`, "success"];
    },
    ([message, tone]) => onDone(message, tone),
  );
  return (
    <Modal title={kind === "table" ? "Save table to CSV" : "Save annotated images to directory"} busy={busy} onClose={onClose}>
      {kind === "table" ? (
        <label>
          Output file path
          <input type="text" placeholder="/path/to/table.csv" value={path} onChange={(e) => setPath(e.target.value)} autoFocus />
        </label>
      ) : (
        <PathField label="Output directory" value={path} onChange={setPath} placeholder="/path/to/output_dir" browseTitle="Choose output directory" />
      )}
      {error && <div className="banner banner-error">{error}</div>}
      <Actions busy={busy} disabled={!path.trim()} label="Save" busyLabel="Saving…" onCancel={onClose} onSubmit={() => void submit()} />
    </Modal>
  );
}

// ── Confirm a deletion ──────────────────────────────────────────────────────

export function ConfirmDialog({ title, label, busyLabel, children, onClose, onConfirm }: {
  title: string;
  label: string;
  busyLabel: string;
  children: ReactNode;
  onClose: () => void;
  onConfirm: () => Promise<void>;
}) {
  const { busy, error, submit } = useSubmit(onConfirm, onClose);
  return (
    <Modal title={title} busy={busy} onClose={onClose}>
      <p style={{ margin: 0 }}>{children}</p>
      {error && <div className="banner banner-error">{error}</div>}
      <Actions busy={busy} label={label} busyLabel={busyLabel} onCancel={onClose} onSubmit={() => void submit()} />
    </Modal>
  );
}

export function ConfirmDeleteDialog({ title, children, onClose, onConfirm }: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  onConfirm: () => Promise<void>;
}) {
  return (
    <ConfirmDialog title={title} label="Delete" busyLabel="Deleting…" onClose={onClose} onConfirm={onConfirm}>
      {children}
    </ConfirmDialog>
  );
}
