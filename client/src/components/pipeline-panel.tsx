import React from "react";

import { PIPELINE_STEPS, type Job } from "@/types/graph";

type PipelinePanelProps = {
  job: Job | null;
  isLoading: boolean;
};

type StepState = "completed" | "active" | "pending" | "unavailable";

function getStepState(
  stepId: string,
  job: Job | null,
  stepAvailable: boolean,
): StepState {
  if (!stepAvailable) {
    return "unavailable";
  }

  if (!job) {
    return "pending";
  }

  if (job.completed_agents.includes(stepId)) {
    return "completed";
  }

  if (job.current_agent === stepId && job.status !== "failed") {
    return "active";
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
    pending: "Queued",
    ingestion_in_progress: "Ingestion in progress",
    ingestion_complete: "Ingestion complete",
    timeline_in_progress: "Timeline in progress",
    timeline_complete: "Timeline complete",
    plot_hole_in_progress: "Issue scan in progress",
    plot_hole_complete: "Results ready",
    failed: "Failed",
  };

  const statusDot: Record<string, string> = {
    pending: "bg-amber-400",
    ingestion_in_progress: "bg-[#4f8957] animate-pulse",
    ingestion_complete: "bg-[#9dc69f]",
    timeline_in_progress: "bg-[#4f8957] animate-pulse",
    timeline_complete: "bg-[#9dc69f]",
    plot_hole_in_progress: "bg-[#4f8957] animate-pulse",
    plot_hole_complete: "bg-[#4f8957]",
    failed: "bg-red-500",
  };

  const currentStatus = job?.status ?? "pending";

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center gap-2.5">
        <span
          className={`h-2.5 w-2.5 shrink-0 rounded-full ${
            statusDot[currentStatus] ?? "bg-gray-400"
          }`}
        />
        <span className="text-sm font-semibold text-[#2b4a37]">
          {isLoading && !job
            ? "Loading..."
            : (statusLabel[currentStatus] ?? currentStatus)}
        </span>
        {job?.status === "failed" && job.error && (
          <span className="ml-1 truncate text-xs text-red-600">
            - {job.error}
          </span>
        )}
      </div>

      <div className="relative flex flex-col gap-0">
        {PIPELINE_STEPS.map((step, index) => {
          const state = getStepState(step.id, job, step.available);
          const isLast = index === PIPELINE_STEPS.length - 1;

          return (
            <div key={step.id} className="flex items-stretch gap-4">
              <div className="flex w-8 shrink-0 flex-col items-center">
                <div
                  className={`
                    z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-full border-2
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

                {!isLast && (
                  <div
                    className={`my-1 w-px flex-1 transition-colors duration-500 ${
                      state === "completed" ? "bg-[#4f8957]" : "bg-[#d4e8ce]"
                    }`}
                    style={{ minHeight: "20px" }}
                  />
                )}
              </div>

              <div className={`min-w-0 ${isLast ? "pb-0" : "pb-5"}`}>
                <p
                  className={`text-sm font-semibold leading-tight transition-colors duration-300 ${
                    state === "completed" || state === "active"
                      ? "text-[#2b4a37]"
                      : "text-[#9ab8a0]"
                  }`}
                >
                  {step.label}
                  {state === "unavailable" && (
                    <span className="ml-1.5 align-middle text-[10px] font-medium uppercase tracking-wide text-[#b8d0b4]">
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
    </div>
  );
};
