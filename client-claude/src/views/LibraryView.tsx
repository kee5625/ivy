import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { uploadPdfDirectToR2, createJob } from "@/api/upload";
import { IconUpload, IconArrowRight } from "@/components/icons";
import { Mono } from "@/components/atoms";

/* ── Status pill ─────────────────────────────────────────────── */
const STATUS_MAP: Record<string, { label: string; accent: boolean }> = {
  complete:                { label: "Complete",       accent: false },
  plot_hole_complete:      { label: "Complete",       accent: false },
  timeline_in_progress:    { label: "Timeline · 2/3", accent: true },
  ingestion_in_progress:   { label: "Ingesting · 1/3",accent: true },
  plot_hole_in_progress:   { label: "Issues · 3/3",   accent: true },
};

function StatusPill({ status }: { status: string }) {
  const s = STATUS_MAP[status] ?? STATUS_MAP["complete"];
  return (
    <span
      className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-sm text-[11px] font-medium border border-ivy-ruleSoft"
      style={{
        color:      s.accent ? "var(--ivy-accentInk)" : "var(--ivy-inkDeep)",
        background: s.accent ? "var(--ivy-accentSoft)" : "var(--ivy-bgInk)",
      }}
    >
      <span
        className="h-1.5 w-1.5 rounded-full"
        style={{ background: s.accent ? "var(--ivy-accent)" : "var(--ivy-inkMute)" }}
      />
      {s.label}
    </span>
  );
}

/* ── Decorative figure ───────────────────────────────────────── */
function FigureGraphic() {
  return (
    <figure className="relative" style={{ height: 220 }}>
      <svg viewBox="0 0 420 220" className="w-full h-full">
        <defs>
          <pattern id="dots" width="6" height="6" patternUnits="userSpaceOnUse">
            <circle cx="0.5" cy="0.5" r="0.5" fill="var(--ivy-rule)" />
          </pattern>
        </defs>
        <rect x="0" y="0" width="420" height="220" fill="url(#dots)" opacity="0.5" />
        <line x1="20" y1="120" x2="400" y2="120" stroke="var(--ivy-inkDeep)" strokeWidth="1.2" />
        {Array.from({ length: 11 }, (_, i) => (
          <line key={i} x1={20 + i * 38} y1="116" x2={20 + i * 38} y2="124"
            stroke="var(--ivy-inkMute)" strokeWidth="1" />
        ))}
        {([
          [60, 80, 0.9], [98, 60, 0.7], [136, 90, 0.5], [174, 50, 0.95],
          [212, 75, 0.6], [250, 95, 0.8], [288, 65, 0.55], [326, 85, 0.75], [364, 70, 0.65],
        ] as [number, number, number][]).map(([x, y, op], i) => (
          <g key={i}>
            <line x1={x} y1="120" x2={x} y2={y} stroke="var(--ivy-inkMute)" strokeWidth="0.8" opacity={op} />
            <circle cx={x} cy={y} r="2.5" fill="var(--ivy-bgRaised)" stroke="var(--ivy-accent)" strokeWidth="1.2" />
          </g>
        ))}
        {([
          [79, 160, 0.7], [117, 175, 0.6], [155, 150, 0.8], [193, 170, 0.5],
          [231, 155, 0.75], [269, 180, 0.6], [307, 145, 0.85], [345, 165, 0.7],
        ] as [number, number, number][]).map(([x, y, op], i) => (
          <g key={i}>
            <line x1={x} y1="120" x2={x} y2={y} stroke="var(--ivy-inkMute)" strokeWidth="0.8" opacity={op} />
            <circle cx={x} cy={y} r="2" fill="var(--ivy-bgRaised)" stroke="var(--ivy-inkMute)" strokeWidth="1" />
          </g>
        ))}
        <text x="20" y="22" fontFamily="ui-monospace, monospace" fontSize="9"
          fill="var(--ivy-inkFaint)" letterSpacing="1">
          FIG. 01 — CHRONOLOGY OF EVENTS, MERGED ACROSS CHAPTERS
        </text>
      </svg>
    </figure>
  );
}

