import { useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useJobPolling } from "@/hooks/useJobPolling";
import { isResultsReady } from "@/types/graph";

const STAGES = [
  { key: "ingestion",  label: "Ingestion",  desc: "Parse PDF and extract chapter summaries" },
  { key: "timeline",   label: "Timeline",   desc: "Merge events into a global chronology" },
  { key: "plot_hole",  label: "Issues",     desc: "Flag contradictions and unresolved setups" },
] as const;

function stageIndex(status: string): number {
  if (status.startsWith("plot_hole"))  return status === "plot_hole_complete"  ? 3 : 2;
  if (status.startsWith("timeline"))   return status === "timeline_complete"   ? 2 : 1;
  if (status.startsWith("ingestion"))  return status === "ingestion_complete"  ? 1 : 0;
  return -1;
}

export default function GraphPage() {
  const { jobId = "" } = useParams<{ jobId: string }>();
  const { job, isLoading, error } = useJobPolling(jobId);
  const navigate = useNavigate();

  // Save to recent jobs
  useEffect(() => {
    if (!jobId) return;
    const prev: string[] = JSON.parse(localStorage.getItem("ivy-recent-jobs") ?? "[]") as string[];
    if (!prev.includes(jobId)) {
      localStorage.setItem("ivy-recent-jobs", JSON.stringify([jobId, ...prev].slice(0, 20)));
    }
  }, [jobId]);

  // Redirect when done
  useEffect(() => {
    if (job && isResultsReady(job.status)) {
      navigate(`/results/${jobId}`);
    }
  }, [job, jobId, navigate]);

  const idx = job ? stageIndex(job.status) : -1;
  const failed = job?.status === "failed";

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center px-6"
      style={{ background: "var(--ivy-bg)" }}
    >
      {/* Logomark */}
      <div className="flex items-center gap-3 mb-12">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="1.5" style={{ color: "var(--ivy-accent)" }}>
          <path d="M5 19c8 0 14-6 14-14" />
          <circle cx="5" cy="19" r="1.5" fill="currentColor" />
          <circle cx="19" cy="5" r="1.5" fill="currentColor" />
          <circle cx="12" cy="12" r="1.2" fill="currentColor" />
        </svg>
        <span className="font-serif text-[22px] tracking-tight" style={{ color: "var(--ivy-inkDeep)" }}>
          Ivy
        </span>
      </div>

      <div className="w-full max-w-md">
        <p className="font-mono text-[10px] uppercase tracking-[0.28em] mb-2 text-center" style={{ color: "var(--ivy-inkFaint)" }}>
          analysing manuscript
        </p>
        <h2 className="font-serif text-[28px] text-center mb-8" style={{ color: "var(--ivy-inkDeep)" }}>
          {isLoading ? "Starting…" : failed ? "Pipeline failed" : "Running pipeline"}
        </h2>

        {/* Pipeline steps */}
        <div
          className="rounded-sm p-6 space-y-4"
          style={{ border: "1px solid var(--ivy-rule)", background: "var(--ivy-bgRaised)" }}
        >
          {STAGES.map((s, i) => {
            const done   = i < idx;
            const active = i === idx && !failed;
            return (
              <div key={s.key} className="flex items-start gap-4">
                <div className="flex flex-col items-center" style={{ minWidth: 20 }}>
                  <span
                    className="h-3 w-3 rounded-full mt-0.5"
                    style={{
                      background: failed && active ? "var(--ivy-sevHigh)" :
                                  done || active   ? "var(--ivy-accent)"  : "var(--ivy-rule)",
                      boxShadow: active
                        ? "0 0 0 4px color-mix(in oklch, var(--ivy-accent) 16%, transparent)"
                        : "none",
                    }}
                  />
                  {i < STAGES.length - 1 && (
                    <div
                      className="w-px mt-1 flex-1"
                      style={{
                        height: 28,
                        background: done ? "var(--ivy-accent)" : "var(--ivy-ruleSoft)",
                      }}
                    />
                  )}
                </div>
                <div className="flex-1 pb-1">
                  <div className="flex items-center justify-between">
                    <p
                      className="text-[13px] font-medium"
                      style={{ color: done || active ? "var(--ivy-inkDeep)" : "var(--ivy-inkFaint)" }}
                    >
                      {s.label}
                    </p>
                    {active && (
                      <span className="font-mono text-[10px] uppercase tracking-[0.18em]" style={{ color: "var(--ivy-accent)" }}>
                        running
                      </span>
                    )}
                    {done && (
                      <span className="font-mono text-[10px] uppercase tracking-[0.18em]" style={{ color: "var(--ivy-inkFaint)" }}>
                        done
                      </span>
                    )}
                  </div>
                  <p className="text-[12px] mt-0.5" style={{ color: "var(--ivy-inkMute)" }}>
                    {s.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>

        {/* Job ID */}
        <p className="mt-6 text-center font-mono text-[11px]" style={{ color: "var(--ivy-inkFaint)" }}>
          job <span style={{ color: "var(--ivy-inkMute)" }}>{jobId}</span>
        </p>

        {/* Error */}
        {(error ?? (failed && job?.error)) && (
          <div
            className="mt-4 px-4 py-3 rounded-sm text-[13px]"
            style={{ background: "var(--ivy-accentSoft)", border: "1px solid var(--ivy-accent)", color: "var(--ivy-accentInk)" }}
          >
            {error ?? job?.error}
          </div>
        )}
      </div>
    </div>
  );
}
