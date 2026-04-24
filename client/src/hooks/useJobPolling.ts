import { useCallback, useEffect, useRef, useState } from "react";

import { isTerminalJobStatus, type Job } from "@/types/graph";

const JOB_POLL_INTERVAL = 3000;

type UseJobPollingResult = {
  job: Job | null;
  isLoading: boolean;
  error: string | null;
};

async function parseErrorMessage(
  response: Response,
  fallbackMessage: string,
): Promise<string> {
  try {
    const contentType = response.headers.get("content-type") ?? "";
    if (contentType.includes("application/json")) {
      const body = (await response.json()) as { detail?: string };
      return body.detail ?? fallbackMessage;
    }

    const text = await response.text();
    return text || fallbackMessage;
  } catch {
    return fallbackMessage;
  }
}

export function useJobPolling(jobId: string): UseJobPollingResult {
  const [job, setJob] = useState<Job | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isMountedRef = useRef(true);

  const fetchJob = useCallback(async () => {
    try {
      const response = await fetch(`/api/jobs/${jobId}`);

      if (!response.ok) {
        const message = await parseErrorMessage(
          response,
          "Failed to fetch job status",
        );
        throw new Error(message);
      }

      const data = (await response.json()) as Job;
      if (!isMountedRef.current) return;

      setJob(data);
      setError(null);

      if (!isTerminalJobStatus(data.status)) {
        timerRef.current = setTimeout(fetchJob, JOB_POLL_INTERVAL);
      }
    } catch (err) {
      if (!isMountedRef.current) return;

      const message =
        err instanceof Error ? err.message : "Failed to fetch job status";

      setError(message);
      timerRef.current = setTimeout(fetchJob, JOB_POLL_INTERVAL);
    } finally {
      if (isMountedRef.current) {
        setIsLoading(false);
      }
    }
  }, [jobId]);

  useEffect(() => {
    isMountedRef.current = true;
    void fetchJob();

    return () => {
      isMountedRef.current = false;
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [fetchJob]);

  return { job, isLoading, error };
}
