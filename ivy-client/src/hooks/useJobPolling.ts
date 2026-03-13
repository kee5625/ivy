import { useCallback, useEffect, useRef, useState } from "react";
import axios from "axios";
import type { Chapter, Job } from "@/types/graph";

const JOB_POLL_INTERVAL = 3000;
const CHAPTERS_POLL_INTERVAL = 4000;

type UseJobPollingResult = {
  job: Job | null;
  chapters: Chapter[];
  isLoading: boolean;
  error: string | null;
};

export function useJobPolling(jobId: string): UseJobPollingResult {
  const [job, setJob] = useState<Job | null>(null);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const jobTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const chaptersTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isMountedRef = useRef(true);

  const isTerminal = useCallback((status: string) => {
    return status === "ingestion_complete" || status === "failed";
  }, []);

  const fetchJob = useCallback(async () => {
    try {
      const { data } = await axios.get<Job>(`/api/jobs/${jobId}`);
      if (!isMountedRef.current) return;

      setJob(data);
      setError(null);

      if (!isTerminal(data.status)) {
        jobTimerRef.current = setTimeout(fetchJob, JOB_POLL_INTERVAL);
      }
    } catch (err) {
      if (!isMountedRef.current) return;
      const message =
        axios.isAxiosError(err)
          ? (err.response?.data?.detail ?? err.message)
          : "Failed to fetch job status";
      setError(message);
      // Retry on error unless we intentionally stopped
      jobTimerRef.current = setTimeout(fetchJob, JOB_POLL_INTERVAL);
    } finally {
      if (isMountedRef.current) {
        setIsLoading(false);
      }
    }
  }, [jobId, isTerminal]);

  const fetchChapters = useCallback(async () => {
    try {
      const { data } = await axios.get<{ chapters: Chapter[] }>(
        `/api/jobs/${jobId}/chapters`
      );
      if (!isMountedRef.current) return;

      // Merge in new chapters without losing ones already shown, sorted by num
      setChapters((prev) => {
        const existingNums = new Set(prev.map((c) => c.chapter_num));
        const incoming = data.chapters ?? [];
        const newOnes = incoming.filter((c) => !existingNums.has(c.chapter_num));
        if (newOnes.length === 0) return prev;
        return [...prev, ...newOnes].sort(
          (a, b) => a.chapter_num - b.chapter_num
        );
      });

      // Keep polling until job is terminal
      setJob((currentJob) => {
        if (!currentJob || !isTerminal(currentJob.status)) {
          chaptersTimerRef.current = setTimeout(
            fetchChapters,
            CHAPTERS_POLL_INTERVAL
          );
        }
        return currentJob;
      });
    } catch {
      if (!isMountedRef.current) return;
      // Silent fail for chapters — retry
      chaptersTimerRef.current = setTimeout(
        fetchChapters,
        CHAPTERS_POLL_INTERVAL
      );
    }
  }, [jobId, isTerminal]);

  useEffect(() => {
    isMountedRef.current = true;

    fetchJob();
    fetchChapters();

    return () => {
      isMountedRef.current = false;
      if (jobTimerRef.current) clearTimeout(jobTimerRef.current);
      if (chaptersTimerRef.current) clearTimeout(chaptersTimerRef.current);
    };
  }, [fetchJob, fetchChapters]);

  // Once job reaches terminal status, do one final chapter fetch to make sure
  // we have everything
  useEffect(() => {
    if (job && isTerminal(job.status)) {
      if (jobTimerRef.current) clearTimeout(jobTimerRef.current);
      if (chaptersTimerRef.current) clearTimeout(chaptersTimerRef.current);

      axios
        .get<{ chapters: Chapter[] }>(`/api/jobs/${jobId}/chapters`)
        .then(({ data }) => {
          if (!isMountedRef.current) return;
          setChapters(
            (data.chapters ?? []).sort(
              (a, b) => a.chapter_num - b.chapter_num
            )
          );
        })
        .catch(() => {
          /* ignore */
        });
    }
  }, [job?.status, jobId, isTerminal]);

  return { job, chapters, isLoading, error };
}
