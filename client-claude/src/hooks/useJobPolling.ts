import { useCallback, useEffect, useRef, useState } from "react";
import { isTerminalJobStatus, type Job } from "@/types/graph";

const POLL_MS = 3000;

export type UseJobPollingResult = {
  job: Job | null;
  isLoading: boolean;
  error: string | null;
};

export function useJobPolling(jobId: string): UseJobPollingResult {
  const [job, setJob] = useState<Job | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const mountedRef = useRef(true);

  const fetchJob = useCallback(async () => {
    try {
      const res = await fetch(`/api/jobs/${jobId}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = (await res.json()) as Job;
      if (!mountedRef.current) return;
      setJob(data);
      setError(null);
      if (!isTerminalJobStatus(data.status)) {
        timerRef.current = setTimeout(fetchJob, POLL_MS);
      }
    } catch (err) {
      if (!mountedRef.current) return;
      setError(err instanceof Error ? err.message : "Failed to fetch job");
      timerRef.current = setTimeout(fetchJob, POLL_MS);
    } finally {
      if (mountedRef.current) setIsLoading(false);
    }
  }, [jobId]);

  useEffect(() => {
    mountedRef.current = true;
    void fetchJob();
    return () => {
      mountedRef.current = false;
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [fetchJob]);

  return { job, isLoading, error };
}
