import { useParams } from "react-router-dom";
import { useJobPolling } from "@/hooks/useJobPolling";
import { PipelinePanel } from "@/components/pipeline-panel";
import { ChapterCard } from "@/components/chapter-card";

export default function JobDetailsPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const { job, chapters, isLoading, error } = useJobPolling(jobId ?? "");

  const isComplete = job?.status === "ingestion_complete";
  const isFailed = job?.status === "failed";

  return (
    <div className="min-h-screen bg-linear-to-b from-[#f4fbf1] via-[#fbfef9] to-[#f5faf3] px-5 py-10 text-[#2b4a37] sm:px-8 lg:px-12">
      {/* Subtle decorative blobs */}
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -left-20 top-10 h-64 w-64 rounded-full bg-[#d8ebd2]/50 blur-3xl" />
        <div className="absolute -right-24 top-20 h-72 w-72 rounded-full bg-[#e5f3df]/60 blur-3xl" />
        <div className="absolute bottom-0 left-1/2 h-48 w-96 -translate-x-1/2 rounded-full bg-[#eaf5e4]/40 blur-3xl" />
      </div>

      <div className="mx-auto max-w-7xl">
        {/* Page header */}
        <div className="mb-8">
          <h1 className="text-3xl font-extrabold tracking-tight text-[#234231] sm:text-4xl">
            Analysis Pipeline
          </h1>
          <p className="mt-1.5 text-sm text-[#5a7a62]">
            Job{" "}
            <span className="font-mono font-semibold text-[#2b4a37]">
              {jobId}
            </span>
          </p>
        </div>

        {/* Completion banner */}
        {isComplete && (
          <div className="mb-6 flex flex-col gap-3 rounded-2xl border border-[#a8d4a0] bg-[#eef8ea] px-5 py-4 shadow-[0_4px_18px_-8px_rgba(50,93,60,0.18)] sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-3">
              {/* Checkmark circle */}
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#4f8957] text-white shadow-sm">
                <svg
                  viewBox="0 0 20 20"
                  fill="none"
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5"
                  aria-hidden
                >
                  <path
                    d="M4 10.5L8.5 15L16 6"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </span>
              <div>
                <p className="font-bold text-[#2b4a37]">Analysis complete</p>
                <p className="text-sm text-[#5a7a62]">
                  {chapters.length} chapter{chapters.length !== 1 ? "s" : ""}{" "}
                  extracted and ready to explore.
                </p>
              </div>
            </div>

            <button
              type="button"
              disabled
              className="inline-flex cursor-not-allowed items-center gap-2 rounded-xl border border-[#b8d5b1] bg-white/70 px-4 py-2 text-sm font-semibold text-[#9ab8a0] shadow-sm"
              title="Graph view coming soon"
            >
              <svg
                viewBox="0 0 20 20"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                className="h-4 w-4"
                aria-hidden
              >
                <circle
                  cx="5"
                  cy="10"
                  r="2.5"
                  stroke="currentColor"
                  strokeWidth="1.6"
                />
                <circle
                  cx="15"
                  cy="5"
                  r="2.5"
                  stroke="currentColor"
                  strokeWidth="1.6"
                />
                <circle
                  cx="15"
                  cy="15"
                  r="2.5"
                  stroke="currentColor"
                  strokeWidth="1.6"
                />
                <path
                  d="M7.5 9L12.5 6M7.5 11L12.5 14"
                  stroke="currentColor"
                  strokeWidth="1.6"
                  strokeLinecap="round"
                />
              </svg>
              View Graph
              <span className="rounded-full border border-[#c5dfbf] bg-[#f4fbf1] px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide text-[#7aa882]">
                soon
              </span>
            </button>
          </div>
        )}

        {/* Failed banner */}
        {isFailed && (
          <div className="mb-6 flex items-center gap-3 rounded-2xl border border-red-200 bg-red-50 px-5 py-4">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-red-100 text-red-600">
              <svg
                viewBox="0 0 16 16"
                fill="none"
                className="h-4 w-4"
                aria-hidden
              >
                <path
                  d="M8 3v5M8 11.5v.5"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                />
                <circle
                  cx="8"
                  cy="8"
                  r="6.5"
                  stroke="currentColor"
                  strokeWidth="1.5"
                />
              </svg>
            </span>
            <div>
              <p className="font-semibold text-red-700">Processing failed</p>
              {job?.error && (
                <p className="text-sm text-red-600">{job.error}</p>
              )}
            </div>
          </div>
        )}

        {/* Two-panel layout */}
        <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:gap-8">
          {/* ── Left panel: pipeline progress ── */}
          <aside className="w-full shrink-0 lg:w-72 xl:w-80">
            <div className="sticky top-8 rounded-3xl border border-[#c5dfbf] bg-white/92 p-6 shadow-[0_20px_55px_-35px_rgba(50,93,60,0.28)]">
              <h2 className="mb-5 text-xs font-bold uppercase tracking-widest text-[#4f8957]">
                Pipeline Progress
              </h2>
              <PipelinePanel job={job} isLoading={isLoading} />
            </div>
          </aside>

          {/* ── Right panel: chapter cards ── */}
          <main className="min-w-0 flex-1">
            {/* Empty / loading state */}
            {chapters.length === 0 && !isFailed && (
              <div className="flex flex-col items-center justify-center gap-4 rounded-3xl border border-dashed border-[#c5dfbf] bg-[#f4fbf1]/60 px-8 py-16 text-center">
                {isLoading ||
                job?.status === "in_progress" ||
                job?.status === "pending" ? (
                  <>
                    {/* Animated leaf/dots loader */}
                    <span className="flex gap-1.5" aria-hidden>
                      {[0, 150, 300].map((delay) => (
                        <span
                          key={delay}
                          className="h-2.5 w-2.5 rounded-full bg-[#4f8957] animate-bounce"
                          style={{ animationDelay: `${delay}ms` }}
                        />
                      ))}
                    </span>
                    <p className="text-sm font-medium text-[#5a7a62]">
                      Extracting chapters…
                    </p>
                    <p className="text-xs text-[#8db397]">
                      Cards will appear here as each chapter finishes.
                    </p>
                  </>
                ) : (
                  <>
                    <span className="text-3xl" aria-hidden>
                      📖
                    </span>
                    <p className="text-sm font-medium text-[#5a7a62]">
                      No chapters found yet.
                    </p>
                  </>
                )}
              </div>
            )}

            {/* Chapter cards grid */}
            {chapters.length > 0 && (
              <>
                <div className="mb-4 flex items-center justify-between">
                  <h2 className="text-xs font-bold uppercase tracking-widest text-[#4f8957]">
                    Chapters
                    <span className="ml-2 rounded-full border border-[#c5dfbf] bg-[#eef8ea] px-2 py-0.5 text-[11px] font-semibold text-[#4f8957]">
                      {chapters.length}
                    </span>
                  </h2>
                  {!isComplete && (
                    <span className="flex items-center gap-1.5 text-xs text-[#7a9e82]">
                      <span className="h-1.5 w-1.5 rounded-full bg-[#4f8957] animate-pulse" />
                      Live
                    </span>
                  )}
                </div>

                <div className="flex flex-col gap-3">
                  {chapters.map((chapter, index) => (
                    <ChapterCard
                      key={chapter.chapter_num}
                      chapter={chapter}
                      animationDelay={Math.min(index * 60, 300)}
                    />
                  ))}
                </div>
              </>
            )}

            {/* Error state */}
            {error && !job && (
              <div className="rounded-2xl border border-red-200 bg-red-50 px-5 py-4 text-sm text-red-700">
                <span className="font-semibold">Error:</span> {error}
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}
