import { useEffect, useRef, useState } from "react";
import { Mono, ViewHeader, DetailField } from "@/components/atoms";
import type { TimelineEvent } from "@/types/graph";

const EVENT_ID_PATTERN = /(?:C\d{2}-E\d{2}|E\d{3}|evt_\d{3})/g;

function formatBeatLabel(order: number): string {
  return `Beat ${String(order).padStart(2, "0")}`;
}

function formatChapterLabel(chapterNum: number): string {
  return `Chapter ${String(chapterNum).padStart(2, "0")}`;
}

function dedupeCharacters(chars: string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  chars.forEach((c) => {
    const trimmed = c.trim();
    if (!trimmed) return;
    const key = trimmed.toLowerCase();
    if (seen.has(key)) return;
    seen.add(key);
    out.push(trimmed);
  });
  return out;
}

function formatRelativeAnchor(value: string, lookup: Record<string, TimelineEvent>): string {
  let out = value.replace(/[0-9a-f]{8}_/gi, "");
  const ids = Object.keys(lookup).sort((a, b) => b.length - a.length);
  ids.forEach((id) => {
    if (!out.includes(id)) return;
    const e = lookup[id];
    const label = `${formatBeatLabel(e.order)} (Ch ${String(e.chapter_num).padStart(2, "0")})`;
    out = out.split(id).join(label);
  });
  return out.replace(EVENT_ID_PATTERN, "a related beat");
}

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
  lookup,
  onSelectEvent,
}: {
  event: TimelineEvent;
  pinned: boolean;
  lookup: Record<string, TimelineEvent>;
  onSelectEvent?: (id: string) => void;
}) {
  const beatLabel = formatBeatLabel(event.order);
  const chapterLabel = formatChapterLabel(event.chapter_num);
  const uniqueCharacters = dedupeCharacters(event.characters_present);
  const causedByIds = new Set(event.caused_by);
  const leadsToIds = new Set(event.causes);

  Object.values(lookup).forEach((e) => {
    if (e.event_id === event.event_id) return;
    if (e.causes.includes(event.event_id)) causedByIds.add(e.event_id);
    if (e.caused_by.includes(event.event_id)) leadsToIds.add(e.event_id);
  });

  const causedByEvents = Array.from(causedByIds)
    .map((id) => lookup[id])
    .filter((e): e is TimelineEvent => Boolean(e))
    .sort((a, b) => a.order - b.order);
  const causesEvents = Array.from(leadsToIds)
    .map((id) => lookup[id])
    .filter((e): e is TimelineEvent => Boolean(e))
    .sort((a, b) => a.order - b.order);
  const rawWhen = event.time_reference ?? event.inferred_date ?? event.relative_time_anchor;
  const whenValue = rawWhen ? formatRelativeAnchor(rawWhen, lookup) : "—";
  return (
    <article className="rounded-sm border border-ivy-rule bg-ivy-bgRaised">
      <div className="px-5 py-4 flex items-start justify-between gap-4 border-b border-ivy-ruleSoft">
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <Mono className="text-[11px] px-1.5 py-0.5 rounded-sm bg-ivy-accentSoft text-ivy-accentInk">
              {beatLabel}
            </Mono>
            <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-ivy-inkFaint">
              {chapterLabel}
            </span>
            {!pinned && (
              <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-ivy-inkFaint">
                · hover preview
              </span>
            )}
          </div>
          <h3 className="font-serif text-[20px] leading-snug text-ivy-inkDeep">{event.description}</h3>
          <p className="text-[12px] mt-1 text-ivy-inkMute">
            {chapterLabel} · "{event.chapter_title || "Untitled chapter"}"
          </p>
        </div>
        <div className="flex flex-col items-end gap-1.5 shrink-0">
          <ConfidenceMeter value={event.confidence} />
          <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-ivy-inkFaint">
            model confidence
          </span>
        </div>
      </div>

      <div className="grid grid-cols-[1fr_1fr_2fr] px-5 py-4 gap-6">
        <DetailField label="When">
          {whenValue}
          {event.inferred_year && (
            <Mono className="ml-2 text-[11px] text-ivy-inkFaint">({event.inferred_year})</Mono>
          )}
        </DetailField>
        <DetailField label="Where">{event.location ?? "—"}</DetailField>
        <DetailField label="Who">
          {uniqueCharacters.length === 0 ? (
            <span className="text-ivy-inkFaint">—</span>
          ) : (
            <div className="flex flex-wrap gap-1 mt-0.5">
              {uniqueCharacters.map((c) => (
                <span key={c} className="text-[12px] px-1.5 py-0.5 rounded-sm border border-ivy-rule">
                  {c}
                </span>
              ))}
            </div>
          )}
        </DetailField>
      </div>

      <div className="grid grid-cols-2 px-5 pb-5 gap-6">
        <DetailField label={`Caused by (${causedByEvents.length})`}>
          {causedByEvents.length === 0 ? (
            <span className="text-ivy-inkFaint">No earlier beats referenced</span>
          ) : (
            <div className="space-y-2">
              {causedByEvents.map((e) => (
                <button
                  key={e.event_id}
                  onClick={() => onSelectEvent?.(e.event_id)}
                  className="w-full text-left rounded-sm border border-ivy-ruleSoft px-2 py-1.5 hover:bg-ivy-bgInk"
                >
                  <div className="text-[12px] text-ivy-inkDeep leading-snug">{e.description}</div>
                  <Mono className="text-[10px] text-ivy-inkFaint mt-1">
                    {formatBeatLabel(e.order)} · {formatChapterLabel(e.chapter_num)}
                  </Mono>
                </button>
              ))}
            </div>
          )}
        </DetailField>
        <DetailField label={`Leads to (${causesEvents.length})`}>
          {causesEvents.length === 0 ? (
            <span className="text-ivy-inkFaint">No later beats referenced</span>
          ) : (
            <div className="space-y-2">
              {causesEvents.map((e) => (
                <button
                  key={e.event_id}
                  onClick={() => onSelectEvent?.(e.event_id)}
                  className="w-full text-left rounded-sm border border-ivy-ruleSoft px-2 py-1.5 hover:bg-ivy-bgInk"
                >
                  <div className="text-[12px] text-ivy-inkDeep leading-snug">{e.description}</div>
                  <Mono className="text-[10px] text-ivy-inkFaint mt-1">
                    {formatBeatLabel(e.order)} · {formatChapterLabel(e.chapter_num)}
                  </Mono>
                </button>
              ))}
            </div>
          )}
        </DetailField>
      </div>
    </article>
  );
}


