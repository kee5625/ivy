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
  severity: "high" | "medium" | "low";
  confidence: number;
  description: string;
  chapters_involved: number[];
  characters_involved: string[];
  events_involved: string[];
};

/** Derived on the frontend from timeline events */
export type Character = {
  name: string;
  event_count: number;
  chapters: number[];
};

export function isTerminalJobStatus(status: string): boolean {
  return status === "plot_hole_complete" || status === "failed";
}

export function isResultsReady(status: string): boolean {
  return status === "plot_hole_complete";
}
