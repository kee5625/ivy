/* Library view: clean home page with upload + recent manuscripts table */

function LibraryView({ onOpen }) {
  const [drag, setDrag] = React.useState(false);
  const [hover, setHover] = React.useState(null);
  const recents = window.IVY_DATA.RECENT_MANUSCRIPTS;

  return (
    <div className="px-10 py-10 max-w-[1100px] mx-auto">
      {/* Hero with editorial typography */}
      <div className="grid grid-cols-12 gap-8 items-end mb-12">
        <div className="col-span-7">
          <p className="font-mono text-[10px] uppercase tracking-[0.28em] mb-4" style={{ color: "var(--ivy-inkFaint)" }}>
            <span style={{ color: "var(--ivy-accent)" }}>—</span> manuscript intelligence, est. 2026
          </p>
          <h1 className="font-serif text-[64px] leading-[0.95] tracking-tight mb-6" style={{ color: "var(--ivy-inkDeep)" }}>
            Read between<br/>
            <em className="not-italic" style={{ color: "var(--ivy-accent)" }}>every</em> line.
          </h1>
          <p className="text-[15px] leading-relaxed max-w-[460px]" style={{ color: "var(--ivy-inkMute)" }}>
            Upload a manuscript. Ivy reads each chapter, weaves the events into a single chronology, and surfaces contradictions a human editor would catch on their fourth pass.
          </p>
        </div>
        {/* tasteful figure: a thin chronology graphic */}
        <div className="col-span-5">
          <FigureGraphic/>
        </div>
      </div>

      {/* Upload affordance — restrained, not a giant dashed box */}
      <section
        className="grid grid-cols-12 gap-0 mb-12 rounded-sm"
        style={{ border: `1px solid ${drag ? "var(--ivy-accent)" : "var(--ivy-rule)"}`, background: "var(--ivy-bgRaised)" }}
        onDragOver={e => { e.preventDefault(); setDrag(true); }}
        onDragLeave={() => setDrag(false)}
        onDrop={e => { e.preventDefault(); setDrag(false); onOpen(recents[0]); }}
      >
        <div className="col-span-7 px-8 py-7">
          <p className="font-mono text-[10px] uppercase tracking-[0.24em] mb-2" style={{ color: "var(--ivy-inkFaint)" }}>new analysis</p>
          <h2 className="font-serif text-[26px] tracking-tight mb-1" style={{ color: "var(--ivy-inkDeep)" }}>Drop a PDF here</h2>
          <p className="text-[13px]" style={{ color: "var(--ivy-inkMute)" }}>
            Or paste a manuscript. We parse chapter by chapter — typically 2–3 minutes for a 300-page novel.
          </p>
        </div>
        <div className="col-span-5 flex items-center justify-end gap-3 px-8 py-7" style={{ borderLeft: "1px solid var(--ivy-ruleSoft)" }}>
          <button
            onClick={() => onOpen(recents[0])}
            className="text-[13px] px-4 py-2 rounded-sm transition-colors"
            style={{ color: "var(--ivy-inkMute)", border: "1px solid var(--ivy-rule)" }}
          >
            Browse files
          </button>
          <button
            onClick={() => onOpen(recents[0])}
            className="flex items-center gap-2 text-[13px] px-4 py-2 rounded-sm font-medium"
            style={{ background: "var(--ivy-inkDeep)", color: "var(--ivy-bgRaised)" }}
          >
            <I.upload/> Upload manuscript
          </button>
        </div>
      </section>

      {/* Recent manuscripts — table style, restrained */}
      <section>
        <div className="flex items-baseline justify-between mb-4">
          <h3 className="font-serif text-[20px] tracking-tight" style={{ color: "var(--ivy-inkDeep)" }}>Recent manuscripts</h3>
          <span className="font-mono text-[11px] uppercase tracking-[0.2em]" style={{ color: "var(--ivy-inkFaint)" }}>
            {recents.length} on file
          </span>
        </div>

        <div style={{ border: "1px solid var(--ivy-rule)", background: "var(--ivy-bgRaised)" }} className="rounded-sm">
          {/* header row */}
          <div className="grid grid-cols-[40px_minmax(0,1fr)_140px_70px_70px_120px_120px] items-center gap-4 px-5 py-2.5 text-[10px] font-mono uppercase tracking-[0.18em]"
               style={{ color: "var(--ivy-inkFaint)", borderBottom: "1px solid var(--ivy-rule)" }}>
            <span>#</span>
            <span>Title / author</span>
            <span>Status</span>
            <span className="text-right">Pages</span>
            <span className="text-right">Issues</span>
            <span>Updated</span>
            <span></span>
          </div>
          {recents.map((m, i) => (
            <button
              key={m.id}
              onClick={() => onOpen(m)}
              onMouseEnter={() => setHover(m.id)}
              onMouseLeave={() => setHover(null)}
              className="grid grid-cols-[40px_minmax(0,1fr)_140px_70px_70px_120px_120px] items-center gap-4 w-full px-5 py-3.5 text-left transition-colors"
              style={{
                borderBottom: i < recents.length - 1 ? "1px solid var(--ivy-ruleSoft)" : "none",
                background: hover === m.id ? "var(--ivy-bgInk)" : "transparent",
              }}
            >
              <Mono className="text-[11px]" style={{ color: "var(--ivy-inkFaint)" }}>{String(i+1).padStart(2,"0")}</Mono>
              <div className="min-w-0">
                <p className="font-serif text-[15px] truncate" style={{ color: "var(--ivy-inkDeep)" }}>{m.title}</p>
                <p className="text-[12px]" style={{ color: "var(--ivy-inkMute)" }}>{m.author} · {m.chapters} chapters</p>
              </div>
              <StatusPill status={m.status}/>
              <Mono className="text-[12px] text-right" style={{ color: "var(--ivy-ink)" }}>{m.pages}</Mono>
              <span className="text-right">
                {m.issues > 0 ? (
                  <Mono className="text-[12px]" style={{ color: "var(--ivy-accent)" }}>{m.issues}</Mono>
                ) : (
                  <span className="text-[12px]" style={{ color: "var(--ivy-inkFaint)" }}>—</span>
                )}
              </span>
              <span className="text-[12px]" style={{ color: "var(--ivy-inkMute)" }}>{m.updated}</span>
              <span className="flex justify-end" style={{ color: hover === m.id ? "var(--ivy-accent)" : "var(--ivy-inkFaint)" }}>
                <I.arrowRight/>
              </span>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}

function StatusPill({ status }) {
  const map = {
    complete: { label: "Complete", c: "var(--ivy-inkDeep)", bg: "var(--ivy-bgInk)" },
    timeline_in_progress: { label: "Timeline · 2/3", c: "var(--ivy-accentInk)", bg: "var(--ivy-accentSoft)" },
    ingestion_in_progress: { label: "Ingesting · 1/3", c: "var(--ivy-accentInk)", bg: "var(--ivy-accentSoft)" },
    plot_hole_in_progress: { label: "Issues · 3/3", c: "var(--ivy-accentInk)", bg: "var(--ivy-accentSoft)" },
  };
  const s = map[status] || map.complete;
  return (
    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-sm text-[11px] font-medium" style={{ color: s.c, background: s.bg, border: "1px solid var(--ivy-ruleSoft)" }}>
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: status === "complete" ? "var(--ivy-inkMute)" : "var(--ivy-accent)" }}/>
      {s.label}
    </span>
  );
}

function FigureGraphic() {
  // Decorative editorial figure — subtle chronology rail with ribs
  return (
    <figure className="relative" style={{ height: 220 }}>
      <svg viewBox="0 0 420 220" className="w-full h-full">
        <defs>
          <pattern id="dots" width="6" height="6" patternUnits="userSpaceOnUse">
            <circle cx="0.5" cy="0.5" r="0.5" fill="var(--ivy-rule)"/>
          </pattern>
        </defs>
        <rect x="0" y="0" width="420" height="220" fill="url(#dots)" opacity="0.5"/>
        {/* spine */}
        <line x1="20" y1="120" x2="400" y2="120" stroke="var(--ivy-inkDeep)" strokeWidth="1.2"/>
        {/* ticks */}
        {Array.from({length: 11}, (_,i) => (
          <line key={i} x1={20 + i*38} y1="116" x2={20 + i*38} y2="124" stroke="var(--ivy-inkMute)" strokeWidth="1"/>
        ))}
        {/* ribs going up */}
        {[
          [60, 80, 0.9], [98, 60, 0.7], [136, 90, 0.5], [174, 50, 0.95],
          [212, 75, 0.6], [250, 95, 0.8], [288, 65, 0.55], [326, 85, 0.75], [364, 70, 0.65]
        ].map(([x, y, op], i) => (
          <g key={i}>
            <line x1={x} y1="120" x2={x} y2={y} stroke="var(--ivy-inkMute)" strokeWidth="0.8" opacity={op}/>
            <circle cx={x} cy={y} r="2.5" fill="var(--ivy-bgRaised)" stroke="var(--ivy-accent)" strokeWidth="1.2"/>
          </g>
        ))}
        {/* ribs going down */}
        {[
          [79, 160, 0.7], [117, 175, 0.6], [155, 150, 0.8], [193, 170, 0.5],
          [231, 155, 0.75], [269, 180, 0.6], [307, 145, 0.85], [345, 165, 0.7]
        ].map(([x, y, op], i) => (
          <g key={i}>
            <line x1={x} y1="120" x2={x} y2={y} stroke="var(--ivy-inkMute)" strokeWidth="0.8" opacity={op}/>
            <circle cx={x} cy={y} r="2" fill="var(--ivy-bgRaised)" stroke="var(--ivy-inkMute)" strokeWidth="1"/>
          </g>
        ))}
        {/* annotation */}
        <text x="20" y="22" fontFamily="ui-monospace, monospace" fontSize="9" fill="var(--ivy-inkFaint)" letterSpacing="1">
          FIG. 01 — CHRONOLOGY OF EVENTS, MERGED ACROSS CHAPTERS
        </text>
      </svg>
    </figure>
  );
}

Object.assign(window, { LibraryView });