/* ── Timeline view ────────────────────────────────────────────── */
export default function TimelineView({ events: rawEvents }: { events: TimelineEvent[] }) {
  const events = [...rawEvents].sort((a, b) => a.order - b.order);
  const [hoverId, setHoverId] = useState<string | null>(null);
  const [pinId, setPinId] = useState<string>(events[0]?.event_id ?? "");
  const activeId = hoverId ?? pinId;
  const active = events.find((e) => e.event_id === activeId);
  const eventById = Object.fromEntries(events.map((e) => [e.event_id, e]));

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
        subtitle="Hover to preview a beat, click to pin it for close reading."
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
            
          </svg>
        </div>
      </div>

      {/* Detail rail + legend */}
      <div className="grid grid-cols-12 gap-6 mt-6">
        <div className="col-span-8">
          {active && (
            <EventDetail
              event={active}
              pinned={active.event_id === pinId}
              lookup={eventById}
              onSelectEvent={(id) => setPinId(id)}
            />
          )}
        </div>
        <div className="col-span-4">
          <div className="">
            <p className="font-mono text-[10px] uppercase tracking-[0.22em] mb-3 text-ivy-inkFaint">beats</p>
            <div className="space-y-2 pr-2" style={{ maxHeight: 520, overflowY: "auto" }}>
              {events.map((e) => {
                const isActive = e.event_id === activeId;
                return (
                  <button
                    key={e.event_id}
                    onMouseEnter={() => setHoverId(e.event_id)}
                    onMouseLeave={() => setHoverId(null)}
                    onClick={() => setPinId(e.event_id)}
                    className="w-full text-left rounded-sm border px-3 py-2"
                    style={{
                      borderColor: isActive ? "var(--ivy-accent)" : "var(--ivy-rule)",
                      background: isActive ? "var(--ivy-bgInk)" : "transparent",
                    }}
                  >
                    <div className="flex items-center justify-between">
                      <Mono className="text-[10px] uppercase tracking-[0.18em] text-ivy-inkMute">
                        Beat {String(e.order).padStart(2, "0")}
                      </Mono>
                      <Mono className="text-[10px] text-ivy-inkFaint">
                        Chapter {String(e.chapter_num).padStart(2, "0")}
                      </Mono>
                    </div>
                    <div className="text-[13px] text-ivy-inkDeep leading-snug mt-1">
                      {e.description}
                    </div>
                    <Mono className="text-[10px] text-ivy-inkFaint mt-1">
                      {e.chapter_title || "Untitled chapter"}
                    </Mono>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
