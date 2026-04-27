/* App shell: top bar + sidebar + view router */

const NAV = [
  { key: "library",     label: "Library",     icon: I.library },
  { key: "manuscript",  label: "Manuscript",  icon: I.manuscript },
  { key: "timeline",    label: "Timeline",    icon: I.timeline },
  { key: "issues",      label: "Issues",      icon: I.issues },
  { key: "characters",  label: "Characters",  icon: I.characters },
];

function TopBar({ palette, setPalette, manuscriptTitle }) {
  return (
    <header
      className="flex items-center justify-between px-6 h-14 border-b"
      style={{ borderColor: "var(--ivy-rule)", background: "var(--ivy-bgRaised)" }}
    >
      <div className="flex items-center gap-3">
        {/* logomark: a leaf-like ivy glyph kept abstract */}
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ color: "var(--ivy-accent)" }}>
          <path d="M5 19c8 0 14-6 14-14"/>
          <circle cx="5" cy="19" r="1.5" fill="currentColor"/>
          <circle cx="19" cy="5" r="1.5" fill="currentColor"/>
          <circle cx="12" cy="12" r="1.2" fill="currentColor"/>
        </svg>
        <span className="font-serif text-[18px] tracking-tight" style={{ color: "var(--ivy-inkDeep)" }}>Ivy</span>
        <span className="text-[11px] font-mono uppercase tracking-[0.18em]" style={{ color: "var(--ivy-inkFaint)" }}>
          manuscript intelligence
        </span>
      </div>

      <div className="flex items-center gap-3">
        <span className="text-[12px]" style={{ color: "var(--ivy-inkMute)" }}>
          {manuscriptTitle ? <>Working on <em className="not-italic" style={{ color: "var(--ivy-inkDeep)" }}>{manuscriptTitle}</em></> : "No manuscript open"}
        </span>
        <div className="flex items-center gap-1 px-2 py-1 rounded-sm" style={{ border: "1px solid var(--ivy-rule)" }}>
          {Object.keys(IVY_PALETTES).map(k => (
            <button
              key={k}
              onClick={() => setPalette(k)}
              title={IVY_PALETTES[k].label}
              className="h-4 w-4 rounded-full"
              style={{
                background: IVY_PALETTES[k].accent,
                outline: palette === k ? `2px solid var(--ivy-ink)` : "none",
                outlineOffset: 1,
              }}
            />
          ))}
        </div>
      </div>
    </header>
  );
}

function Sidebar({ view, setView, manuscript, jobStatus }) {
  return (
    <aside
      className="flex flex-col w-[224px] shrink-0 border-r"
      style={{ borderColor: "var(--ivy-rule)", background: "var(--ivy-bgRaised)" }}
    >
      <nav className="flex flex-col py-4 gap-0.5">
        {NAV.map(n => {
          const active = view === n.key;
          return (
            <button
              key={n.key}
              onClick={() => setView(n.key)}
              className="flex items-center gap-3 mx-3 px-3 py-2 rounded-sm text-[13px] text-left transition-colors"
              style={{
                background: active ? "var(--ivy-bgInk)" : "transparent",
                color: active ? "var(--ivy-inkDeep)" : "var(--ivy-inkMute)",
                fontWeight: active ? 600 : 500,
                position: "relative",
              }}
            >
              {active && <span className="absolute left-0 top-2 bottom-2 w-[2px] rounded-r" style={{ background: "var(--ivy-accent)" }}/>}
              <n.icon/>
              <span>{n.label}</span>
            </button>
          );
        })}
      </nav>

      <div className="mt-auto px-4 py-4 space-y-3">
        <Hairline/>
        <div>
          <p className="text-[10px] font-mono uppercase tracking-[0.2em] mb-2" style={{ color: "var(--ivy-inkFaint)" }}>
            current manuscript
          </p>
          {manuscript ? (
            <div>
              <p className="font-serif text-[14px] leading-tight" style={{ color: "var(--ivy-inkDeep)" }}>{manuscript.title}</p>
              <p className="text-[11px] mt-0.5" style={{ color: "var(--ivy-inkMute)" }}>{manuscript.author} · {manuscript.pages}pp</p>
            </div>
          ) : (
            <p className="text-[12px]" style={{ color: "var(--ivy-inkFaint)" }}>None open</p>
          )}
        </div>
        <PipelineStatus status={jobStatus}/>
      </div>
    </aside>
  );
}

function PipelineStatus({ status }) {
  const stages = [
    { key: "ingestion",  label: "Ingest"   },
    { key: "timeline",   label: "Timeline" },
    { key: "plot_hole",  label: "Issues"   },
  ];
  const idx = status === "complete" ? 3 : status === "plot_hole_in_progress" ? 2 : status === "timeline_in_progress" ? 1 : status === "ingestion_in_progress" ? 0 : -1;
  return (
    <div>
      <p className="text-[10px] font-mono uppercase tracking-[0.2em] mb-2" style={{ color: "var(--ivy-inkFaint)" }}>
        pipeline
      </p>
      <div className="flex flex-col gap-1.5">
        {stages.map((s, i) => {
          const done = i < idx, active = i === idx;
          return (
            <div key={s.key} className="flex items-center gap-2 text-[11px]">
              <span className="h-1.5 w-1.5 rounded-full" style={{
                background: done ? "var(--ivy-accent)" : active ? "var(--ivy-accent)" : "var(--ivy-rule)",
                boxShadow: active ? "0 0 0 3px color-mix(in oklch, var(--ivy-accent) 18%, transparent)" : "none"
              }}/>
              <span style={{ color: done || active ? "var(--ivy-inkDeep)" : "var(--ivy-inkFaint)" }}>{s.label}</span>
              {active && <span className="font-mono text-[10px] ml-auto" style={{ color: "var(--ivy-inkMute)" }}>running</span>}
              {done && <span className="font-mono text-[10px] ml-auto" style={{ color: "var(--ivy-inkFaint)" }}>done</span>}
            </div>
          );
        })}
      </div>
    </div>
  );
}

Object.assign(window, { TopBar, Sidebar, PipelineStatus, NAV });
