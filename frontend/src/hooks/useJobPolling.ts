import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { Job } from "../api/types";

const POLL_MS = 2000;
const ACTIVE: Job["status"][] = ["queued", "running"];

export function useJobPolling(jobId: number | null) {
  const [job, setJob] = useState<Job | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (jobId === null) return;

    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | null = null;

    const tick = async () => {
      try {
        const fresh = await api.getJob(jobId);
        if (cancelled) return;
        setJob(fresh);
        setError(null);
        if (ACTIVE.includes(fresh.status)) {
          timer = setTimeout(tick, POLL_MS);
        }
      } catch (e) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : String(e));
        timer = setTimeout(tick, POLL_MS);
      }
    };

    tick();

    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
  }, [jobId]);

  return { job, error };
}
