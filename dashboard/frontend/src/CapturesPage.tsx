import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import {
  deleteCapture,
  deleteLocalization,
  deleteReconstruction,
  getJob,
  listCaptures,
  listLocalizations,
  listPoselessSets,
  listReconstructions,
  renameCapture,
  renamePoselessSet,
} from "./api";
import {
  ConfirmDeleteDialog,
  ExportDialog,
  ImportDialog,
  LocalizeDialog,
  optionsSummary,
  PoselessReconstructDialog,
  ReconstructDialog,
  SaveRunDialog,
  type ExportKind,
} from "./components/ActionDialogs";
import { Menu } from "./components/Menu";
import { RunResults } from "./components/RunResults";
import { errorText, readStored, store, STORAGE_KEYS } from "./storage";
import type { CaptureSession, LocalizationSummary, PoselessImageSet, Reconstruction } from "./types";
import { TERMINAL_STATUSES } from "./types";

// One page, one tree: capture → its reconstructions (one per set of options) → each
// reconstruction's localization runs. Captures and reconstructions come from the API; runs are the
// local data/localizations/* results, which record their reconstruction. The tree polls while any
// reconstruction or run is in progress.

type Dialog =
  | { kind: "reconstruct"; capture: CaptureSession }
  | { kind: "poseless"; set: PoselessImageSet }
  | { kind: "localize"; reconstruction: Reconstruction; label: string }
  | { kind: "import" }
  | { kind: "export"; exportKind: ExportKind; reconstruction: Reconstruction }
  | { kind: "save"; saveKind: "table" | "images"; runId: string }
  | { kind: "deleteReconstruction"; reconstruction: Reconstruction }
  | { kind: "deleteSelection" };

// Selection keys are type-tagged so one set can hold all three kinds of row.
type SelectionKey = `capture:${string}` | `reconstruction:${string}` | `run:${string}`;

interface Notice {
  id: number;
  tone: "success" | "error";
  text: string;
}

type FrameStats = Pick<Reconstruction, "is_stereo" | "total_frame_count">;

// Failed/cancelled only: a succeeded reconstruction has (or soon gets) a localization map, and the
// API refuses to delete a reconstruction while one exists.
const DELETABLE_STATUSES = new Set(["failed", "cancelled"]);
const POLL_MS = 3000;

function formatSize(bytes: number): string {
  const units = ["B", "KB", "MB", "GB"];
  let size = bytes;
  let unit = 0;
  while (size >= 1024 && unit < units.length - 1) {
    size /= 1024;
    unit += 1;
  }
  return `${size.toFixed(1)} ${units[unit]}`;
}

function formatDate(iso: string | null): string {
  return iso ? new Date(iso).toLocaleString() : "—";
}

function openViewer(reconstructionId: string, runId?: string): void {
  const query = runId ? `reconstruction=${reconstructionId}&localization=${runId}` : `reconstruction=${reconstructionId}`;
  window.open(`/viewer?${query}`, "_blank", "width=1280,height=900");
}

function readExpanded(): Record<string, boolean> {
  try {
    return JSON.parse(readStored(STORAGE_KEYS.expanded, "{}")) as Record<string, boolean>;
  } catch {
    return {};
  }
}

function Toggle({ open, onClick }: { open: boolean; onClick: () => void }) {
  return (
    <button className="toggle" onClick={onClick} aria-expanded={open}>
      {open ? "▾" : "▸"}
    </button>
  );
}

type Renaming = { kind: "capture" | "set"; id: string; value: string } | null;

// Click-to-edit name, opened by the pencil: Enter or blur saves, Escape abandons. Module-level so
// editing doesn't remount the input (and drop focus) on each keystroke.
function NameField({ kind, id, name, renaming, setRenaming, commit }: {
  kind: "capture" | "set";
  id: string;
  name: string;
  renaming: Renaming;
  setRenaming: (value: Renaming) => void;
  commit: () => void;
}) {
  if (renaming?.id === id) {
    return (
      <input
        autoFocus
        // Preselected so typing replaces the name, rather than inserting at the click position.
        onFocus={(e) => e.target.select()}
        value={renaming.value}
        onChange={(e) => setRenaming({ kind, id, value: e.target.value })}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === "Enter") commit();
          if (e.key === "Escape") setRenaming(null);
        }}
      />
    );
  }
  return (
    <>
      <span className="node-name">{name}</span>
      <button className="pencil" onClick={() => setRenaming({ kind, id, value: name })} title="Rename" aria-label="Rename">
        ✎
      </button>
    </>
  );
}

