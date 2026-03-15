export type JobStatus =
  | "pending"
  | "ingestion_in_progress"
  | "ingestion_complete"
  | "timeline_in_progress"
  | "timeline_complete"
  | "plot_hole_in_progress"
  | "plot_hole_complete"
  | "failed";

export type Job = {
  job_id: string;
  status: JobStatus;
  current_agent: string | null;
  completed_agents: string[];
  error: string | null;
  created_at: string;
  updated_at: string;
};

export type Chapter = {
  chapter_num: number;
  chapter_title: string;
  summary: string[];
  key_events: string[];
  characters: string[];
};

export type TimelineEvent = {
  event_id: string;
  description: string;
  chapter_num: number;
  chapter_title: string;
  order: number;
  characters_present: string[];
  location: string | null;
  causes: string[];
  caused_by: string[];
  time_reference: string | null;
  inferred_date: string | null;
  inferred_year: number | null;
  relative_time_anchor: string | null;
  confidence: number | null;
};

export type PlotHole = {
  hole_id: string;
  hole_type: string;
  severity: string;
  description: string;
  chapters_involved: number[];
  characters_involved: string[];
  events_involved: string[];
};

export type PipelineStep = {
  id: string;
  label: string;
  description: string;
  available: boolean;
};

export const PIPELINE_STEPS: PipelineStep[] = [
  {
    id: "ingestion_agent",
    label: "Ingestion",
    description: "Parse the PDF and extract chapter summaries and events.",
    available: true,
  },
  {
    id: "timeline_agent",
    label: "Timeline",
    description: "Turn chapter-level events into one ordered story timeline.",
    available: true,
  },
  {
    id: "plot_hole_agent",
    label: "Issues",
    description: "Review the finished timeline for concrete contradictions and unresolved setups.",
    available: true,
  },
];

export function isTerminalJobStatus(status: JobStatus | string): boolean {
  return status === "plot_hole_complete" || status === "failed";
}

export function isResultsReadyStatus(status: JobStatus | string): boolean {
  return status === "plot_hole_complete";
}

// Legacy - kept so JobStatus component import doesn't break
export type JobStatusProps = {
  jobId: string;
  status: "pending" | "running" | "completed" | "failed";
  progress?: number;
  message?: string;
};
