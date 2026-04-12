import { Link, useParams } from "react-router-dom";

import { PipelinePanel } from "@/components/pipeline-panel";
import { useJobPolling } from "@/hooks/useJobPolling";
import { isResultsReadyStatus } from "@/types/graph";

const ACTIVE_COPY: Record<string, { title: string; body: string }> = {
  pending: {
    title: "Queued for processing",
    body: "Your upload has been accepted and the backend is preparing the pipeline.",
  },
  ingestion_in_progress: {
    title: "Extracting the story structure",
    body: "Ivy is parsing the PDF, breaking it into chapters, and storing the chapter summaries and key events.",
  },
  ingestion_complete: {
    title: "Chapters extracted",
    body: "Ingestion finished successfully. The timeline agent is next and will build a full chronological story view.",
  },
  timeline_in_progress: {
    title: "Building the complete timeline",
    body: "The backend is ordering events across the full story and preserving causal links between them.",
  },
  timeline_complete: {
    title: "Timeline locked in",
    body: "Chronology is complete. Ivy is now reviewing the finished story state for concrete plot holes before publishing the final results.",
  },
  plot_hole_in_progress: {
    title: "Scanning for continuity issues",
    body: "The final pass is looking for high-signal contradictions like timeline paradoxes, location conflicts, dead-character contradictions, and unresolved setups.",
  },
  plot_hole_complete: {
    title: "Results are ready",
    body: "The full pipeline has finished. You can open the results page to inspect chapters, the merged timeline, and real issues from the plot-hole pass.",
  },
  failed: {
    title: "Pipeline stopped",
    body: "The job failed before the full review finished. Review the error details below before retrying.",
  },
};

export default function JobDetailsPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const { job, isLoading, error } = useJobPolling(jobId ?? "");

  const currentStatus = job?.status ?? "pending";
  const statusCopy = ACTIVE_COPY[currentStatus] ?? ACTIVE_COPY.pending;
  const canSeeResults = job ? isResultsReadyStatus(job.status) : false;

  return (
    <div className="min-h-screen bg-linear-to-b from-[#f4fbf1] via-[#fbfef9] to-[#f5faf3] px-5 py-10 text-[#2b4a37] sm:px-8 lg:px-12">
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -left-20 top-10 h-64 w-64 rounded-full bg-[#d8ebd2]/50 blur-3xl" />
        <div className="absolute -right-24 top-20 h-72 w-72 rounded-full bg-[#e5f3df]/60 blur-3xl" />
        <div className="absolute bottom-0 left-1/2 h-48 w-96 -translate-x-1/2 rounded-full bg-[#eaf5e4]/40 blur-3xl" />
      </div>

      <div className="mx-auto max-w-6xl">
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[#6e9576]">
              Processing
            </p>
            <h1 className="mt-2 text-3xl font-extrabold tracking-tight text-[#234231] sm:text-4xl">
              Story Analysis Status
            </h1>
          </div>

          <Link
            to={`/results/${jobId}`}
            aria-disabled={!canSeeResults}
            className={`inline-flex items-center justify-center rounded-xl px-4 py-2.5 text-sm font-semibold transition ${
              canSeeResults
                ? "bg-[#4f8957] text-white shadow-[0_14px_30px_-20px_rgba(50,93,60,0.55)] hover:bg-[#42774a]"
                : "cursor-not-allowed border border-[#c9dec5] bg-white/70 text-[#9ab8a0]"
            }`}
          >
            See Results
          </Link>
        </div>

        <div className="grid gap-6 lg:grid-cols-[minmax(0,1.15fr)_320px]">
          <main className="space-y-6">
            <section className="rounded-[2rem] border border-[#c5dfbf] bg-white/92 p-6 shadow-[0_20px_55px_-35px_rgba(50,93,60,0.28)] sm:p-8">
              <div className="flex flex-col gap-5">
                <div className="max-w-2xl">
                  <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[#6e9576]">
                    Current Step
                  </p>
                  <h2 className="mt-3 text-2xl font-bold text-[#234231]">
                    {isLoading && !job ? "Loading pipeline state..." : statusCopy.title}
                  </h2>
                  <p className="mt-3 text-sm leading-7 text-[#587160]">
                    {statusCopy.body}
                  </p>
                </div>
              </div>

              {job?.status === "failed" && job.error && (
                <div className="mt-6 rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
                  <p className="font-semibold">Processing failed</p>
                  <p className="mt-1">{job.error}</p>
                </div>
              )}

              {!canSeeResults && job?.status !== "failed" && (
                <div className="mt-6 rounded-2xl border border-[#d8ead2] bg-[#f7fbf5] px-5 py-4 text-sm text-[#587160]">
                  <p className="font-semibold text-[#294635]">Results unlock after processing finishes</p>
                  <p className="mt-1">
                    Once the final review completes, the button above will open the full results view.
                  </p>
                </div>
              )}
            </section>

            {error && !job && (
              <div className="rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
                <span className="font-semibold">Error:</span> {error}
              </div>
            )}
          </main>

          <aside className="lg:sticky lg:top-8 lg:self-start">
            <div className="rounded-[2rem] border border-[#c5dfbf] bg-white/92 p-6 shadow-[0_20px_55px_-35px_rgba(50,93,60,0.28)]">
              <h2 className="mb-5 text-xs font-bold uppercase tracking-widest text-[#4f8957]">
                Pipeline Progress
              </h2>
              <PipelinePanel job={job} isLoading={isLoading} />
            </div>
          </aside>
        </div>
      </div>
    </div>
  );
}
