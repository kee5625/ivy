import { useEffect, useState } from "react";
import axios from "axios";

import type { Chapter, Job, PlotHole, TimelineEvent } from "@/types/graph";

type UseJobResultsResult = {
  job: Job | null;
  chapters: Chapter[];
  timelineEvents: TimelineEvent[];
  plotHoles: PlotHole[];
  isLoading: boolean;
  error: string | null;
};

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
        const [jobResponse, chaptersResponse, timelineResponse, plotHoleResponse] =
          await Promise.all([
            axios.get<Job>(`/api/jobs/${jobId}`),
            axios.get<{ chapters: Chapter[] }>(`/api/jobs/${jobId}/chapters`),
            axios.get<{ timeline_events: TimelineEvent[] }>(
              `/api/jobs/${jobId}/timeline`
            ),
            axios.get<{ plot_holes: PlotHole[] }>(`/api/jobs/${jobId}/plot-holes`),
          ]);

        if (!active) return;

        setJob(jobResponse.data);
        setChapters(chaptersResponse.data.chapters ?? []);
        setTimelineEvents(timelineResponse.data.timeline_events ?? []);
        setPlotHoles(plotHoleResponse.data.plot_holes ?? []);
        setError(null);
      } catch (err) {
        if (!active) return;

        const message = axios.isAxiosError(err)
          ? (err.response?.data?.detail ?? err.message)
          : "Failed to load job results";

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
