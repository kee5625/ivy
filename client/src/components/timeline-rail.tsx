import React, { useMemo } from "react";

import { TimelineEventCard } from "@/components/timeline-event-card";
import type { TimelineEvent } from "@/types/graph";

type TimelineRailProps = {
  events: TimelineEvent[];
};

type ChapterTimelineSection = {
  chapter_num: number;
  chapter_title: string;
  start_order: number;
  end_order: number;
  events: TimelineEvent[];
};

function buildChapterSections(events: TimelineEvent[]): ChapterTimelineSection[] {
  const grouped = new Map<number, ChapterTimelineSection>();

  events
    .slice()
    .sort((left, right) => left.order - right.order)
    .forEach((event) => {
      const existing = grouped.get(event.chapter_num);

      if (existing) {
        existing.events.push(event);
        existing.start_order = Math.min(existing.start_order, event.order);
        existing.end_order = Math.max(existing.end_order, event.order);
        return;
      }

      grouped.set(event.chapter_num, {
        chapter_num: event.chapter_num,
        chapter_title: event.chapter_title,
        start_order: event.order,
        end_order: event.order,
        events: [event],
      });
    });

  return Array.from(grouped.values()).sort(
    (left, right) => left.start_order - right.start_order
  );
}

function TimelineLegend() {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="inline-flex items-center gap-2 rounded-full border border-[#d5e6d1] bg-white px-3 py-1.5 text-xs font-semibold text-[#4d6d54]">
        <span className="h-2.5 w-2.5 rounded-full bg-[#4f8957]" />
        Chronology node
      </span>
      <span className="inline-flex items-center gap-2 rounded-full border border-[#d5e6d1] bg-white px-3 py-1.5 text-xs font-semibold text-[#4d6d54]">
        <span className="h-2.5 w-2.5 rounded-full bg-[#87b18b]" />
        Cause / trigger pill
      </span>
      <span className="inline-flex items-center gap-2 rounded-full border border-[#d5e6d1] bg-white px-3 py-1.5 text-xs font-semibold text-[#4d6d54]">
        <span className="h-2.5 w-2.5 rounded-full bg-[#d5ead0]" />
        Time anchor cue
      </span>
    </div>
  );
}

function ChapterHeader({ section }: { section: ChapterTimelineSection }) {
  return (
    <div className="rounded-[1.8rem] border border-[#cfe3ca] bg-linear-to-br from-[#f8fcf6] to-[#eff8ea] p-5 shadow-[0_18px_44px_-38px_rgba(50,93,60,0.3)] md:sticky md:top-28">
      <div className="flex items-center gap-3">
        <span className="inline-flex h-11 w-11 items-center justify-center rounded-full border border-[#c5dfbf] bg-white text-sm font-bold text-[#4f8957]">
          {section.chapter_num}
        </span>
        <div className="min-w-0">
          <p className="text-[11px] font-semibold uppercase tracking-[0.28em] text-[#6e9576]">
            Source Chapter
          </p>
          <h3 className="mt-1 truncate text-lg font-bold text-[#234231]">
            {section.chapter_title}
          </h3>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3">
        <div className="rounded-2xl border border-[#d7e8d3] bg-white/85 px-3 py-3">
          <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#7c987f]">
            Events
          </p>
          <p className="mt-1 text-lg font-bold text-[#2f4f3b]">{section.events.length}</p>
        </div>
        <div className="rounded-2xl border border-[#d7e8d3] bg-white/85 px-3 py-3">
          <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#7c987f]">
            Order Span
          </p>
          <p className="mt-1 text-lg font-bold text-[#2f4f3b]">
            #{section.start_order}
            {section.end_order !== section.start_order ? `-#${section.end_order}` : ""}
          </p>
        </div>
      </div>

      <p className="mt-4 text-sm leading-6 text-[#587160]">
        These events originated in this chapter, but their placement on the rail
        follows the merged global chronology.
      </p>
    </div>
  );
}

function RailNode({
  order,
  isLast,
}: {
  order: number;
  isLast: boolean;
}) {
  return (
    <div className="relative flex min-h-12 justify-center">
      {!isLast && (
        <div className="absolute left-1/2 top-8 h-[calc(100%+1.75rem)] w-px -translate-x-1/2 bg-linear-to-b from-[#b8d7b3] via-[#d6e9d1] to-transparent" />
      )}
      <div className="relative z-10 flex h-8 w-8 items-center justify-center rounded-full border border-[#bdd8b7] bg-white text-[11px] font-bold text-[#4f8957] shadow-[0_10px_24px_-18px_rgba(50,93,60,0.45)]">
        {order}
      </div>
    </div>
  );
}

