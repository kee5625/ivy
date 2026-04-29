import { useEffect, useRef, useState } from "react";
import { Mono, ViewHeader, DetailField } from "@/components/atoms";
import type { TimelineEvent } from "@/types/graph";

/* ── Confidence meter ─────────────────────────────────────────── */
function ConfidenceMeter({ value }: { value: number | null }) {
  const v = value ?? 0;
  return (
    <div className="flex items-center gap-2">
      <Mono className="text-[13px] text-ivy-inkDeep">{Math.round(v * 100)}%</Mono>
      <div className="bg-ivy-rule" style={{ width: 60, height: 6 }}>
        <div style={{ width: `${v * 100}%`, height: "100%", background: "var(--ivy-accent)" }} />
      </div>
    </div>
  );
}

/* ── Event detail panel ───────────────────────────────────────── */
function EventDetail({
  event,
  pinned,
}: {
  event: TimelineEvent;
  pinned: boolean;
}) {
  return (
    <article className="rounded-sm border border-ivy-rule bg-ivy-bgRaised">
      <div className="px-5 py-4 flex items-start justify-between gap-4 border-b border-ivy-ruleSoft">
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <Mono
              className="text-[11px] px-1.5 py-0.5 rounded-sm bg-ivy-accentSoft text-ivy-accentInk"
            >
              {event.event_id}
            </Mono>
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-ivy-inkFaint">
              order #{String(event.order).padStart(2, "0")} · ch.{event.chapter_num}
            </span>
            {!pinned && (
              <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-ivy-inkFaint">
                · hover
              </span>
            )}
          </div>
          <h3 className="font-serif text-[20px] leading-snug text-ivy-inkDeep">{event.description}</h3>
          <p className="text-[12px] mt-1 text-ivy-inkMute">From "{event.chapter_title}"</p>
        </div>
        <div className="flex flex-col items-end gap-1.5 shrink-0">
          <ConfidenceMeter value={event.confidence} />
          <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-ivy-inkFaint">
            confidence
          </span>
        </div>
      </div>

      <div className="grid grid-cols-3 px-5 py-4 gap-6">
        <DetailField label="When">
          {event.time_reference ?? event.inferred_date ?? event.relative_time_anchor ?? "—"}
          {event.inferred_year && (
            <Mono className="ml-2 text-[11px] text-ivy-inkFaint">({event.inferred_year})</Mono>
          )}
        </DetailField>
        <DetailField label="Where">{event.location ?? "—"}</DetailField>
        <DetailField label="Who">
          <div className="flex flex-wrap gap-1 mt-0.5">
            {event.characters_present.map((c) => (
              <span key={c} className="text-[12px] px-1.5 py-0.5 rounded-sm border border-ivy-rule">
                {c}
              </span>
            ))}
          </div>
        </DetailField>
      </div>

      <div className="grid grid-cols-2 px-5 pb-5 gap-6">
        <DetailField label={`Caused by (${event.caused_by.length})`}>
          {event.caused_by.length === 0 ? (
            <span className="text-ivy-inkFaint">nothing in scope</span>
          ) : (
            <div className="flex flex-wrap gap-1 mt-0.5">
              {event.caused_by.map((id) => (
                <Mono key={id} className="text-[11px] px-1.5 py-0.5 rounded-sm border border-ivy-rule text-ivy-ink">
                  {id}
                </Mono>
              ))}
            </div>
          )}
        </DetailField>
        <DetailField label={`Causes (${event.causes.length})`}>
          {event.causes.length === 0 ? (
            <span className="text-ivy-inkFaint">nothing in scope</span>
          ) : (
            <div className="flex flex-wrap gap-1 mt-0.5">
              {event.causes.map((id) => (
                <Mono key={id} className="text-[11px] px-1.5 py-0.5 rounded-sm bg-ivy-accentSoft text-ivy-accentInk">
                  {id}
                </Mono>
              ))}
            </div>
          )}
        </DetailField>
      </div>
    </article>
  );
}

