import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ChapterCard } from "@/components/chapter-card";
import { useJobResults } from "@/hooks/useJobResults";
import type { PlotHole, TimelineEvent } from "@/types/graph";

type TabKey = "chapters" | "timeline" | "issues";

function formatConfidence(confidence: number | null): string {
  if (confidence === null || Number.isNaN(confidence)) {
    return "N/A";
  }

  return `${Math.round(confidence * 100)}%`;
}

function TimelineList({ events }: { events: TimelineEvent[] }) {
  if (events.length === 0) {
    return (
      <div className="rounded-3xl border border-dashed border-[#caded1] bg-[#f7fbf5] px-6 py-10 text-sm text-[#5a7a62]">
        No timeline events have been generated for this job yet.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {events.map((event) => (
        <article
          key={event.event_id}
          className="rounded-3xl border border-[#c5dfbf] bg-white px-5 py-5 shadow-[0_16px_40px_-34px_rgba(50,93,60,0.3)]"
        >
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="rounded-full border border-[#c9e0c3] bg-[#eef8ea] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-[#4f8957]">
                  {event.event_id}
                </span>
                <span className="rounded-full border border-[#d8e8d4] bg-[#f9fcf8] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-[#6e9576]">
                  Chapter {event.chapter_num}
                </span>
                <span className="rounded-full border border-[#d8e8d4] bg-[#f9fcf8] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-[#6e9576]">
                  Confidence {formatConfidence(event.confidence)}
                </span>
              </div>
              <h3 className="mt-3 text-lg font-bold text-[#234231]">
                {event.description}
              </h3>
              <p className="mt-1 text-sm text-[#607864]">{event.chapter_title}</p>
            </div>

            <div className="rounded-2xl border border-[#d6e8d0] bg-[#f7fbf5] px-4 py-3 text-sm text-[#4a6551]">
              <p>Order #{event.order}</p>
              {event.time_reference && <p className="mt-1">{event.time_reference}</p>}
              {event.relative_time_anchor && (
                <p className="mt-1">{event.relative_time_anchor}</p>
              )}
            </div>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <div className="rounded-2xl bg-[#f6fbf4] px-4 py-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#6e9576]">
                Characters
              </p>
              <p className="mt-2 text-sm text-[#355342]">
                {event.characters_present.length > 0
                  ? event.characters_present.join(", ")
                  : "None attached"}
              </p>
            </div>
            <div className="rounded-2xl bg-[#f6fbf4] px-4 py-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#6e9576]">
                Causes
              </p>
              <p className="mt-2 text-sm text-[#355342]">
                {event.causes.length > 0 ? event.causes.join(", ") : "No direct outgoing links"}
              </p>
            </div>
            <div className="rounded-2xl bg-[#f6fbf4] px-4 py-3">
              <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#6e9576]">
                Caused By
              </p>
              <p className="mt-2 text-sm text-[#355342]">
                {event.caused_by.length > 0
                  ? event.caused_by.join(", ")
                  : "No direct incoming links"}
              </p>
            </div>
          </div>
        </article>
      ))}
    </div>
  );
}

function IssuesList({ plotHoles }: { plotHoles: PlotHole[] }) {
  if (plotHoles.length === 0) {
    return (
      <div className="rounded-3xl border border-dashed border-[#caded1] bg-[#f7fbf5] px-6 py-10 text-sm text-[#5a7a62]">
        The Issues tab is wired and ready, but the plot-hole pipeline has not been implemented on this branch yet.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {plotHoles.map((plotHole) => (
        <article
          key={plotHole.hole_id}
          className="rounded-3xl border border-[#c5dfbf] bg-white px-5 py-5 shadow-[0_16px_40px_-34px_rgba(50,93,60,0.3)]"
        >
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-[#d4e8ce] bg-[#f8fcf7] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-[#5c7b63]">
              {plotHole.hole_type}
            </span>
            <span className="rounded-full border border-[#d4e8ce] bg-[#f8fcf7] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-[#5c7b63]">
              {plotHole.severity}
            </span>
          </div>
          <p className="mt-3 text-sm leading-7 text-[#355342]">
            {plotHole.description}
          </p>
        </article>
      ))}
    </div>
  );
}

export default function ResultsPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const [activeTab, setActiveTab] = useState<TabKey>("timeline");
  const { job, chapters, timelineEvents, plotHoles, isLoading, error } =
    useJobResults(jobId ?? "");

  const tabs = useMemo(
    () =>
      [
        { key: "chapters" as const, label: `Chapters (${chapters.length})` },
        { key: "timeline" as const, label: `Timeline (${timelineEvents.length})` },
        { key: "issues" as const, label: `Issues (${plotHoles.length})` },
      ],
    [chapters.length, timelineEvents.length, plotHoles.length]
  );

  return (
    <div className="min-h-screen bg-linear-to-b from-[#f4fbf1] via-[#fbfef9] to-[#f5faf3] px-5 py-10 text-[#2b4a37] sm:px-8 lg:px-12">
      <div className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
        <div className="absolute -left-20 top-10 h-64 w-64 rounded-full bg-[#d8ebd2]/50 blur-3xl" />
        <div className="absolute -right-24 top-20 h-72 w-72 rounded-full bg-[#e5f3df]/60 blur-3xl" />
      </div>

      <div className="mx-auto max-w-6xl">
        <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[#6e9576]">
              Story Results
            </p>
            <h1 className="mt-2 text-3xl font-extrabold tracking-tight text-[#234231] sm:text-4xl">
              Timeline Review
            </h1>
            <p className="mt-2 text-sm text-[#5a7a62]">
              Job{" "}
              <span className="font-mono font-semibold text-[#2b4a37]">
                {jobId}
              </span>
            </p>
          </div>

          <div className="flex flex-wrap gap-3">
            <span className="inline-flex items-center rounded-full border border-[#c9e0c3] bg-white/80 px-3 py-1.5 text-sm font-semibold text-[#4f8957]">
              {job?.status ?? "Loading"}
            </span>
            <Link
              to={`/graph/${jobId}`}
              className="inline-flex items-center justify-center rounded-xl border border-[#c9e0c3] bg-white/80 px-4 py-2.5 text-sm font-semibold text-[#355342] transition hover:bg-[#f4fbf1]"
            >
              Back to Job Monitor
            </Link>
          </div>
        </div>

        <div className="rounded-[2rem] border border-[#c5dfbf] bg-white/92 p-4 shadow-[0_20px_55px_-35px_rgba(50,93,60,0.28)] sm:p-6">
          <div className="flex flex-wrap gap-2">
            {tabs.map((tab) => (
              <button
                key={tab.key}
                type="button"
                onClick={() => setActiveTab(tab.key)}
                className={`rounded-2xl px-4 py-2.5 text-sm font-semibold transition ${
                  activeTab === tab.key
                    ? "bg-[#4f8957] text-white shadow-[0_12px_28px_-22px_rgba(50,93,60,0.55)]"
                    : "bg-[#f5fbf2] text-[#587160] hover:bg-[#eef8ea]"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="mt-6">
            {isLoading && (
              <div className="rounded-3xl border border-dashed border-[#caded1] bg-[#f7fbf5] px-6 py-10 text-sm text-[#5a7a62]">
                Loading results...
              </div>
            )}

            {!isLoading && error && (
              <div className="rounded-3xl border border-red-200 bg-red-50 px-6 py-10 text-sm text-red-700">
                <span className="font-semibold">Error:</span> {error}
              </div>
            )}

            {!isLoading && !error && activeTab === "chapters" && (
              <div className="space-y-3">
                {chapters.length > 0 ? (
                  chapters.map((chapter, index) => (
                    <ChapterCard
                      key={chapter.chapter_num}
                      chapter={chapter}
                      animationDelay={Math.min(index * 50, 250)}
                    />
                  ))
                ) : (
                  <div className="rounded-3xl border border-dashed border-[#caded1] bg-[#f7fbf5] px-6 py-10 text-sm text-[#5a7a62]">
                    No chapter data is available for this job.
                  </div>
                )}
              </div>
            )}

            {!isLoading && !error && activeTab === "timeline" && (
              <TimelineList events={timelineEvents} />
            )}

            {!isLoading && !error && activeTab === "issues" && (
              <IssuesList plotHoles={plotHoles} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