/* ── Library view ────────────────────────────────────────────── */
export default function LibraryView() {
  const navigate = useNavigate();
  const [drag, setDrag] = useState(false);
  const [hover, setHover] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const inflightRef = useRef(false);
  const inputRef = useRef<HTMLInputElement>(null);

  async function handleFile(file: File) {
    if (inflightRef.current) return;
    inflightRef.current = true;
    setIsUploading(true);
    try {
      const { objectKey } = await uploadPdfDirectToR2(file);
      const jobId = await createJob(file.name, objectKey);
      navigate(`/graph/${jobId}`);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Upload failed");
      inflightRef.current = false;
    } finally {
      setIsUploading(false);
    }
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setDrag(false);
    const file = e.dataTransfer.files[0];
    if (file) void handleFile(file);
  }

  function onInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) void handleFile(file);
  }

  // Recent jobs from localStorage
  const recentIds: string[] = JSON.parse(localStorage.getItem("ivy-recent-jobs") ?? "[]") as string[];

  return (
    <div className="px-10 py-10 max-w-[1100px] mx-auto">
      {/* Hero */}
      <div className="grid grid-cols-12 gap-8 items-end mb-12">
        <div className="col-span-7">
          <p className="font-mono text-[10px] uppercase tracking-[0.28em] mb-4 text-ivy-inkFaint">
            <span className="text-ivy-accent">—</span> manuscript intelligence, est. 2026
          </p>
          <h1 className="font-serif text-[64px] leading-[0.95] tracking-tight mb-6 text-ivy-inkDeep">
            Read between<br />
            <em className="not-italic text-ivy-accent">every</em> line.
          </h1>
          <p className="text-[15px] leading-relaxed max-w-[460px] text-ivy-inkMute">
            Upload a manuscript. Ivy reads each chapter, weaves the events into a single
            chronology, and surfaces contradictions a human editor would catch on their fourth pass.
          </p>
        </div>
        <div className="col-span-5">
          <FigureGraphic />
        </div>
      </div>

      {/* Upload */}
      <section
        className="grid grid-cols-12 gap-0 mb-12 rounded-sm"
        style={{
          border: `1px solid ${drag ? "var(--ivy-accent)" : "var(--ivy-rule)"}`,
          background: "var(--ivy-bgRaised)",
        }}
        onDragOver={(e) => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={onDrop}
      >
        <div className="col-span-7 px-8 py-7">
          <p className="font-mono text-[10px] uppercase tracking-[0.24em] mb-2 text-ivy-inkFaint">
            new analysis
          </p>
          <h2 className="font-serif text-[26px] tracking-tight mb-1 text-ivy-inkDeep">
            Drop a PDF here
          </h2>
          <p className="text-[13px] text-ivy-inkMute">
            Or browse a manuscript. We parse chapter by chapter — typically 2–3 minutes for a 300-page novel.
          </p>
        </div>
        <div
          className="col-span-5 flex items-center justify-end gap-3 px-8 py-7"
          style={{ borderLeft: "1px solid var(--ivy-ruleSoft)" }}
        >
          <button
            onClick={() => inputRef.current?.click()}
            disabled={isUploading}
            className="text-[13px] px-4 py-2 rounded-sm border border-ivy-rule text-ivy-inkMute disabled:opacity-50"
          >
            Browse files
          </button>
          <button
            onClick={() => inputRef.current?.click()}
            disabled={isUploading}
            className="flex items-center gap-2 text-[13px] px-4 py-2 rounded-sm font-medium disabled:opacity-50"
            style={{ background: "var(--ivy-inkDeep)", color: "var(--ivy-bgRaised)" }}
          >
            <IconUpload />
            {isUploading ? "Uploading…" : "Upload manuscript"}
          </button>
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf"
            className="sr-only"
            onChange={onInputChange}
          />
        </div>
      </section>

      {/* Recent jobs */}
      {recentIds.length > 0 && (
        <section>
          <div className="flex items-baseline justify-between mb-4">
            <h3 className="font-serif text-[20px] tracking-tight text-ivy-inkDeep">Recent analyses</h3>
            <span className="font-mono text-[11px] uppercase tracking-[0.2em] text-ivy-inkFaint">
              {recentIds.length} on file
            </span>
          </div>
          <div className="rounded-sm border border-ivy-rule bg-ivy-bgRaised">
            <div
              className="grid items-center gap-4 px-5 py-2.5 text-[10px] font-mono uppercase tracking-[0.18em] text-ivy-inkFaint border-b border-ivy-rule"
              style={{ gridTemplateColumns: "40px minmax(0,1fr) 120px 24px" }}
            >
              <span>#</span>
              <span>Job ID</span>
              <span>Status</span>
              <span />
            </div>
            {recentIds.map((id, i) => (
              <button
                key={id}
                onClick={() => navigate(`/results/${id}`)}
                onMouseEnter={() => setHover(id)}
                onMouseLeave={() => setHover(null)}
                className="grid items-center gap-4 w-full px-5 py-3.5 text-left"
                style={{
                  gridTemplateColumns: "40px minmax(0,1fr) 120px 24px",
                  borderBottom: i < recentIds.length - 1 ? "1px solid var(--ivy-ruleSoft)" : "none",
                  background: hover === id ? "var(--ivy-bgInk)" : "transparent",
                }}
              >
                <Mono className="text-[11px] text-ivy-inkFaint">{String(i + 1).padStart(2, "0")}</Mono>
                <span className="font-mono text-[13px] truncate text-ivy-inkDeep">{id}</span>
                <StatusPill status="complete" />
                <span style={{ color: hover === id ? "var(--ivy-accent)" : "var(--ivy-inkFaint)" }}>
                  <IconArrowRight />
                </span>
              </button>
            ))}
          </div>
        </section>
      )}

      {recentIds.length === 0 && (
        <div className="mt-4 text-center py-12 rounded-sm border border-ivy-ruleSoft">
          <p className="font-mono text-[11px] uppercase tracking-[0.2em] text-ivy-inkFaint">
            No manuscripts analysed yet
          </p>
        </div>
      )}
    </div>
  );
}
