import { useState } from "react";
import { Mono, ViewHeader } from "@/components/atoms";
import { IconArrowRight } from "@/components/icons";
import type { Chapter, TimelineEvent } from "@/types/graph";

/* ── Spine indicator ─────────────────────────────────────────── */
function SpineIndicator({ count, max: _max }: { count: number; max: number }) {
  return (
    <div className="flex items-center justify-center" style={{ width: 24, height: 36 }}>
      <div className="relative bg-ivy-rule" style={{ width: 4, height: 36 }}>
        {Array.from({ length: count }).map((_, i) => (
          <div
            key={i}
            className="absolute left-0 right-0 bg-ivy-accent"
            style={{
              top:    `${(i / Math.max(count, 1)) * 100}%`,
              height: `${Math.max(2, 100 / Math.max(count, 1) - 8)}%`,
            }}
          />
        ))}
      </div>
    </div>
  );
}

/* ── Density bars ────────────────────────────────────────────── */
function DensityBars({ count, max }: { count: number; max: number }) {
  return (
    <div className="flex items-center gap-0.5" style={{ height: 12 }}>
      {Array.from({ length: max }).map((_, i) => (
        <span
          key={i}
          style={{
            width: 6,
            height: i < count ? 10 : 4,
            background: i < count ? "var(--ivy-ink)" : "var(--ivy-rule)",
          }}
        />
      ))}
    </div>
  );
}

/* ── Chapter ribbon ──────────────────────────────────────────── */
function ChapterRibbon({ events, totalEvents }: { events: TimelineEvent[]; totalEvents: number }) {
  return (
    <div className="relative" style={{ height: 28 }}>
      <div className="absolute left-0 right-0 top-1/2 h-px bg-ivy-rule" />
      {events.map((e) => (
        <div
          key={e.event_id}
          className="absolute"
          style={{ left: `${(e.order / totalEvents) * 100}%`, top: "50%", transform: "translate(-50%, -50%)" }}
          title={e.description}
        >
          <span
            className="block h-2 w-2 rounded-full bg-ivy-accent"
            style={{ outline: "2px solid var(--ivy-bgInk)" }}
          />
        </div>
      ))}
      <div className="absolute -bottom-1 left-0 font-mono text-[9px] text-ivy-inkFaint">order #1</div>
      <div className="absolute -bottom-1 right-0 font-mono text-[9px] text-ivy-inkFaint">#{totalEvents}</div>
    </div>
  );
}

/* ── Manuscript view ─────────────────────────────────────────── */
export default function ManuscriptView({
  chapters,
  events,
}: {
  chapters: Chapter[];
  events: TimelineEvent[];
}) {
  const [openIdx, setOpenIdx] = useState(0);

  const counts = chapters.map((c) =>
    events.filter((e) => e.chapter_num === c.chapter_num).length
  );
  const maxCount = Math.max(...counts, 1);
  const totalEvents = events.length;
  const totalChars = new Set(chapters.flatMap((c) => c.characters)).size;

  return (
    <div className="px-10 py-8 max-w-[1100px] mx-auto">
      <ViewHeader
        title="Manuscript"
        subtitle={`${chapters.length} chapters · ${totalEvents} events`}
        stats={[
          { v: chapters.length, l: "Chapters" },
          { v: totalEvents,     l: "Events" },
          { v: totalChars,      l: "Named characters" },
        ]}
      />

      <div className="rounded-sm border border-ivy-rule bg-ivy-bgRaised">
        {/* Table header */}
        <div
          className="grid items-center gap-4 px-5 py-2.5 text-[10px] font-mono uppercase tracking-[0.18em] text-ivy-inkFaint border-b border-ivy-rule"
          style={{ gridTemplateColumns: "44px 36px minmax(0,1fr) 140px 60px 60px 24px" }}
        >
          <span>Ch.</span>
          <span />
          <span>Title</span>
          <span>Event density</span>
          <span className="text-right">Events</span>
          <span className="text-right">Char.</span>
          <span />
        </div>

        {chapters.map((c, i) => {
          const ce = events
            .filter((e) => e.chapter_num === c.chapter_num)
            .sort((a, b) => a.order - b.order);
          const open = openIdx === i;
          return (
            <div
              key={c.chapter_num}
              style={{ borderBottom: i < chapters.length - 1 ? "1px solid var(--ivy-ruleSoft)" : "none" }}
            >
              <button
                onClick={() => setOpenIdx(open ? -1 : i)}
                className="grid items-center gap-4 w-full px-5 py-3.5 text-left transition-colors"
                style={{
                  gridTemplateColumns: "44px 36px minmax(0,1fr) 140px 60px 60px 24px",
                  background: open ? "var(--ivy-bgInk)" : "transparent",
                }}
              >
                <Mono className="text-[12px] text-ivy-inkMute">
                  {String(c.chapter_num).padStart(2, "0")}
                </Mono>
                <SpineIndicator count={ce.length} max={maxCount} />
                <div className="min-w-0">
                  <p className="font-serif text-[15px] truncate text-ivy-inkDeep">{c.chapter_title}</p>
                  <p className="text-[12px] truncate text-ivy-inkMute">{c.summary[0]}</p>
                </div>
                <DensityBars count={ce.length} max={maxCount} />
                <Mono className="text-[12px] text-right text-ivy-ink">{ce.length}</Mono>
                <Mono className="text-[12px] text-right text-ivy-ink">{c.characters.length}</Mono>
                <span
                  className="text-ivy-inkFaint transition-transform duration-200"
                  style={{ transform: open ? "rotate(90deg)" : "none" }}
                >
                  <IconArrowRight />
                </span>
              </button>

              {open && (
                <div
                  className="grid grid-cols-12 gap-8 px-5 pt-1 pb-6"
                  style={{ background: "var(--ivy-bgInk)" }}
                >
                  <div className="col-span-7">
                    <p className="font-mono text-[10px] uppercase tracking-[0.22em] mb-2 text-ivy-inkFaint">
                      summary
                    </p>
                    <ul className="space-y-2 mb-5">
                      {c.summary.map((s, k) => (
                        <li key={k} className="flex gap-3 text-[14px] leading-relaxed text-ivy-ink">
                          <Mono className="text-ivy-inkFaint">{String(k + 1).padStart(2, "0")}</Mono>
                          <span>{s}</span>
                        </li>
                      ))}
                    </ul>
                    <p className="font-mono text-[10px] uppercase tracking-[0.22em] mb-2 text-ivy-inkFaint">
                      key events
                    </p>
                    <ol className="space-y-1.5">
                      {c.key_events.map((ev, k) => (
                        <li key={k} className="flex items-baseline gap-3 text-[13px] text-ivy-ink">
                          <Mono className="text-ivy-accent">{ce[k]?.event_id ?? "—"}</Mono>
                          <span>{ev}</span>
                        </li>
                      ))}
                    </ol>
                  </div>
                  <div className="col-span-5 space-y-4">
                    <div>
                      <p className="font-mono text-[10px] uppercase tracking-[0.22em] mb-2 text-ivy-inkFaint">
                        characters
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {c.characters.map((name) => (
                          <span
                            key={name}
                            className="text-[12px] px-2 py-0.5 rounded-sm border border-ivy-rule text-ivy-ink"
                          >
                            {name}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="font-mono text-[10px] uppercase tracking-[0.22em] mb-2 text-ivy-inkFaint">
                        chronology contribution
                      </p>
                      <ChapterRibbon events={ce} totalEvents={totalEvents} />
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