/* ── Legend ───────────────────────────────────────────────────── */
function TimelineLegend() {
  return (
    <div className="rounded-sm p-4 border border-ivy-rule bg-ivy-bgRaised">
      <p className="font-mono text-[10px] uppercase tracking-[0.22em] mb-3 text-ivy-inkFaint">legend</p>
      <ul className="space-y-2 text-[12px] text-ivy-ink">
        <li className="flex items-center gap-2.5">
          <svg width="20" height="14"><line x1="0" y1="7" x2="20" y2="7" stroke="var(--ivy-inkDeep)" strokeWidth="1.4" /></svg>
          <span>Spine — story order, left → right</span>
        </li>
        <li className="flex items-center gap-2.5">
          <svg width="20" height="14">
            <line x1="10" y1="0" x2="10" y2="14" stroke="var(--ivy-inkMute)" strokeWidth="1" />
            <circle cx="10" cy="0" r="3" fill="var(--ivy-bgRaised)" stroke="var(--ivy-inkDeep)" />
          </svg>
          <span>Rib length ∝ link density × uncertainty</span>
        </li>
        <li className="flex items-center gap-2.5">
          <svg width="20" height="14">
            <path d="M2 7 Q10 14 18 7" fill="none" stroke="var(--ivy-rule)" strokeWidth="0.8" />
          </svg>
          <span>Curve — causality chord</span>
        </li>
        <li className="flex items-center gap-2.5">
          <span className="inline-block h-2 w-2 rounded-full bg-ivy-accent" />
          <span>Active / pinned event</span>
        </li>
      </ul>
    </div>
  );
}

