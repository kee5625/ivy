import { useState } from "react";
import { Mono, ViewHeader } from "@/components/atoms";
import { IconArrowRight } from "@/components/icons";
import type { Chapter, TimelineEvent } from "@/types/graph";

/* ── Grid template (shared between header, rows, expanded panel) ── */
const GRID = "48px minmax(0,1fr) 140px 48px 24px";

/* ── Event density bar ───────────────────────────────────────── */
function DensityBar({ count, max }: { count: number; max: number }) {
  const pct = max > 0 ? count / max : 0;
  return (
    <div className="flex items-center gap-2.5">
      <div className="relative h-[3px] rounded-full bg-ivy-rule flex-1" style={{ minWidth: 60 }}>
        <div
          className="absolute left-0 top-0 h-[3px] rounded-full bg-ivy-accent transition-all"
          style={{ width: `${pct * 100}%` }}
        />
      </div>
      <Mono className="text-[11px] text-ivy-inkFaint w-3 text-right shrink-0">{count}</Mono>
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
  const [openIdx, setOpenIdx] = useState<number>(-1);

  const counts = chapters.map((c) =>
    events.filter((e) => e.chapter_num === c.chapter_num).length
  );
  const maxCount = Math.max(...counts, 1);
  const totalEvents = events.length;
  const totalChars = new Set(chapters.flatMap((c) => c.characters)).size;

  return (
    <div className="px-10 py-8 max-w-[960px] mx-auto">
      <ViewHeader
        title="Manuscript"
        subtitle="Chapter-by-chapter breakdown"
        stats={[
          { v: chapters.length, l: "Chapters" },
          { v: totalEvents,     l: "Events" },
          { v: totalChars,      l: "Characters" },
        ]}
      />

      <div className="rounded-sm border border-ivy-rule bg-ivy-bgRaised overflow-hidden">

        {/* ── Table header ── */}
        <div
          className="grid items-center gap-6 px-5 py-2.5 border-b border-ivy-rule
                     text-[10px] font-mono uppercase tracking-[0.18em] text-ivy-inkFaint"
          style={{ gridTemplateColumns: GRID }}
        >
          <span>Ch.</span>
          <span>Title</span>
          <span>Events</span>
          <span className="text-right">Char.</span>
          <span />
        </div>

        {chapters.map((c, i) => {
          const ce = events
            .filter((e) => e.chapter_num === c.chapter_num)
            .sort((a, b) => a.order - b.order);
          const open = openIdx === i;
          const isLast = i === chapters.length - 1;

          return (
            <div
              key={c.chapter_num}
              style={{
                borderBottom: isLast ? "none" : "1px solid var(--ivy-ruleSoft)",
                borderLeft: open ? "3px solid var(--ivy-accent)" : "3px solid transparent",
                transition: "border-left-color 150ms ease",
              }}
            >
              {/* ── Collapsed row ── */}
              <button
                onClick={() => setOpenIdx(open ? -1 : i)}
                className="grid items-center gap-6 w-full px-5 py-3.5 text-left
                           transition-colors hover:bg-ivy-bgInk"
                style={{
                  gridTemplateColumns: GRID,
                  background: open ? "var(--ivy-bgInk)" : "transparent",
                }}
              >
                <Mono className="text-[12px] text-ivy-inkMute">
                  {String(c.chapter_num).padStart(2, "0")}
                </Mono>

                <p className="font-serif text-[15px] truncate text-ivy-inkDeep leading-snug">
                  {c.chapter_title}
                </p>

                <DensityBar count={ce.length} max={maxCount} />

                <Mono className="text-[12px] text-right text-ivy-inkMute">
                  {c.characters.length}
                </Mono>

                <span
                  className="flex justify-center text-ivy-inkFaint transition-transform duration-200"
                  style={{ transform: open ? "rotate(90deg)" : "none" }}
                >
                  <IconArrowRight />
                </span>
              </button>

              {/* ── Expanded panel ── */}
              {open && (
                <div
                  className="grid gap-6 px-5 pt-5 pb-6"
                  style={{
                    gridTemplateColumns: GRID,
                    background: "var(--ivy-bgInk)",
                    borderTop: "1px solid var(--ivy-ruleSoft)",
                  }}
                >
                  {/* Spacer: aligns content under Title column */}
                  <div />

                  {/* Summary + Key events */}
                  <div className="min-w-0 space-y-6">

                    {c.summary.length > 0 && (
                      <div>
                        <p className="font-mono text-[10px] uppercase tracking-[0.22em] mb-3 text-ivy-inkFaint">
                          Summary
                        </p>
                        <ul className="space-y-2.5">
                          {c.summary.map((s, k) => (
                            <li key={k} className="flex gap-3">
                              <span
                                className="mt-[7px] h-1.5 w-1.5 rounded-full shrink-0"
                                style={{ background: "var(--ivy-accentSoft)", border: "1px solid var(--ivy-accent)" }}
                              />
                              <span className="text-[13px] leading-relaxed text-ivy-ink">{s}</span>
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {c.key_events.length > 0 && (
                      <div>
                        <p className="font-mono text-[10px] uppercase tracking-[0.22em] mb-3 text-ivy-inkFaint">
                          Key events
                          <span className="ml-2 text-ivy-inkFaint opacity-60">· {c.key_events.length}</span>
                        </p>
                        <ol
                          className="space-y-0 rounded-sm overflow-hidden"
                          style={{ border: "1px solid var(--ivy-ruleSoft)" }}
                        >
                          {c.key_events.map((ev, k) => (
                            <li
                              key={k}
                              className="flex gap-3 px-3 py-2.5 text-[13px] text-ivy-ink"
                              style={{
                                borderBottom: k < c.key_events.length - 1 ? "1px solid var(--ivy-ruleSoft)" : "none",
                                background: k % 2 === 0 ? "transparent" : "color-mix(in oklch, var(--ivy-rule) 20%, transparent)",
                              }}
                            >
                              <Mono className="text-[11px] text-ivy-accent shrink-0 mt-px w-4">
                                {k + 1}
                              </Mono>
                              <span className="leading-relaxed">{ev}</span>
                            </li>
                          ))}
                        </ol>
                      </div>
                    )}
                  </div>

                  {/* Characters — spans events + char cols */}
                  <div style={{ gridColumn: "3 / 5" }}>
                    <p className="font-mono text-[10px] uppercase tracking-[0.22em] mb-3 text-ivy-inkFaint">
                      Characters
                      {c.characters.length > 0 && (
                        <span className="ml-2 opacity-60">· {c.characters.length}</span>
                      )}
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {c.characters.map((name) => (
                        <span
                          key={name}
                          className="text-[12px] px-2 py-0.5 rounded-sm text-ivy-ink"
                          style={{ border: "1px solid var(--ivy-rule)", background: "var(--ivy-bgRaised)" }}
                        >
                          {name}
                        </span>
                      ))}
                      {c.characters.length === 0 && (
                        <span className="text-[12px] text-ivy-inkFaint italic">None recorded</span>
                      )}
                    </div>
                  </div>

                  {/* Arrow col spacer */}
                  <div />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
