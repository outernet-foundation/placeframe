import { useEffect, useRef, useState } from "react";
import { getLocalizationProgress, type LocalizationProgress } from "./api";

// Polls GET /api/localizations/{run_id}/progress while `active` is true. `run_id` is known
// immediately when the localize job starts (the backend generates it up front — see
// dashboard/backend/app.py's start_localize), so this can poll from the very first tick rather
// than waiting for the job to finish and report its own run_id in job.result.
export function useLocalizationProgress(
  runId: string | null,
  active: boolean,
  intervalMs = 1000,
): LocalizationProgress | null {
  const [progress, setProgress] = useState<LocalizationProgress | null>(null);
  const timer = useRef<number | null>(null);

  useEffect(() => {
    if (!runId || !active) {
      setProgress(null);
      return;
    }
    let cancelled = false;

    async function poll(): Promise<void> {
      try {
        const result = await getLocalizationProgress(runId as string);
        if (!cancelled) setProgress(result);
      } catch {
        // Transient (e.g. run directory not created yet) — keep the last known value and retry.
      }
      if (!cancelled) timer.current = window.setTimeout(poll, intervalMs);
    }

    void poll();
    return () => {
      cancelled = true;
      if (timer.current !== null) window.clearTimeout(timer.current);
    };
  }, [runId, active, intervalMs]);

  return progress;
}