/* ── Timeline view ────────────────────────────────────────────── */
export default function TimelineView({ events: rawEvents }: { events: TimelineEvent[] }) {
  const events = [...rawEvents].sort((a, b) => a.order - b.order);
  const [hoverId, setHoverId] = useState<string | null>(null);
  const [pinId, setPinId] = useState<string>(events[0]?.event_id ?? "");
  const activeId = hoverId ?? pinId;
  const active = events.find((e) => e.event_id === activeId);

  const containerRef = useRef<HTMLDivElement>(null);
  const [w, setW] = useState(900);
  useEffect(() => {
    const update = () => {
      if (containerRef.current) setW(containerRef.current.clientWidth);
    };
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  const padX = 60, padY = 100;
  const minWidth = events.length * 70;
  const innerW = Math.max(w - padX * 2, minWidth);
  const totalW = innerW + padX * 2;
  const spineY = padY + 110;
  const xFor = (i: number) => padX + (i / Math.max(events.length - 1, 1)) * innerW;

  const layout = events.map((e, i) => {
    const above = i % 2 === 0;
    const linkCount = e.causes.length + e.caused_by.length;
    const ribLen = 30 + linkCount * 16 + (1 - (e.confidence ?? 0.5)) * 20;
    const x = xFor(i);
    const y = above ? spineY - ribLen : spineY + ribLen;
    return { ...e, x, y, above, ribLen };
  });

  const idToPt = Object.fromEntries(layout.map((p) => [p.event_id, p]));

  const years = Array.from(
    new Set(events.map((e) => e.inferred_year).filter(Boolean))
  ).sort() as number[];

  // Chapter bands
  const chapterBands: { chapter_num: number; chapter_title: string; startX: number; endX: number }[] = [];
  layout.forEach((p) => {
    const last = chapterBands[chapterBands.length - 1];
    if (last && last.chapter_num === p.chapter_num) {
      last.endX = p.x;
    } else {
      chapterBands.push({ chapter_num: p.chapter_num, chapter_title: p.chapter_title, startX: p.x, endX: p.x });
    }
  });

  return (
    <div className="px-10 py-8 max-w-[1400px] mx-auto">
      <ViewHeader
        title="Timeline"
        subtitle="A visual representation of your story."
        stats={[
          { v: events.length, l: "Events" },
          { v: events.filter((e) => e.causes.length || e.caused_by.length).length, l: "Linked" },
          { v: events.filter((e) => e.time_reference ?? e.inferred_date).length, l: "Time-anchored" },
          { v: years.length, l: "Year markers" },
        ]}
      />

      {/* Fish-skeleton SVG */}
      <div
        ref={containerRef}
        className="rounded-sm overflow-x-auto border border-ivy-rule bg-ivy-bgRaised"
      >
        <div style={{ width: totalW, position: "relative" }}>
          <svg width={totalW} height={spineY * 2} style={{ display: "block" }}>
            {/* guide rails */}
            <line x1={padX} y1={spineY - 150} x2={totalW - padX} y2={spineY - 150}
              stroke="var(--ivy-ruleSoft)" strokeWidth="1" strokeDasharray="2 4" />
            <line x1={padX} y1={spineY + 150} x2={totalW - padX} y2={spineY + 150}
              stroke="var(--ivy-ruleSoft)" strokeWidth="1" strokeDasharray="2 4" />

            {/* order ticks */}
            {layout.map((p, i) => (
              <g key={`tick-${i}`}>
                <line x1={p.x} y1={spineY - 6} x2={p.x} y2={spineY + 6}
                  stroke="var(--ivy-inkMute)" strokeWidth="0.8" />
                <text x={p.x} y={spineY + 22} fontSize="9" fontFamily="ui-monospace,monospace"
                  textAnchor="middle" fill="var(--ivy-inkFaint)">
                  #{String(i + 1).padStart(2, "0")}
                </text>
              </g>
            ))}

            {/* chapter bands */}
            {chapterBands.map((b, i) => {
              const x1 = b.startX - 12, x2 = b.endX + 12;
              const isActive = active?.chapter_num === b.chapter_num;
              return (
                <g key={`band-${i}`}>
                  <rect x={x1} y={spineY - 50} width={x2 - x1} height={14}
                    fill={isActive ? "var(--ivy-accentSoft)" : i % 2 === 0 ? "var(--ivy-bgInk)" : "var(--ivy-panel)"}
                    stroke={isActive ? "var(--ivy-accent)" : "var(--ivy-ruleSoft)"} strokeWidth="0.6" />
                  <text x={(x1 + x2) / 2} y={spineY - 40} textAnchor="middle"
                    fontSize="9" fontFamily="ui-monospace,monospace"
                    fill={isActive ? "var(--ivy-accentInk)" : "var(--ivy-inkMute)"} letterSpacing="0.5">
                    CH.{String(b.chapter_num).padStart(2, "0")}
                  </text>
                  <line x1={(x1 + x2) / 2} y1={spineY - 36} x2={(x1 + x2) / 2} y2={spineY - 8}
                    stroke="var(--ivy-ruleSoft)" strokeWidth="0.6" strokeDasharray="1 2" />
                </g>
              );
            })}

            {/* spine */}
            <line x1={padX} y1={spineY} x2={totalW - padX} y2={spineY}
              stroke="var(--ivy-inkDeep)" strokeWidth="1.4" />
            <polygon
              points={`${padX - 2},${spineY} ${padX + 6},${spineY - 3} ${padX + 6},${spineY + 3}`}
              fill="var(--ivy-inkDeep)" />
            <polygon
              points={`${totalW - padX + 2},${spineY} ${totalW - padX - 6},${spineY - 3} ${totalW - padX - 6},${spineY + 3}`}
              fill="var(--ivy-inkDeep)" />

            {/* causality chords */}
            {layout.map((p) =>
              p.causes.map((cid) => {
                const target = idToPt[cid];
                if (!target) return null;
                const mx = (p.x + target.x) / 2;
                const dim = activeId === p.event_id || activeId === cid;
                return (
                  <path
                    key={`${p.event_id}->${cid}`}
                    d={`M ${p.x} ${spineY} Q ${mx} ${spineY + (target.x > p.x ? 36 : -36)} ${target.x} ${spineY}`}
                    fill="none"
                    stroke={dim ? "var(--ivy-accent)" : "var(--ivy-rule)"}
                    strokeWidth={dim ? 1.2 : 0.8}
                    opacity={dim ? 0.95 : 0.55}
                  />
                );
              })
            )}

            {/* ribs + nodes */}
            {layout.map((p) => {
              const isActive = p.event_id === activeId;
              const isPinned = p.event_id === pinId;
              return (
                <g key={p.event_id}>
                  <line x1={p.x} y1={spineY} x2={p.x} y2={p.y}
                    stroke={isActive ? "var(--ivy-accent)" : "var(--ivy-inkMute)"}
                    strokeWidth={isActive ? 1.4 : 0.9} />
                  <circle cx={p.x} cy={p.y} r={isActive ? 6 : 4}
                    fill={isActive ? "var(--ivy-accent)" : "var(--ivy-bgRaised)"}
                    stroke={isActive ? "var(--ivy-accent)" : "var(--ivy-inkDeep)"}
                    strokeWidth="1.2" />
                  {isPinned && !hoverId && (
                    <circle cx={p.x} cy={p.y} r="10" fill="none"
                      stroke="var(--ivy-accent)" strokeWidth="0.8" opacity="0.5" />
                  )}
                  <text x={p.x} y={p.above ? p.y - 12 : p.y + 16}
                    fontSize="9" fontFamily="ui-monospace,monospace" textAnchor="middle"
                    fill={isActive ? "var(--ivy-accent)" : "var(--ivy-inkMute)"}
                    style={{ letterSpacing: "0.5px" }}>
                    {p.event_id}
                  </text>
                  {p.inferred_year && (
                    <text x={p.x} y={p.above ? p.y - 26 : p.y + 30}
                      fontSize="9" fontFamily="ui-monospace,monospace" textAnchor="middle"
                      fill="var(--ivy-inkFaint)">
                      {p.inferred_year}
                    </text>
                  )}
                  {/* hit area */}
                  <circle cx={p.x} cy={p.y} r="14" fill="transparent"
                    onMouseEnter={() => setHoverId(p.event_id)}
                    onMouseLeave={() => setHoverId(null)}
                    onClick={() => setPinId(p.event_id)}
                    style={{ cursor: "pointer" }}
                  />
                </g>
              );
            })}

            <text x={padX} y={spineY - 178} fontSize="9" fontFamily="ui-monospace,monospace"
              fill="var(--ivy-inkFaint)" letterSpacing="1">
              ABOVE THE LINE — EARLIER STORY ORDER WITHIN PAIR
            </text>
            <text x={padX} y={spineY + 188} fontSize="9" fontFamily="ui-monospace,monospace"
              fill="var(--ivy-inkFaint)" letterSpacing="1">
              BELOW THE LINE — LATER STORY ORDER WITHIN PAIR
            </text>
          </svg>
        </div>
      </div>

      {/* Detail rail + legend */}
      <div className="grid grid-cols-12 gap-6 mt-6">
        <div className="col-span-8">
          {active && <EventDetail event={active} pinned={active.event_id === pinId} />}
        </div>
        <div className="col-span-4">
          <TimelineLegend />
          <div className="mt-4">
            <p className="font-mono text-[10px] uppercase tracking-[0.22em] mb-3 text-ivy-inkFaint">navigate</p>
            <div className="flex flex-wrap gap-1">
              {events.map((e) => (
                <button
                  key={e.event_id}
                  onMouseEnter={() => setHoverId(e.event_id)}
                  onMouseLeave={() => setHoverId(null)}
                  onClick={() => setPinId(e.event_id)}
                  className="font-mono text-[10px] px-1.5 py-0.5 rounded-sm border border-ivy-rule"
                  style={{
                    color:      e.event_id === activeId ? "var(--ivy-bgRaised)" : "var(--ivy-inkMute)",
                    background: e.event_id === activeId ? "var(--ivy-accent)"   : "transparent",
                  }}
                >
                  {e.event_id}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
