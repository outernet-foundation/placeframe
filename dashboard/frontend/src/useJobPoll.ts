import { useEffect, useRef, useState } from "react";
import { getJob } from "./api";
import type { Job } from "./types";

export function useJobPoll<TResult = unknown>(jobId: string | null, intervalMs = 2000): Job<TResult> | null {
  const [job, setJob] = useState<Job<TResult> | null>(null);
  const timer = useRef<number | null>(null);

  useEffect(() => {
    if (!jobId) {
      setJob(null);
      return;
    }
    let cancelled = false;

    async function poll(): Promise<void> {
      try {
        const result = await getJob<TResult>(jobId as string);
        if (cancelled) return;
        setJob(result);
        if (result.status === "running") {
          timer.current = window.setTimeout(poll, intervalMs);
        }
      } catch (err) {
        if (cancelled) return;
        setJob({
          id: jobId as string,
          kind: "reconstruct",
          status: "failed",
          reconstruction_id: null,
          result: null,
          error: err instanceof Error ? err.message : String(err),
        });
      }
    }

    void poll();
    return () => {
      cancelled = true;
      if (timer.current !== null) window.clearTimeout(timer.current);
    };
  }, [jobId, intervalMs]);

  return job;
}
