export type JobStatus =
  | "pending"
  | "in_progress"
  | "ingestion_complete"
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

export type PipelineStep = {
  id: string;
  label: string;
  description: string;
  available: boolean;
};

export const PIPELINE_STEPS: PipelineStep[] = [
  {
    id: "ingestion_agent",
    label: "Extract Chapters",
    description: "Parsing PDF and extracting chapter data",
    available: true,
  },
  {
    id: "entity_agent",
    label: "Extract Entities",
    description: "Identifying characters and locations",
    available: false,
  },
  {
    id: "relation_agent",
    label: "Build Relations",
    description: "Mapping relationships between entities",
    available: false,
  },
  {
    id: "graph_agent",
    label: "Render Graph",
    description: "Constructing the knowledge graph",
    available: false,
  },
];

// Legacy — kept so JobStatus component import doesn't break
export type JobStatusProps = {
  jobId: string;
  status: "pending" | "running" | "completed" | "failed";
  progress?: number;
  message?: string;
};
