import React from "react";
import type { Job } from "@/types/graph";
import { PIPELINE_STEPS } from "@/types/graph";

type PipelinePanelProps = {
  job: Job | null;
  isLoading: boolean;
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

type StepState = "completed" | "active" | "pending" | "unavailable";

function getStepState(
  stepId: string,
  job: Job | null,
  stepAvailable: boolean,
): StepState {
  if (!stepAvailable) return "unavailable";
  if (!job) return "pending";

  if (job.completed_agents.includes(stepId)) return "completed";

  if (
    job.current_agent === stepId &&
    (job.status === "in_progress" || job.status === "pending")
  )
    return "active";

  if (job.status === "ingestion_complete") {
    // All available steps are done
    return "completed";
  }

  return "pending";
}

const CheckIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    viewBox="0 0 16 16"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    aria-hidden
  >
    <path
      d="M3 8.5L6.5 12L13 5"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

const SpinnerIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    viewBox="0 0 16 16"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    aria-hidden
  >
    <circle
      cx="8"
      cy="8"
      r="6"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeDasharray="28"
      strokeDashoffset="10"
    />
  </svg>
);

const LockIcon: React.FC<{ className?: string }> = ({ className }) => (
  <svg
    viewBox="0 0 16 16"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className={className}
    aria-hidden
  >
    <rect
      x="3"
      y="7"
      width="10"
      height="7"
      rx="1.5"
      stroke="currentColor"
      strokeWidth="1.5"
    />
    <path
      d="M5 7V5a3 3 0 0 1 6 0v2"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
    />
  </svg>
);

export const PipelinePanel: React.FC<PipelinePanelProps> = ({
  job,
  isLoading,
}) => {
  const statusLabel: Record<string, string> = {
    pending: "Pending",
    in_progress: "In Progress",
    ingestion_complete: "Chapters Extracted",
    failed: "Failed",
  };

  const statusDot: Record<string, string> = {
    pending: "bg-amber-400",
    in_progress: "bg-[#4f8957] animate-pulse",
    ingestion_complete: "bg-[#4f8957]",
    failed: "bg-red-500",
  };

  const currentStatus = job?.status ?? "pending";

  return (
    <div className="flex flex-col gap-6">
      {/* Status badge */}
      <div className="flex items-center gap-2.5">
        <span
          className={`h-2.5 w-2.5 rounded-full shrink-0 ${
            statusDot[currentStatus] ?? "bg-gray-400"
          }`}
        />
        <span className="text-sm font-semibold text-[#2b4a37]">
          {isLoading && !job
            ? "Loading…"
            : (statusLabel[currentStatus] ?? currentStatus)}
        </span>
        {job?.status === "failed" && job.error && (
          <span className="ml-1 text-xs text-red-600 truncate">
            — {job.error}
          </span>
        )}
      </div>

      {/* Stepper */}
      <div className="relative flex flex-col gap-0">
        {PIPELINE_STEPS.map((step, index) => {
          const state = getStepState(step.id, job, step.available);
          const isLast = index === PIPELINE_STEPS.length - 1;

          return (
            <div key={step.id} className="flex items-stretch gap-4">
              {/* Track column */}
              <div className="flex flex-col items-center w-8 shrink-0">
                {/* Icon circle */}
                <div
                  className={`
                    z-10 flex items-center justify-center h-8 w-8 rounded-full border-2 shrink-0
                    transition-colors duration-300
                    ${
                      state === "completed"
                        ? "border-[#4f8957] bg-[#4f8957] text-white"
                        : state === "active"
                          ? "border-[#4f8957] bg-white text-[#4f8957]"
                          : state === "pending"
                            ? "border-[#c5dfbf] bg-[#f4fbf1] text-[#a3c19a]"
                            : "border-[#d8e8d4] bg-[#f8fcf6] text-[#c5d9c0]"
                    }
                  `}
                >
                  {state === "completed" && <CheckIcon className="h-4 w-4" />}
                  {state === "active" && (
                    <SpinnerIcon className="h-4 w-4 animate-spin" />
                  )}
                  {state === "pending" && (
                    <span className="h-2 w-2 rounded-full bg-current" />
                  )}
                  {state === "unavailable" && (
                    <LockIcon className="h-3.5 w-3.5" />
                  )}
                </div>

                {/* Connector line */}
                {!isLast && (
                  <div
                    className={`flex-1 w-px my-1 transition-colors duration-500 ${
                      state === "completed" ? "bg-[#4f8957]" : "bg-[#d4e8ce]"
                    }`}
                    style={{ minHeight: "20px" }}
                  />
                )}
              </div>

              {/* Text content */}
              <div className={`pb-5 min-w-0 ${isLast ? "pb-0" : ""}`}>
                <p
                  className={`text-sm font-semibold leading-tight transition-colors duration-300 ${
                    state === "completed" || state === "active"
                      ? "text-[#2b4a37]"
                      : "text-[#9ab8a0]"
                  }`}
                >
                  {step.label}
                  {state === "unavailable" && (
                    <span className="ml-1.5 text-[10px] font-medium uppercase tracking-wide text-[#b8d0b4] align-middle">
                      soon
                    </span>
                  )}
                </p>
                <p
                  className={`mt-0.5 text-xs leading-relaxed transition-colors duration-300 ${
                    state === "completed" || state === "active"
                      ? "text-[#5a7a62]"
                      : "text-[#b8cfbb]"
                  }`}
                >
                  {step.description}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Job metadata */}
      {job && (
        <div className="mt-1 rounded-xl border border-[#d4e8ce] bg-[#f4fbf1] px-4 py-3 space-y-2">
          <h3 className="text-xs font-bold uppercase tracking-widest text-[#4f8957] mb-2">
            Job Details
          </h3>
          <dl className="space-y-1.5">
            <div className="flex items-start justify-between gap-2">
              <dt className="text-xs text-[#7a9e82] shrink-0">Job ID</dt>
              <dd
                className="text-xs font-mono font-medium text-[#2b4a37] truncate max-w-35"
                title={job.job_id}
              >
                {job.job_id}
              </dd>
            </div>
            {job.created_at && (
              <div className="flex items-start justify-between gap-2">
                <dt className="text-xs text-[#7a9e82] shrink-0">Started</dt>
                <dd className="text-xs font-medium text-[#2b4a37]">
                  {formatDate(job.created_at)}
                </dd>
              </div>
            )}
            {job.updated_at && (
              <div className="flex items-start justify-between gap-2">
                <dt className="text-xs text-[#7a9e82] shrink-0">Updated</dt>
                <dd className="text-xs font-medium text-[#2b4a37]">
                  {formatDate(job.updated_at)}
                </dd>
              </div>
            )}
          </dl>
        </div>
      )}
    </div>
  );
};