const sleep = (ms: number) => new Promise((resolve) => window.setTimeout(resolve, ms));

export function CapturesPage() {
  const [captures, setCaptures] = useState<CaptureSession[]>([]);
  const [reconstructions, setReconstructions] = useState<Reconstruction[]>([]);
  const [runs, setRuns] = useState<LocalizationSummary[]>([]);
  const [sets, setSets] = useState<PoselessImageSet[]>([]);
  const [frameStats, setFrameStats] = useState<Record<string, FrameStats>>({});
  const [loaded, setLoaded] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [pendingJobs, setPendingJobs] = useState(0);

  const [dialog, setDialog] = useState<Dialog | null>(null);
  const [notices, setNotices] = useState<Notice[]>([]);
  const [expanded, setExpanded] = useState<Record<string, boolean>>(readExpanded);
  const [resultsOpen, setResultsOpen] = useState<Set<string>>(new Set());
  // Inline rename, for a capture (the API's own name) or an unlinked image folder (local only).
  const [renaming, setRenaming] = useState<Renaming>(null);
  const [selecting, setSelecting] = useState(false);
  const [selected, setSelected] = useState<Set<SelectionKey>>(new Set());
  const nextNoticeId = useRef(0);

  function notify(tone: Notice["tone"], text: string): void {
    const id = nextNoticeId.current++;
    setNotices((n) => [...n, { id, tone, text }]);
  }

  // ── Loading ───────────────────────────────────────────────────────────────

  const refreshFast = useCallback(async (): Promise<void> => {
    const [c, r, l, s] = await Promise.all([listCaptures(), listReconstructions(false), listLocalizations(), listPoselessSets()]);
    setCaptures(c);
    setReconstructions(r);
    setRuns(l);
    setSets(s);
    setLoaded(true);
    setLoadError(null);
  }, []);

  // Mono/stereo and frame counts need a slow per-capture lookup, so they arrive after the tree.
  const refreshStats = useCallback(async (): Promise<void> => {
    try {
      const full = await listReconstructions(true);
      setFrameStats(Object.fromEntries(full.map((r) => [r.id, { is_stereo: r.is_stereo, total_frame_count: r.total_frame_count }])));
    } catch {
      // Columns stay "—"; the tree itself is unaffected.
    }
  }, []);

  const refreshAll = useCallback(async (): Promise<void> => {
    setRefreshing(true);
    try {
      await refreshFast();
    } catch (err) {
      setLoadError(errorText(err));
    } finally {
      setRefreshing(false);
    }
    void refreshStats();
  }, [refreshFast, refreshStats]);

  useEffect(() => {
    void refreshAll();
  }, [refreshAll]);

  const active =
    pendingJobs > 0 || reconstructions.some((r) => !TERMINAL_STATUSES.has(r.status)) || runs.some((r) => r.status === "running");

  useEffect(() => {
    if (!active) return;
    const timer = window.setTimeout(() => void refreshFast().catch(() => undefined), POLL_MS);
    return () => window.clearTimeout(timer);
  }, [active, reconstructions, runs, refreshFast]);

  // A reconstruction that just succeeded has a new frame count to fetch.
  const lastStatuses = useRef<Record<string, string>>({});
  useEffect(() => {
    const finished = reconstructions.some((r) => r.status === "succeeded" && lastStatuses.current[r.id] && lastStatuses.current[r.id] !== "succeeded");
    lastStatuses.current = Object.fromEntries(reconstructions.map((r) => [r.id, r.status]));
    if (finished) void refreshStats();
  }, [reconstructions, refreshStats]);

  // A reconstruct job first creates the reconstruction (a poseless one uploads its capture first);
  // follow it until the reconstruction exists — the tree takes over from there — or it fails.
  async function followJob(jobId: string): Promise<void> {
    setPendingJobs((n) => n + 1);
    try {
      for (let i = 0; i < 300; i++) {
        const job = await getJob(jobId);
        if (job.status === "failed") {
          notify("error", `Reconstruction could not start: ${job.error ?? "unknown error"}`);
          break;
        }
        if (job.reconstruction_id) break;
        await sleep(1000);
      }
      await refreshFast();
    } catch (err) {
      notify("error", errorText(err));
    } finally {
      setPendingJobs((n) => n - 1);
    }
  }

  // ── Tree structure ────────────────────────────────────────────────────────

  const tree = useMemo(() => {
    const captureIds = new Set(captures.map((c) => c.id));
    const setByCapture = new Map<string, PoselessImageSet>();
    const pendingSets: PoselessImageSet[] = [];
    for (const s of sets) {
      if (s.capture_session_id && captureIds.has(s.capture_session_id)) setByCapture.set(s.capture_session_id, s);
      else pendingSets.push(s);
    }
    const byCapture = new Map<string, Reconstruction[]>();
    const orphanReconstructions: Reconstruction[] = [];
    for (const r of [...reconstructions].sort((a, b) => b.created_at.localeCompare(a.created_at))) {
      if (r.capture_session_id && captureIds.has(r.capture_session_id)) {
        byCapture.set(r.capture_session_id, [...(byCapture.get(r.capture_session_id) ?? []), r]);
      } else orphanReconstructions.push(r);
    }
    const reconstructionIds = new Set(reconstructions.map((r) => r.id));
    const byReconstruction = new Map<string, LocalizationSummary[]>();
    const orphanRuns: LocalizationSummary[] = [];
    for (const run of runs) {
      if (run.reconstruction_id && reconstructionIds.has(run.reconstruction_id)) {
        byReconstruction.set(run.reconstruction_id, [...(byReconstruction.get(run.reconstruction_id) ?? []), run]);
      } else orphanRuns.push(run);
    }
    const sortedCaptures = [...captures].sort((a, b) => b.recorded_at.localeCompare(a.recorded_at));
    return { sortedCaptures, setByCapture, pendingSets, byCapture, orphanReconstructions, byReconstruction, orphanRuns };
  }, [captures, reconstructions, runs, sets]);

  function isOpen(id: string, byDefault: boolean): boolean {
    return expanded[id] ?? byDefault;
  }

  function setOpen(id: string, open: boolean): void {
    setExpanded((current) => {
      const next = { ...current, [id]: open };
      store(STORAGE_KEYS.expanded, JSON.stringify(next));
      return next;
    });
  }

  function toggleResults(runId: string): void {
    setResultsOpen((current) => {
      const next = new Set(current);
      if (next.has(runId)) next.delete(runId);
      else next.add(runId);
      return next;
    });
  }

  const captureName = (id: string | null) => captures.find((c) => c.id === id)?.name ?? "unknown capture";
  const reconstructionLabel = (r: Reconstruction) => `${captureName(r.capture_session_id)} · ${r.id.slice(0, 8)}`;

  async function commitRename(): Promise<void> {
    if (!renaming) return;
    const { kind, id, value } = renaming;
    setRenaming(null);
    if (!value.trim()) return;
    try {
      await (kind === "capture" ? renameCapture(id, value.trim()) : renamePoselessSet(id, value.trim()));
      await refreshFast();
    } catch (err) {
      notify("error", errorText(err));
    }
  }

  // ── Selection ─────────────────────────────────────────────────────────────

  function toggleSelected(key: SelectionKey): void {
    setSelected((current) => {
      const next = new Set(current);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  }

  function endSelecting(): void {
    setSelecting(false);
    setSelected(new Set());
  }

  // What a delete of the current selection would remove. A selected capture takes its
  // reconstructions (and their runs) with it, and a selected reconstruction takes its runs, so
  // those are dropped from the explicit lists and counted as cascaded instead.
  const plan = useMemo(() => {
    const captureIds = [...selected].filter((k) => k.startsWith("capture:")).map((k) => k.slice(8));
    const coveredReconstructions = new Set(captureIds.flatMap((id) => (tree.byCapture.get(id) ?? []).map((r) => r.id)));
    const reconstructionIds = [...selected]
      .filter((k) => k.startsWith("reconstruction:"))
      .map((k) => k.slice(15))
      .filter((id) => !coveredReconstructions.has(id));
    const allReconstructions = [...coveredReconstructions, ...reconstructionIds];
    const coveredRuns = new Set(allReconstructions.flatMap((id) => (tree.byReconstruction.get(id) ?? []).map((r) => r.run_id)));
    const runIds = [...selected]
      .filter((k) => k.startsWith("run:"))
      .map((k) => k.slice(4))
      .filter((id) => !coveredRuns.has(id));
    return {
      captureIds,
      reconstructionIds,
      runIds,
      cascadedReconstructions: coveredReconstructions.size,
      cascadedRuns: coveredRuns.size,
      total: captureIds.length + reconstructionIds.length + runIds.length,
    };
  }, [selected, tree]);

  // Runs first, then reconstructions, then captures: each level is a dependency of the next, and
  // deleting a child twice (once explicitly, once by cascade) would 404 the second time.
  async function deleteSelection(): Promise<void> {
    const failures: string[] = [];
    for (const runId of plan.runIds) {
      await deleteLocalization(runId).catch((err: unknown) => failures.push(`run ${runId.slice(0, 8)}: ${errorText(err)}`));
    }
    for (const id of plan.reconstructionIds) {
      await deleteReconstruction(id, true).catch((err: unknown) =>
        failures.push(`reconstruction ${id.slice(0, 8)}: ${errorText(err)}`),
      );
    }
    for (const id of plan.captureIds) {
      await deleteCapture(id, true).catch((err: unknown) => failures.push(`capture ${id.slice(0, 8)}: ${errorText(err)}`));
    }
    await refreshFast();
    endSelecting();
    if (failures.length) notify("error", `Could not delete ${failures.length} item(s) — ${failures.join("; ")}`);
    else notify("success", `Deleted ${plan.total} item${plan.total === 1 ? "" : "s"}.`);
  }

  function Check({ selectionKey }: { selectionKey: SelectionKey }) {
    if (!selecting) return null;
    return (
      <input
        type="checkbox"
        className="node-check"
        checked={selected.has(selectionKey)}
        onChange={() => toggleSelected(selectionKey)}
        aria-label="Select for deletion"
      />
    );
  }

  // ── Rows ──────────────────────────────────────────────────────────────────

  function captureNode(c: CaptureSession): ReactNode {
    const set = tree.setByCapture.get(c.id);
    const children = tree.byCapture.get(c.id) ?? [];
    const imported = c.size_bytes === 0 && !set;
    const open = isOpen(c.id, children.length > 0);
    return (
      <div className="node node-capture" key={c.id}>
        <div className="node-row">
          <Check selectionKey={`capture:${c.id}`} />
          <Toggle open={open} onClick={() => setOpen(c.id, !open)} />
          <div className="node-main">
            <div className="node-title">
              <NameField
                kind="capture"
                id={c.id}
                name={c.name}
                renaming={renaming}
                setRenaming={setRenaming}
                commit={() => void commitRename()}
              />
              <span className="badge">{imported ? "Imported" : set ? "Image folder" : c.device_type}</span>
              <span className="node-count">
                {children.length} reconstruction{children.length === 1 ? "" : "s"}
              </span>
            </div>
            <div className="node-meta" title={c.id}>
              {set
                ? `${set.image_count} images · f = ${set.focal_length ?? "?"} px · ${set.path}`
                : imported
                  ? "Reconstruction imported from a tar; no capture data"
                  : `${formatSize(c.size_bytes)} · recorded ${formatDate(c.recorded_at)}`}
              <span className="mono"> · {c.id.slice(0, 8)}</span>
            </div>
          </div>
          <div className="node-actions">
            {set ? (
              <button onClick={() => setDialog({ kind: "poseless", set })}>Reconstruct…</button>
            ) : (
              !imported && <button onClick={() => setDialog({ kind: "reconstruct", capture: c })}>Reconstruct…</button>
            )}
          </div>
        </div>
        {open && (
          <div className="node-children">
            {children.map(reconstructionNode)}
            {children.length === 0 && <div className="node-empty">Not reconstructed yet.</div>}
          </div>
        )}
      </div>
    );
  }

  function pendingSetNode(s: PoselessImageSet): ReactNode {
    return (
      <div className="node node-capture" key={s.id}>
        <div className="node-row">
          <span className="toggle-spacer" />
          <div className="node-main">
            <div className="node-title">
              <NameField
                kind="set"
                id={s.id}
                name={s.name}
                renaming={renaming}
                setRenaming={setRenaming}
                commit={() => void commitRename()}
              />
              <span className="badge">Image folder</span>
              <span className="node-count">no linked capture yet</span>
            </div>
            <div className="node-meta">
              {s.image_count} images · {s.path}
            </div>
          </div>
          <div className="node-actions">
            <button onClick={() => setDialog({ kind: "poseless", set: s })}>Reconstruct…</button>
          </div>
        </div>
      </div>
    );
  }

  function statusChip(status: string, queue?: { position: number | null; depth: number | null }): ReactNode {
    const tone = status === "succeeded" || status === "done" ? "ok" : TERMINAL_STATUSES.has(status) || status === "failed" || status === "incomplete" ? "bad" : "busy";
    const text = status === "queued" && queue?.position != null ? `queued ${queue.position}/${queue.depth}` : status.replaceAll("_", " ");
    return <span className={`status status-${tone}`}>{text}</span>;
  }

  function progressBar(current: number | null | undefined, total: number | null | undefined, unit: string): ReactNode {
    if (current == null || !total) return null;
    return (
      <div className="node-progress">
        <div className="progress-bar">
          <div className="progress-bar-fill" style={{ width: `${Math.round((current / total) * 100)}%` }} />
        </div>
        <span>
          {current}/{total} {unit}
        </span>
      </div>
    );
  }

  function reconstructionNode(r: Reconstruction): ReactNode {
    const children = tree.byReconstruction.get(r.id) ?? [];
    const open = isOpen(r.id, false);
    const stats = frameStats[r.id];
    const total = stats?.total_frame_count ?? r.total_frame_count;
    const isStereo = stats?.is_stereo ?? r.is_stereo;
    const succeeded = r.status === "succeeded";
    const facts = [
      r.map_point_count != null ? `${r.map_point_count.toLocaleString()} pts` : null,
      r.registered_frame_count != null
        ? total != null
          ? `${r.registered_frame_count}/${total} frames used`
          : `${r.registered_frame_count} frames`
        : null,
      isStereo == null ? null : isStereo ? "stereo" : "mono",
    ].filter(Boolean);
    return (
      <div className="node node-reconstruction" key={r.id}>
        <div className="node-row">
          <Check selectionKey={`reconstruction:${r.id}`} />
          {children.length > 0 ? <Toggle open={open} onClick={() => setOpen(r.id, !open)} /> : <span className="toggle-spacer" />}
          <div className="node-main">
            <div className="node-title">
              <span className="node-name">Reconstruction</span>
              {statusChip(r.status, { position: r.queue_position, depth: r.queue_depth })}
              <span className="node-count">{formatDate(r.created_at)}</span>
              {children.length > 0 && (
                <button className="link" onClick={() => setOpen(r.id, !open)}>
                  {children.length} localization run{children.length === 1 ? "" : "s"}
                </button>
              )}
            </div>
            <div className="node-meta">
              {facts.length > 0 && <>{facts.join(" · ")} · </>}
              <span className="mono" title={JSON.stringify(r.options ?? {}, null, 1)}>
                {optionsSummary(r)}
              </span>
              <span className="mono"> · {r.id.slice(0, 8)}</span>
            </div>
            {!TERMINAL_STATUSES.has(r.status) && progressBar(r.progress_current, r.progress_total, "")}
            {r.error && <div className="node-error">{r.error}</div>}
          </div>
          <div className="node-actions">
            {succeeded && (
              <>
                <button onClick={() => openViewer(r.id)}>Visualize</button>
                <button onClick={() => setDialog({ kind: "localize", reconstruction: r, label: reconstructionLabel(r) })}>Localize…</button>
                <Menu
                  label="Export"
                  items={[
                    { label: "Zip archive…", onSelect: () => setDialog({ kind: "export", exportKind: "zip", reconstruction: r }) },
                    { label: "Poses (JSON)…", onSelect: () => setDialog({ kind: "export", exportKind: "poses", reconstruction: r }) },
                  ]}
                />
              </>
            )}
            {DELETABLE_STATUSES.has(r.status) && <button onClick={() => setDialog({ kind: "deleteReconstruction", reconstruction: r })}>Delete</button>}
          </div>
        </div>
        {open && children.length > 0 && <div className="node-children">{children.map(runNode)}</div>}
      </div>
    );
  }

  function runNode(run: LocalizationSummary): ReactNode {
    const done = run.status === "done";
    const showing = resultsOpen.has(run.run_id);
    return (
      <div className="node node-run" key={run.run_id}>
        <div className="node-row">
          <Check selectionKey={`run:${run.run_id}`} />
          {done ? <Toggle open={showing} onClick={() => toggleResults(run.run_id)} /> : <span className="toggle-spacer" />}
          <div className="node-main">
            <div className="node-title">
              <span className="node-name">Localization run</span>
              {statusChip(run.status)}
              <span className="node-count">{formatDate(run.created_at)}</span>
              {done && (
                <span className="node-count">
                  {run.valid_count}/{run.image_count} valid poses
                </span>
              )}
            </div>
            <div className="node-meta">
              <span className="mono">{run.image_dir ?? "—"}</span>
              {run.use_chunking != null && <> · {run.use_chunking ? "chunking" : "no chunking"}</>}
              <span className="mono"> · {run.run_id.slice(0, 8)}</span>
            </div>
            {run.status === "running" && progressBar(run.progress?.completed, run.progress?.total, "images")}
            {run.error && <div className="node-error">{run.error}</div>}
          </div>
          <div className="node-actions">
            {done && run.reconstruction_id && (
              <>
                <button onClick={() => openViewer(run.reconstruction_id as string, run.run_id)}>Visualize</button>
                <button onClick={() => toggleResults(run.run_id)}>{showing ? "Hide results" : "Results"}</button>
                <button onClick={() => setDialog({ kind: "save", saveKind: "table", runId: run.run_id })}>Save table</button>
                <button onClick={() => setDialog({ kind: "save", saveKind: "images", runId: run.run_id })}>Save images</button>
              </>
            )}
          </div>
        </div>
        {done && showing && (
          <div className="node-children">
            <RunResults runId={run.run_id} />
          </div>
        )}
      </div>
    );
  }

  // ── Page ──────────────────────────────────────────────────────────────────

  const empty = loaded && tree.sortedCaptures.length === 0 && tree.pendingSets.length === 0;

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Captures</h2>
        <div className="node-actions">
          {selecting ? (
            <>
              <span className="node-count">{plan.total} selected</span>
              <button disabled title="Merging selected items isn't implemented yet">
                Merge
              </button>
              <button disabled={plan.total === 0} onClick={() => setDialog({ kind: "deleteSelection" })}>
                Delete…
              </button>
              <button onClick={endSelecting}>Cancel</button>
            </>
          ) : (
            <>
              <button onClick={() => setSelecting(true)}>Select</button>
              <button onClick={() => setDialog({ kind: "import" })}>Import…</button>
              <button onClick={() => void refreshAll()} disabled={refreshing}>
                {refreshing ? "Refreshing…" : "Refresh"}
              </button>
            </>
          )}
        </div>
      </div>

      {loadError && <div className="banner banner-error">{loadError}</div>}
      {notices.map((n) => (
        <div key={n.id} className={`banner banner-${n.tone} banner-dismissible`}>
          <span>{n.text}</span>
          <button className="link" onClick={() => setNotices((all) => all.filter((x) => x.id !== n.id))} aria-label="Dismiss">
            ✕
          </button>
        </div>
      ))}

      {!loaded && !loadError && <div className="node-empty">Loading…</div>}
      {empty && <div className="node-empty">No captures yet. Add an image folder, import a reconstruction, or upload a capture with howard-test.</div>}

      <div className="tree">
        {tree.pendingSets.map(pendingSetNode)}
        {tree.sortedCaptures.map(captureNode)}
      </div>

      {tree.orphanReconstructions.length > 0 && (
        <>
          <div className="panel-header">
            <h2>Reconstructions without a listed capture</h2>
          </div>
          <div className="tree">{tree.orphanReconstructions.map(reconstructionNode)}</div>
        </>
      )}
      {tree.orphanRuns.length > 0 && (
        <>
          <div className="panel-header">
            <h2>Localization runs without a reconstruction</h2>
          </div>
          <div className="tree">{tree.orphanRuns.map(runNode)}</div>
        </>
      )}

      {dialog?.kind === "reconstruct" && (
        <ReconstructDialog
          captureName={dialog.capture.name}
          captureId={dialog.capture.id}
          siblings={tree.byCapture.get(dialog.capture.id) ?? []}
          onClose={() => setDialog(null)}
          onStarted={(jobId) => {
            setDialog(null);
            setOpen(dialog.capture.id, true);
            void followJob(jobId);
          }}
        />
      )}
      {dialog?.kind === "poseless" && (
        <PoselessReconstructDialog
          set={dialog.set}
          onClose={() => setDialog(null)}
          onStarted={(jobId) => {
            setDialog(null);
            void followJob(jobId);
          }}
        />
      )}
      {dialog?.kind === "localize" && (
        <LocalizeDialog
          reconstructionLabel={dialog.label}
          reconstructionId={dialog.reconstruction.id}
          onClose={() => setDialog(null)}
          onStarted={() => {
            setDialog(null);
            setOpen(dialog.reconstruction.id, true);
            void refreshFast().catch((err: unknown) => notify("error", errorText(err)));
          }}
        />
      )}
      {dialog?.kind === "import" && (
        <ImportDialog
          onClose={() => setDialog(null)}
          onImported={(result, path) => {
            setDialog(null);
            const name = path.split("/").pop();
            if (result.kind === "image_folder") {
              notify("success", `Added image folder ${name}. Reconstruct it from its row.`);
            } else if (result.kind === "reconstruction_tar" && result.reconstruction) {
              if (result.reconstruction.capture_session_id) setOpen(result.reconstruction.capture_session_id, true);
              notify("success", `Imported ${name} as reconstruction ${result.reconstruction.id}.`);
            } else if (result.job_id) {
              // A video: frames are extracted and uploaded before a reconstruction exists to show.
              notify("success", `Extracting ${name} and starting a reconstruction; this takes a few minutes.`);
              void followJob(result.job_id);
            }
            void refreshFast().catch((err: unknown) => notify("error", errorText(err)));
          }}
        />
      )}
      {dialog?.kind === "export" && (
        <ExportDialog
          kind={dialog.exportKind}
          reconstruction={dialog.reconstruction}
          onClose={() => setDialog(null)}
          onDone={(message) => {
            setDialog(null);
            notify("success", message);
          }}
        />
      )}
      {dialog?.kind === "save" && (
        <SaveRunDialog
          kind={dialog.saveKind}
          runId={dialog.runId}
          onClose={() => setDialog(null)}
          onDone={(message, tone) => {
            setDialog(null);
            notify(tone, message);
          }}
        />
      )}
      {dialog?.kind === "deleteReconstruction" && (
        <ConfirmDeleteDialog
          title="Delete reconstruction?"
          onClose={() => setDialog(null)}
          onConfirm={async () => {
            await deleteReconstruction(dialog.reconstruction.id);
            await refreshFast();
          }}
        >
          This permanently deletes reconstruction <span className="mono">{dialog.reconstruction.id}</span> and its stored
          data. This cannot be undone.
        </ConfirmDeleteDialog>
      )}
      {dialog?.kind === "deleteSelection" && (
        <ConfirmDeleteDialog
          title={`Delete ${plan.total} selected item${plan.total === 1 ? "" : "s"}?`}
          onClose={() => setDialog(null)}
          onConfirm={async () => {
            setDialog(null);
            await deleteSelection();
          }}
        >
          <>
            This permanently deletes:
            <ul style={{ margin: "6px 0", paddingLeft: 18 }}>
              {plan.captureIds.length > 0 && (
                <li>
                  {plan.captureIds.length} capture{plan.captureIds.length === 1 ? "" : "s"} — each with its uploaded
                  tar and every reconstruction built from it
                </li>
              )}
              {plan.reconstructionIds.length > 0 && (
                <li>
                  {plan.reconstructionIds.length} reconstruction{plan.reconstructionIds.length === 1 ? "" : "s"} — each
                  with its stored map data and localization map
                </li>
              )}
              {plan.runIds.length > 0 && (
                <li>
                  {plan.runIds.length} localization run{plan.runIds.length === 1 ? "" : "s"}
                </li>
              )}
              {(plan.cascadedReconstructions > 0 || plan.cascadedRuns > 0) && (
                <li>
                  included in the above: {plan.cascadedReconstructions} reconstruction
                  {plan.cascadedReconstructions === 1 ? "" : "s"} and {plan.cascadedRuns} localization run
                  {plan.cascadedRuns === 1 ? "" : "s"}
                </li>
              )}
            </ul>
            Stored data on the server (object storage and database rows) is removed as well. This cannot be undone.
            Query images and registered image folders are not touched.
          </>
        </ConfirmDeleteDialog>
      )}
    </div>
  );
}
