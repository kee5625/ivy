import { useEffect, useState } from "react";

import type { Chapter, Job, PlotHole, TimelineEvent } from "@/types/graph";

type UseJobResultsResult = {
  job: Job | null;
  chapters: Chapter[];
  timelineEvents: TimelineEvent[];
  plotHoles: PlotHole[];
  isLoading: boolean;
  error: string | null;
};

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url);

  if (!response.ok) {
    let message = "Failed to load job results";

    try {
      const errorData = await response.json();
      if (
        errorData &&
        typeof errorData === "object" &&
        "detail" in errorData &&
        typeof (errorData as { detail?: unknown }).detail === "string"
      ) {
        message = (errorData as { detail: string }).detail;
      }
    } catch {
      // Ignore JSON parse issues and keep fallback message.
    }

    throw new Error(message);
  }

  return (await response.json()) as T;
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

    async function loadResults() {
      setIsLoading(true);

      try {
        const [
          jobResponse,
          chaptersResponse,
          timelineResponse,
          plotHoleResponse,
        ] = await Promise.all([
          fetchJson<Job>(`/api/jobs/${jobId}`),
          fetchJson<{ chapters: Chapter[] }>(`/api/jobs/${jobId}/chapters`),
          fetchJson<{ timeline_events: TimelineEvent[] }>(
            `/api/jobs/${jobId}/timeline`,
          ),
          fetchJson<{ plot_holes: PlotHole[] }>(
            `/api/jobs/${jobId}/plot-holes`,
          ),
        ]);

        if (!active) return;

        setJob(jobResponse);
        setChapters(chaptersResponse.chapters ?? []);
        setTimelineEvents(timelineResponse.timeline_events ?? []);
        setPlotHoles(plotHoleResponse.plot_holes ?? []);
        setError(null);
      } catch (err) {
        if (!active) return;

        const message =
          err instanceof Error ? err.message : "Failed to load job results";

        setError(message);
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }

    void loadResults();

    return () => {
      active = false;
    };
  }, [jobId]);

  return { job, chapters, timelineEvents, plotHoles, isLoading, error };
}