function EventRow({
  event,
  isLast,
  animationDelay,
}: {
  event: TimelineEvent;
  isLast: boolean;
  animationDelay: number;
}) {
  return (
    <div className="grid grid-cols-[2.25rem_minmax(0,1fr)] gap-3 md:grid-cols-[2.5rem_minmax(0,1fr)] md:gap-5">
      <div className="relative pt-1">
        <RailNode order={event.order} isLast={isLast} />
      </div>

      <div className="relative">
        <div className="pointer-events-none absolute -left-6 top-5 hidden h-px w-6 bg-[#c9dfc4] md:block" />
        <TimelineEventCard event={event} animationDelay={animationDelay} />
      </div>
    </div>
  );
}

export const TimelineRail: React.FC<TimelineRailProps> = ({ events }) => {
  const orderedEvents = useMemo(
    () => events.slice().sort((left, right) => left.order - right.order),
    [events]
  );

  const sections = useMemo(() => buildChapterSections(orderedEvents), [orderedEvents]);

  const summary = useMemo(() => {
    const anchoredCount = orderedEvents.filter(
      (event) => event.relative_time_anchor || event.time_reference || event.inferred_date
    ).length;
    const linkedCount = orderedEvents.filter(
      (event) => event.causes.length > 0 || event.caused_by.length > 0
    ).length;

    return {
      chapters: sections.length,
      linkedCount,
      anchoredCount,
      firstOrder: orderedEvents[0]?.order ?? 0,
      lastOrder: orderedEvents[orderedEvents.length - 1]?.order ?? 0,
    };
  }, [orderedEvents, sections.length]);

  if (events.length === 0) {
    return (
      <div className="rounded-3xl border border-dashed border-[#caded1] bg-[#f7fbf5] px-6 py-10 text-sm text-[#5a7a62]">
        No timeline events have been generated for this job yet.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="rounded-[1.9rem] border border-[#cfe3ca] bg-white/90 p-5 shadow-[0_18px_42px_-34px_rgba(50,93,60,0.35)]">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.28em] text-[#6e9576]">
              Story Rail
            </p>
            <h2 className="mt-2 text-2xl font-bold text-[#234231]">
              Visual chronology across the full narrative
            </h2>
            <p className="mt-2 max-w-3xl text-sm leading-7 text-[#5a7a62]">
              The rail keeps the merged order readable while still showing which
              chapter each event came from and where the strongest relationship
              cues live.
            </p>
          </div>

          <TimelineLegend />
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-2xl border border-[#d7e8d3] bg-[#f7fbf5] px-4 py-3">
            <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#7c987f]">
              Total Events
            </p>
            <p className="mt-1 text-xl font-bold text-[#2f4f3b]">{orderedEvents.length}</p>
          </div>
          <div className="rounded-2xl border border-[#d7e8d3] bg-[#f7fbf5] px-4 py-3">
            <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#7c987f]">
              Chapter Span
            </p>
            <p className="mt-1 text-xl font-bold text-[#2f4f3b]">{summary.chapters}</p>
          </div>
          <div className="rounded-2xl border border-[#d7e8d3] bg-[#f7fbf5] px-4 py-3">
            <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#7c987f]">
              Linked Events
            </p>
            <p className="mt-1 text-xl font-bold text-[#2f4f3b]">{summary.linkedCount}</p>
          </div>
          <div className="rounded-2xl border border-[#d7e8d3] bg-[#f7fbf5] px-4 py-3">
            <p className="text-[11px] font-semibold uppercase tracking-[0.24em] text-[#7c987f]">
              Order Range
            </p>
            <p className="mt-1 text-xl font-bold text-[#2f4f3b]">
              #{summary.firstOrder}-#{summary.lastOrder}
            </p>
            <p className="mt-1 text-xs text-[#708b74]">
              {summary.anchoredCount} events with time cues
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-8">
        {sections.map((section, sectionIndex) => (
          <section
            key={`chapter-${section.chapter_num}`}
            className="relative rounded-[2rem] border border-[#d7e8d3] bg-[#f8fcf7] p-4 shadow-[0_20px_50px_-40px_rgba(50,93,60,0.28)] sm:p-5 lg:p-6"
          >
            <div className="grid gap-6 lg:grid-cols-[minmax(0,250px)_minmax(0,1fr)] lg:gap-8">
              <ChapterHeader section={section} />

              <div className="relative">
                <div className="pointer-events-none absolute bottom-0 left-[1.1rem] top-0 w-px bg-linear-to-b from-[#b7d6b2] via-[#d7e7d2] to-transparent md:hidden" />
                <div className="space-y-4">
                  {section.events.map((event, eventIndex) => (
                    <EventRow
                      key={event.event_id}
                      event={event}
                      isLast={eventIndex === section.events.length - 1}
                      animationDelay={Math.min(sectionIndex * 60 + eventIndex * 40, 280)}
                    />
                  ))}
                </div>
              </div>
            </div>
          </section>
        ))}
      </div>
    </div>
  );
};
