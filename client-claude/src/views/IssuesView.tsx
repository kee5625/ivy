import { useState } from "react";
import { Mono, ViewHeader } from "@/components/atoms";
import { SevDot } from "@/components/atoms";
import { IconArrowRight } from "@/components/icons";
import type { PlotHole, TimelineEvent } from "@/types/graph";

/* ── Triage matrix scatter plot ──────────────────────────────── */
function TriageMatrix({
  holes,
  activeId,
  setActiveId,
}: {
  holes: PlotHole[];
  activeId: string;
  setActiveId: (id: string) => void;
}) {
  const W = 540, H = 320, padL = 60, padR = 16, padT = 16, padB = 44;
  const innerW = W - padL - padR, innerH = H - padT - padB;

  const sevToY = (sev: string) => {
    const map: Record<string, number> = { low: 0.2, medium: 0.5, high: 0.85 };
    return padT + innerH - (map[sev] ?? 0.2) * innerH;
  };
  const confToX = (c: number) => padL + c * innerW;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ height: H }}>
      {/* grid */}
      {[0.25, 0.5, 0.75, 1].map((t) => (
        <line key={t} x1={padL + t * innerW} y1={padT} x2={padL + t * innerW} y2={padT + innerH}
          stroke="var(--ivy-ruleSoft)" strokeWidth="0.6" strokeDasharray="2 3" />
      ))}
      {[0.2, 0.5, 0.85].map((t) => (
        <line key={t} x1={padL} y1={padT + innerH - t * innerH} x2={padL + innerW} y2={padT + innerH - t * innerH}
          stroke="var(--ivy-ruleSoft)" strokeWidth="0.6" strokeDasharray="2 3" />
      ))}
      {/* axes */}
      <line x1={padL} y1={padT} x2={padL} y2={padT + innerH} stroke="var(--ivy-inkDeep)" strokeWidth="1" />
      <line x1={padL} y1={padT + innerH} x2={padL + innerW} y2={padT + innerH} stroke="var(--ivy-inkDeep)" strokeWidth="1" />
      {/* y labels */}
      {(["high", "medium", "low"] as const).map((s, idx) => {
        const t = [0.85, 0.5, 0.2][idx];
        return (
          <text key={s} x={padL - 10} y={padT + innerH - t * innerH + 4}
            textAnchor="end" fontSize="10" fontFamily="ui-monospace,monospace" fill="var(--ivy-inkMute)">
            {s}
          </text>
        );
      })}
      {/* x labels */}
      {[0, 0.5, 1].map((t) => (
        <text key={t} x={padL + t * innerW} y={padT + innerH + 18}
          textAnchor="middle" fontSize="10" fontFamily="ui-monospace,monospace" fill="var(--ivy-inkMute)">
          {Math.round(t * 100)}%
        </text>
      ))}
      <text x={padL + innerW / 2} y={H - 6} textAnchor="middle" fontSize="9"
        fontFamily="ui-monospace,monospace" fill="var(--ivy-inkFaint)" letterSpacing="1.5">
        CONFIDENCE →
      </text>
      <text x={14} y={padT + innerH / 2} fontSize="9" fontFamily="ui-monospace,monospace"
        fill="var(--ivy-inkFaint)" letterSpacing="1.5"
        transform={`rotate(-90, 14, ${padT + innerH / 2})`}>
        SEVERITY →
      </text>
      {/* points */}
      {holes.map((h) => {
        const x = confToX(h.confidence);
        const y = sevToY(h.severity);
        const isActive = activeId === h.hole_id;
        const c = h.severity === "high" ? "var(--ivy-sevHigh)"
                : h.severity === "medium" ? "var(--ivy-sevMed)" : "var(--ivy-sevLow)";
        return (
          <g key={h.hole_id} onClick={() => setActiveId(h.hole_id)} style={{ cursor: "pointer" }}>
            {isActive && <circle cx={x} cy={y} r="13" fill="none" stroke={c} strokeWidth="1" opacity="0.4" />}
            <circle cx={x} cy={y} r={isActive ? 7 : 5}
              fill={isActive ? c : "var(--ivy-bgRaised)"} stroke={c} strokeWidth="1.4" />
            <text x={x + 10} y={y + 3} fontSize="9" fontFamily="ui-monospace,monospace"
              fill={isActive ? "var(--ivy-inkDeep)" : "var(--ivy-inkMute)"}>
              {h.hole_id}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

/* ── Chapter heatmap ─────────────────────────────────────────── */
function ChapterHeatmap({
  holes,
  totalChapters,
  activeId,
  setActiveId,
}: {
  holes: PlotHole[];
  totalChapters: number;
  activeId: string;
  setActiveId: (id: string) => void;
}) {
  const sevRank: Record<string, number> = { high: 3, medium: 2, low: 1 };
  const cols = Array.from({ length: totalChapters }, (_, i) => {
    const ch = i + 1;
    const issues = holes.filter((h) => h.chapters_involved.includes(ch));
    return { ch, issues };
  });

  return (
    <div>
      <div className="grid gap-1" style={{ gridTemplateColumns: `repeat(${totalChapters}, minmax(0, 1fr))` }}>
        {cols.map((col) => {
          const top = [...col.issues].sort((a, b) => sevRank[b.severity] - sevRank[a.severity]);
          return (
            <div key={col.ch} className="flex flex-col gap-1">
              <div className="flex flex-col gap-0.5" style={{ minHeight: 96 }}>
                {top.length === 0 ? (
                  <div className="border border-ivy-ruleSoft bg-ivy-bgInk" style={{ height: 14 }} />
                ) : top.map((h) => {
                  const c = h.severity === "high" ? "var(--ivy-sevHigh)"
                          : h.severity === "medium" ? "var(--ivy-sevMed)" : "var(--ivy-sevLow)";
                  return (
                    <button
                      key={h.hole_id}
                      onClick={() => setActiveId(h.hole_id)}
                      title={`${h.hole_id} · ${h.hole_type}`}
                      style={{
                        height: 14,
                        background: c,
                        opacity: activeId === h.hole_id ? 1 : 0.85,
                        outline: activeId === h.hole_id ? "1.5px solid var(--ivy-inkDeep)" : "none",
                        outlineOffset: 1,
                      }}
                    />
                  );
                })}
              </div>
              <Mono className="text-[10px] text-center text-ivy-inkFaint">
                {String(col.ch).padStart(2, "0")}
              </Mono>
            </div>
          );
        })}
      </div>
      <div className="flex items-center gap-3 mt-3 text-[11px] text-ivy-inkMute">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 bg-ivy-sevHigh" />high
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 bg-ivy-sevMed" />medium
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 bg-ivy-sevLow" />low
        </span>
        <span className="ml-auto font-mono text-[10px] uppercase tracking-[0.18em] text-ivy-inkFaint">
          each block = 1 issue · click to focus
        </span>
      </div>
    </div>
  );
}

/* ── Issue detail panel ──────────────────────────────────────── */
function IssueDetail({ hole, events }: { hole: PlotHole; events: TimelineEvent[] }) {
  const involved = events.filter((e) => hole.events_involved.includes(e.event_id));
  return (
    <article className="rounded-sm border border-ivy-rule bg-ivy-bgRaised">
      <div className="px-5 py-4 border-b border-ivy-ruleSoft">
        <div className="flex items-center gap-2 mb-2">
          <Mono className="text-[11px] px-1.5 py-0.5 rounded-sm bg-ivy-accentSoft text-ivy-accentInk">
            {hole.hole_id}
          </Mono>
          <span className="font-mono text-[10px] uppercase tracking-[0.18em] text-ivy-inkFaint">
            {hole.hole_type}
          </span>
          <span className="ml-auto inline-flex items-center gap-1.5 text-[11px] font-mono uppercase tracking-[0.16em] text-ivy-ink">
            <SevDot level={hole.severity} /> {hole.severity}
          </span>
        </div>
        <p className="font-serif text-[16px] leading-relaxed text-ivy-inkDeep">{hole.description}</p>
      </div>

      <div className="px-5 py-4 space-y-4">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.22em] mb-2 text-ivy-inkFaint">
            chapters cross-referenced
          </p>
          <div className="flex flex-wrap gap-1.5">
            {hole.chapters_involved.map((c) => (
              <span key={c} className="text-[12px] px-2 py-0.5 rounded-sm border border-ivy-rule text-ivy-ink">
                Ch. {String(c).padStart(2, "0")}
              </span>
            ))}
          </div>
        </div>
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.22em] mb-2 text-ivy-inkFaint">
            characters involved
          </p>
          <div className="flex flex-wrap gap-1.5">
            {hole.characters_involved.map((c) => (
              <span key={c} className="text-[12px] px-2 py-0.5 rounded-sm border border-ivy-rule text-ivy-ink">
                {c}
              </span>
            ))}
          </div>
        </div>
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.22em] mb-2 text-ivy-inkFaint">
            evidence trail
          </p>
          <ul className="space-y-2.5">
            {involved.map((e) => (
              <li key={e.event_id} className="grid gap-3 text-[13px]"
                style={{ gridTemplateColumns: "60px minmax(0,1fr)" }}>
                <div>
                  <Mono className="text-[11px] text-ivy-accent">{e.event_id}</Mono>
                  <p className="font-mono text-[10px] text-ivy-inkFaint">ch.{e.chapter_num}</p>
                </div>
                <p className="text-ivy-ink">{e.description}</p>
              </li>
            ))}
          </ul>
        </div>
        <div className="flex items-center justify-between border-t border-ivy-ruleSoft pt-3">
          <span className="font-mono text-[11px] text-ivy-inkMute">
            confidence <span className="text-ivy-inkDeep">{Math.round(hole.confidence * 100)}%</span>
          </span>
          <div className="flex gap-2">
            <button className="text-[12px] px-3 py-1.5 rounded-sm border border-ivy-rule text-ivy-inkMute">
              Dismiss
            </button>
          </div>
        </div>
      </div>
    </article>
  );
}

/* ── Issues view ─────────────────────────────────────────────── */
export default function IssuesView({
  holes,
  events,
}: {
  holes: PlotHole[];
  events: TimelineEvent[];
}) {
  const [activeId, setActiveId] = useState(holes[0]?.hole_id ?? "");
  const active = holes.find((h) => h.hole_id === activeId);

  const counts = {
    high:   holes.filter((h) => h.severity === "high").length,
    medium: holes.filter((h) => h.severity === "medium").length,
    low:    holes.filter((h) => h.severity === "low").length,
  };

  const totalChapters = Math.max(
    0,
    ...holes.flatMap((h) => h.chapters_involved)
  );

  if (holes.length === 0) {
    return (
      <div className="px-10 py-8">
        <ViewHeader title="Issues" />
        <p className="text-ivy-inkMute text-[14px]">No issues found.</p>
      </div>
    );
  }

  return (
    <div className="px-10 py-8 max-w-[1300px] mx-auto">
      <ViewHeader
        title="Issues"
        subtitle="Cross-referenced contradictions, unresolved setups, and temporal paradoxes"
        stats={[
          { v: holes.length,   l: "Total flagged" },
          { v: counts.high,    l: "High severity" },
          { v: counts.medium,  l: "Medium" },
          { v: counts.low,     l: "Low" },
        ]}
      />

      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-7">
          {/* Triage matrix */}
          <div className="rounded-sm p-5 border border-ivy-rule bg-ivy-bgRaised">
            <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-ivy-inkFaint">fig. 02</p>
            <h3 className="font-serif text-[18px] text-ivy-inkDeep">Triage matrix</h3>
            <p className="text-[12px] mt-0.5 mb-4 text-ivy-inkMute">
              Severity × confidence — top-right deserves first attention
            </p>
            <TriageMatrix holes={holes} activeId={activeId} setActiveId={setActiveId} />
          </div>

          {/* Chapter heatmap */}
          <div className="mt-6 rounded-sm p-5 border border-ivy-rule bg-ivy-bgRaised">
            <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-ivy-inkFaint">fig. 03</p>
            <h3 className="font-serif text-[18px] mb-3 text-ivy-inkDeep">Where issues cluster</h3>
            <ChapterHeatmap
              holes={holes}
              totalChapters={Math.max(totalChapters, 10)}
              activeId={activeId}
              setActiveId={setActiveId}
            />
          </div>

          {/* List */}
          <div className="mt-6 rounded-sm border border-ivy-rule bg-ivy-bgRaised">
            <div
              className="grid items-center gap-3 px-5 py-2.5 text-[10px] font-mono uppercase tracking-[0.18em] text-ivy-inkFaint border-b border-ivy-rule"
              style={{ gridTemplateColumns: "44px minmax(0,1fr) 120px 70px 70px 24px" }}
            >
              <span>id</span><span>type</span><span>severity</span>
              <span className="text-right">conf.</span><span className="text-right">ch.</span><span />
            </div>
            {holes.map((h, i) => (
              <button
                key={h.hole_id}
                onClick={() => setActiveId(h.hole_id)}
                className="grid items-center gap-3 w-full px-5 py-3 text-left"
                style={{
                  gridTemplateColumns: "44px minmax(0,1fr) 120px 70px 70px 24px",
                  borderBottom: i < holes.length - 1 ? "1px solid var(--ivy-ruleSoft)" : "none",
                  background: activeId === h.hole_id ? "var(--ivy-bgInk)" : "transparent",
                }}
              >
                <Mono
                  className="text-[11px]"
                  style={{ color: activeId === h.hole_id ? "var(--ivy-accent)" : "var(--ivy-inkMute)" }}
                >
                  {h.hole_id}
                </Mono>
                <span className="text-[13px] truncate text-ivy-inkDeep">{h.hole_type}</span>
                <span className="flex items-center gap-1.5 text-[12px] text-ivy-ink">
                  <SevDot level={h.severity} /> {h.severity}
                </span>
                <Mono className="text-[12px] text-right text-ivy-ink">
                  {Math.round(h.confidence * 100)}%
                </Mono>
                <Mono className="text-[12px] text-right text-ivy-inkMute">
                  {h.chapters_involved.length}
                </Mono>
                <span style={{ color: activeId === h.hole_id ? "var(--ivy-accent)" : "var(--ivy-inkFaint)" }}>
                  <IconArrowRight />
                </span>
              </button>
            ))}
          </div>
        </div>

        {/* Evidence panel */}
        <div className="col-span-5">
          {active && <IssueDetail hole={active} events={events} />}
        </div>
      </div>
    </div>
  );
}
