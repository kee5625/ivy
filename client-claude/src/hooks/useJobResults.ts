import { useEffect, useState } from "react";
import type { Chapter, Job, PlotHole, TimelineEvent } from "@/types/graph";

export type UseJobResultsResult = {
  job: Job | null;
  chapters: Chapter[];
  timelineEvents: TimelineEvent[];
  plotHoles: PlotHole[];
  isLoading: boolean;
  error: string | null;
};

async function fetchJson<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const body = (await res.json()) as { detail?: string };
      if (body.detail) msg = body.detail;
    } catch { /* ignore */ }
    throw new Error(msg);
  }
  return (await res.json()) as T;
}

export function useJobResults(jobId: string): UseJobResultsResult {
  const [job, setJob] = useState<Job | null>(null);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
  const [plotHoles, setPlotHoles] = useState<PlotHole[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      setIsLoading(true);
      try {
        const [jobData, chapData, timeData, holeData] = await Promise.all([
          fetchJson<Job>(`/api/jobs/${jobId}`),
          fetchJson<{ chapters: Chapter[] }>(`/api/jobs/${jobId}/chapters`),
          fetchJson<{ timeline_events: TimelineEvent[] }>(`/api/jobs/${jobId}/timeline`),
          fetchJson<{ plot_holes: PlotHole[] }>(`/api/jobs/${jobId}/plot-holes`),
        ]);
        if (!active) return;
        setJob(jobData);
        setChapters(chapData.chapters ?? []);
        setTimelineEvents(timeData.timeline_events ?? []);
        setPlotHoles(holeData.plot_holes ?? []);
        setError(null);
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Failed to load results");
      } finally {
        if (active) setIsLoading(false);
      }
    }

    void load();
    return () => { active = false; };
  }, [jobId]);

  return { job, chapters, timelineEvents, plotHoles, isLoading, error };
}
