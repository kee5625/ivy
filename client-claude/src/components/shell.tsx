import { Hairline } from "@/components/atoms";
import {
  IconLibrary,
  IconManuscript,
  IconTimeline,
  IconIssues,
  IconCharacters,
} from "@/components/icons";
import type { Job } from "@/types/graph";

/* ── Nav items ───────────────────────────────────────────────── */
export type ViewKey = "library" | "manuscript" | "timeline" | "issues" | "characters";

const NAV: { key: ViewKey; label: string; Icon: React.ComponentType }[] = [
  { key: "library",    label: "Library",    Icon: IconLibrary },
  { key: "manuscript", label: "Manuscript", Icon: IconManuscript },
  { key: "timeline",   label: "Timeline",   Icon: IconTimeline },
  { key: "issues",     label: "Issues",     Icon: IconIssues },
  { key: "characters", label: "Characters", Icon: IconCharacters },
];

/* ── TopBar ──────────────────────────────────────────────────── */
export function TopBar({ manuscriptTitle }: { manuscriptTitle?: string }) {
  return (
    <header className="flex items-center justify-between px-6 h-14 border-b border-ivy-rule bg-ivy-bgRaised shrink-0">
      <div className="flex items-center gap-3">
        {/* Ivy logomark */}
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="1.5" className="text-ivy-accent">
          <path d="M5 19c8 0 14-6 14-14"/>
          <circle cx="5" cy="19" r="1.5" fill="currentColor"/>
          <circle cx="19" cy="5" r="1.5" fill="currentColor"/>
          <circle cx="12" cy="12" r="1.2" fill="currentColor"/>
        </svg>
        <span className="font-serif text-[18px] tracking-tight text-ivy-inkDeep">Ivy</span>
        <span className="text-[11px] font-mono uppercase tracking-[0.18em] text-ivy-inkFaint">
          manuscript intelligence
        </span>
      </div>

      <span className="text-[12px] text-ivy-inkMute">
        {manuscriptTitle ? (
          <>Working on <em className="not-italic text-ivy-inkDeep">{manuscriptTitle}</em></>
        ) : (
          "No manuscript open"
        )}
      </span>
    </header>
  );
}

/* ── Sidebar ─────────────────────────────────────────────────── */
export function Sidebar({
  view,
  setView,
  job,
  manuscriptTitle,
}: {
  view: ViewKey;
  setView: (v: ViewKey) => void;
  job: Job | null;
  manuscriptTitle?: string;
}) {
  return (
    <aside className="flex flex-col w-[224px] shrink-0 border-r border-ivy-rule bg-ivy-bgRaised">
      <nav className="flex flex-col py-4 gap-0.5">
        {NAV.map((n) => {
          const active = view === n.key;
          return (
            <button
              key={n.key}
              onClick={() => setView(n.key)}
              className="relative flex items-center gap-3 mx-3 px-3 py-2 rounded-sm text-[13px] text-left transition-colors"
              style={{
                background: active ? "var(--ivy-bgInk)" : "transparent",
                color: active ? "var(--ivy-inkDeep)" : "var(--ivy-inkMute)",
                fontWeight: active ? 600 : 500,
              }}
            >
              {active && (
                <span className="absolute left-0 top-2 bottom-2 w-[2px] rounded-r bg-ivy-accent" />
              )}
              <n.Icon />
              <span>{n.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="mt-auto px-4 py-4 space-y-3">
        <Hairline />
        <div>
          <p className="text-[10px] font-mono uppercase tracking-[0.2em] mb-2 text-ivy-inkFaint">
            current manuscript
          </p>
          {manuscriptTitle ? (
            <div>
              <p className="font-serif text-[14px] leading-tight text-ivy-inkDeep">{manuscriptTitle}</p>
            </div>
          ) : (
            <p className="text-[12px] text-ivy-inkFaint">None open</p>
          )}
        </div>
        <PipelineStatus job={job} />
      </div>
    </aside>
  );
}

/* ── Pipeline status ─────────────────────────────────────────── */
const STAGES = [
  { key: "ingestion",  label: "Ingest" },
  { key: "timeline",   label: "Timeline" },
  { key: "plot_hole",  label: "Issues" },
] as const;

function statusToIdx(status: string | undefined): number {
  if (!status) return -1;
  if (status.startsWith("plot_hole"))   return status === "plot_hole_complete" ? 3 : 2;
  if (status.startsWith("timeline"))    return status === "timeline_complete"   ? 2 : 1;
  if (status.startsWith("ingestion"))   return status === "ingestion_complete"  ? 1 : 0;
  return -1;
}

function PipelineStatus({ job }: { job: Job | null }) {
  const idx = statusToIdx(job?.status);
  const failed = job?.status === "failed";

  return (
    <div>
      <p className="text-[10px] font-mono uppercase tracking-[0.2em] mb-2 text-ivy-inkFaint">pipeline</p>
      <div className="flex flex-col gap-1.5">
        {STAGES.map((s, i) => {
          const done   = i < idx;
          const active = i === idx;
          return (
            <div key={s.key} className="flex items-center gap-2 text-[11px]">
              <span
                className="h-1.5 w-1.5 rounded-full"
                style={{
                  background: failed && active ? "var(--ivy-sevHigh)" :
                               done || active  ? "var(--ivy-accent)"  : "var(--ivy-rule)",
                  boxShadow: active && !failed
                    ? "0 0 0 3px color-mix(in oklch, var(--ivy-accent) 18%, transparent)"
                    : "none",
                }}
              />
              <span
                style={{
                  color: done || active ? "var(--ivy-inkDeep)" : "var(--ivy-inkFaint)",
                }}
              >
                {s.label}
              </span>
              {active && !failed && (
                <span className="font-mono text-[10px] ml-auto text-ivy-inkMute">running</span>
              )}
              {done && (
                <span className="font-mono text-[10px] ml-auto text-ivy-inkFaint">done</span>
              )}
            </div>
          );
        })}
      </div>
      {failed && (
        <p className="mt-2 text-[11px] font-mono text-ivy-sevHigh">Pipeline failed</p>
      )}
    </div>
  );
}
