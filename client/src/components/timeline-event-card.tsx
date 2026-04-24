import React, { useEffect, useRef, useState } from "react";

import type { TimelineEvent } from "@/types/graph";

type TimelineEventCardProps = {
  event: TimelineEvent;
  animationDelay?: number;
};

function formatConfidence(confidence: number | null): string {
  if (confidence === null || Number.isNaN(confidence)) {
    return "N/A";
  }

  return `${Math.round(confidence * 100)}%`;
}

function buildTimingCue(event: TimelineEvent): string {
  if (event.time_reference) {
    return event.time_reference;
  }

  if (event.inferred_date) {
    return event.inferred_date;
  }

  if (event.inferred_year !== null) {
    return `${event.inferred_year}`;
  }

  if (event.relative_time_anchor) {
    return event.relative_time_anchor;
  }

  return "No explicit time cue";
}

function buildRelationshipPills(event: TimelineEvent): string[] {
  const pills: string[] = [];

  if (event.causes.length > 0) {
    pills.push(`${event.causes.length} cause${event.causes.length > 1 ? "s" : ""}`);
  }

  if (event.caused_by.length > 0) {
    pills.push(`${event.caused_by.length} trigger${event.caused_by.length > 1 ? "s" : ""}`);
  }

  if (event.relative_time_anchor) {
    pills.push("time anchor");
  }

  return pills;
}

function MetadataList({
  label,
  values,
  emptyLabel,
}: {
  label: string;
  values: string[];
  emptyLabel: string;
}) {
  return (
    <section>
      <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#6e9576]">
        {label}
      </p>
      <div className="mt-2 flex flex-wrap gap-1.5">
        {values.length > 0 ? (
          values.map((value) => (
            <span
              key={value}
              className="inline-flex items-center rounded-full border border-[#cfe3ca] bg-white px-2.5 py-1 text-xs font-medium text-[#2f4f3b]"
            >
              {value}
            </span>
          ))
        ) : (
          <span className="text-sm text-[#6a866f]">{emptyLabel}</span>
        )}
      </div>
    </section>
  );
}

export const TimelineEventCard: React.FC<TimelineEventCardProps> = ({
  event,
  animationDelay = 0,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [bodyHeight, setBodyHeight] = useState(0);
  const [visible, setVisible] = useState(false);
  const bodyRef = useRef<HTMLDivElement>(null);
  const relationshipPills = buildRelationshipPills(event);
  const timingCue = buildTimingCue(event);

  useEffect(() => {
    const timeout = setTimeout(() => setVisible(true), 20);
    return () => clearTimeout(timeout);
  }, []);

  useEffect(() => {
    if (bodyRef.current) {
      setBodyHeight(isExpanded ? bodyRef.current.scrollHeight : 0);
    }
  }, [event, isExpanded]);

  return (
    <article
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(14px)",
        transition: `opacity 0.42s ease ${animationDelay}ms, transform 0.42s ease ${animationDelay}ms`,
      }}
      className="overflow-hidden rounded-[1.7rem] border border-[#c7e0c2] bg-white/96 shadow-[0_18px_45px_-34px_rgba(50,93,60,0.38)]"
    >
      <button
        type="button"
        onClick={() => setIsExpanded((value) => !value)}
        className="w-full px-4 py-4 text-left transition hover:bg-[#f7fbf4] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[#4f8957]/40 sm:px-5"
        aria-expanded={isExpanded}
      >
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className="rounded-full border border-[#c9e0c3] bg-[#eef8ea] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-[#4f8957]">
                {event.event_id}
              </span>
              <span className="rounded-full border border-[#d8e8d4] bg-[#f9fcf8] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-[#6e9576]">
                Chapter {event.chapter_num}
              </span>
              {relationshipPills.map((pill) => (
                <span
                  key={pill}
                  className="rounded-full border border-[#d7e6d3] bg-white px-2.5 py-1 text-[11px] font-semibold uppercase tracking-wide text-[#6a866f]"
                >
                  {pill}
                </span>
              ))}
            </div>

            <h3 className="mt-3 text-base font-bold leading-6 text-[#234231] sm:text-lg">
              {event.description}
            </h3>

            <div className="mt-2 flex flex-wrap items-center gap-2 text-sm text-[#5f7a66]">
              <span className="rounded-full bg-[#f3faf0] px-2.5 py-1 text-xs font-medium text-[#4c6b54]">
                {timingCue}
              </span>
              <span className="text-xs uppercase tracking-[0.22em] text-[#8aa58e]">
                {event.chapter_title}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3 self-start sm:flex-col sm:items-end">
            <div className="rounded-2xl border border-[#d7e6d3] bg-[#f7fbf5] px-3 py-2 text-right text-sm text-[#4d6652]">
              <p className="text-xs uppercase tracking-[0.2em] text-[#7c987f]">Order</p>
              <p className="mt-1 text-base font-bold text-[#2f4f3b]">#{event.order}</p>
            </div>

            <span
              className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-[#c9e0c3] bg-white text-[#4f8957] transition-transform duration-300"
              style={{ transform: isExpanded ? "rotate(180deg)" : "rotate(0deg)" }}
              aria-hidden
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 16 16"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M3 6L8 11L13 6"
                  stroke="currentColor"
                  strokeWidth="1.8"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </span>
          </div>
        </div>
      </button>

      <div
        style={{
          height: bodyHeight,
          transition: "height 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
          overflow: "hidden",
        }}
      >
        <div ref={bodyRef}>
          <div className="border-t border-[#eef7eb] bg-[#fbfef9] px-4 pb-5 pt-4 sm:px-5">
            <div className="grid gap-4 md:grid-cols-[1.1fr_1fr]">
              <div className="space-y-4 rounded-[1.3rem] border border-[#dbead7] bg-white px-4 py-4">
                <section>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#6e9576]">
                    Timing
                  </p>
                  <div className="mt-2 space-y-1.5 text-sm text-[#355342]">
                    <p>{event.time_reference ?? "No direct time reference"}</p>
                    {event.inferred_date && <p>Inferred date: {event.inferred_date}</p>}
                    {event.inferred_year !== null && <p>Inferred year: {event.inferred_year}</p>}
                    {event.relative_time_anchor && <p>{event.relative_time_anchor}</p>}
                  </div>
                </section>

                <section>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#6e9576]">
                    Context
                  </p>
                  <div className="mt-2 space-y-1.5 text-sm text-[#355342]">
                    <p>Chapter: {event.chapter_title}</p>
                    <p>Location: {event.location ?? "Unspecified"}</p>
                    <p>Confidence: {formatConfidence(event.confidence)}</p>
                  </div>
                </section>
              </div>

              <div className="space-y-4 rounded-[1.3rem] border border-[#dbead7] bg-[#f6fbf4] px-4 py-4">
                <MetadataList
                  label="Characters"
                  values={event.characters_present}
                  emptyLabel="No characters attached"
                />
                <MetadataList
                  label="Causes"
                  values={event.causes}
                  emptyLabel="No direct outgoing links"
                />
                <MetadataList
                  label="Caused By"
                  values={event.caused_by}
                  emptyLabel="No direct incoming links"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </article>
  );
};
