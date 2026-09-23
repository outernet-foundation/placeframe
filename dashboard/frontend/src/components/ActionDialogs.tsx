import { useState, type ReactNode } from "react";
import {
  exportPoses,
  exportReconstructionZip,
  importPath,
  saveLocalizationImages,
  saveLocalizationTable,
  startLocalize,
  startPoselessReconstruct,
  startReconstruct,
} from "../api";
import type { ImportResult } from "../api";
import { errorText, joinPath, parentDir, readStored, store, STORAGE_KEYS } from "../storage";
import type { PoselessImageSet, Reconstruction } from "../types";
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

export function ReconstructDialog({ captureName, captureId, siblings, onClose, onStarted }: {
  captureName: string;
  captureId: string;
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
  const { busy, error, submit } = useSubmit(
    () => startReconstruct(captureId, optionsJson.trim() || null),
    ({ job_id }) => onStarted(job_id),
  );
  return (
    <Modal title={`Reconstruct ${captureName}`} busy={busy} onClose={onClose}>
      <label>
        Options (JSON, optional overrides for ReconstructionOptions)
        <textarea rows={6} placeholder='{"ransac_max_error": 2.0}' value={optionsJson} onChange={(e) => setOptionsJson(e.target.value)} />
      </label>
      {fromImageFolder && (
        <div style={HINT}>
          This capture was uploaded from an image folder, so its poses are synthetic: the pose prior is pre-set to be
          negligible, as in its earlier reconstructions.
        </div>
      )}
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
      <Actions busy={busy} label="Reconstruct" busyLabel="Starting…" onCancel={onClose} onSubmit={() => void submit()} />
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
  const focal = Number(focalLength);
  const reuses = set.capture_session_id != null && set.focal_length === focal;
  const { busy, error, submit } = useSubmit(
    () => startPoselessReconstruct(set.id, focal, targetKeyframes, optionsJson.trim() || null),
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
  const { busy, error, submit } = useSubmit(
    () => startLocalize(reconstructionId, imageDir.trim(), null, null, useChunking),
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
      <label style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
        <input type="checkbox" checked={useChunking} onChange={(e) => setUseChunking(e.target.checked)} />
        Use chunking
      </label>
      <div style={{ ...HINT, marginTop: -8 }}>
        Matches each query image against retrieval candidates in small batches instead of one large batch, capping
        peak GPU memory per image. Recommended; disable only to reproduce the pre-fix behavior for comparison.
      </div>
      {error && <div className="banner banner-error">{error}</div>}
      <Actions busy={busy} disabled={!imageDir.trim()} label="Run" busyLabel="Starting…" onCancel={onClose} onSubmit={() => void submit()} />
    </Modal>
  );
}

// ── Import: a folder of images, a reconstruction tar, or a spherical video ──

export function ImportDialog({ onClose, onImported }: {
  onClose: () => void;
  onImported: (result: ImportResult, path: string) => void;
}) {
  const [path, setPath] = useRemembered(STORAGE_KEYS.importTar);
  const [newId, setNewId] = useState(false);
  const { busy, error, submit } = useSubmit(
    () => importPath(path.trim(), newId),
    (result) => onImported(result, path.trim()),
  );
  const isTar = path.trim().toLowerCase().endsWith(".tar");
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
            <b>A reconstruction tar</b> — <span className="mono">metadata.json</span> plus a reconstruction's
            artifacts, as produced by an export. It arrives ready to localize against, under its own capture.
          </li>
          <li>
            <b>A spherical (360) video</b> — its frames become a capture and a reconstruction starts straight away.
            The video has to declare that it is spherical; an ordinary video is not supported yet.
          </li>
        </ul>
      </div>
      {isTar && (
        <label style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
          <input type="checkbox" checked={newId} onChange={(e) => setNewId(e.target.checked)} />
          Import as a separate copy
        </label>
      )}
      {isTar && (
        <div style={{ ...HINT, marginTop: -8 }}>
          A tar carries one fixed id, so it imports once; tick the box to import it again alongside the existing one.
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

export function ConfirmDeleteDialog({ title, children, onClose, onConfirm }: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  onConfirm: () => Promise<void>;
}) {
  const { busy, error, submit } = useSubmit(onConfirm, onClose);
  return (
    <Modal title={title} busy={busy} onClose={onClose}>
      <p style={{ margin: 0 }}>{children}</p>
      {error && <div className="banner banner-error">{error}</div>}
      <Actions busy={busy} label="Delete" busyLabel="Deleting…" onCancel={onClose} onSubmit={() => void submit()} />
    </Modal>
  );
}
