import { useCallback, useEffect, useRef, useState } from "react";
import axios from "axios";

import { isTerminalJobStatus, type Job } from "@/types/graph";

const JOB_POLL_INTERVAL = 3000;

type UseJobPollingResult = {
  job: Job | null;
  isLoading: boolean;
  error: string | null;
};

export function useJobPolling(jobId: string): UseJobPollingResult {
  const [job, setJob] = useState<Job | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isMountedRef = useRef(true);

  const fetchJob = useCallback(async () => {
    try {
      const { data } = await axios.get<Job>(`/api/jobs/${jobId}`);
      if (!isMountedRef.current) return;

      setJob(data);
      setError(null);

      if (!isTerminalJobStatus(data.status)) {
        timerRef.current = setTimeout(fetchJob, JOB_POLL_INTERVAL);
      }
    } catch (err) {
      if (!isMountedRef.current) return;

      const message = axios.isAxiosError(err)
        ? (err.response?.data?.detail ?? err.message)
        : "Failed to fetch job status";

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
