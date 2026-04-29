/* Manuscript view: chapter rows with spine indicator (length + density),
   sparkline of key events, expandable detail. */

function ManuscriptView() {
  const chapters = window.IVY_DATA.CHAPTERS;
  const events = window.IVY_DATA.TIMELINE_EVENTS;
  const [openIdx, setOpenIdx] = React.useState(0);

  // Per-chapter event count (for spine indicator scale)
  const counts = chapters.map(c => events.filter(e => e.chapter_num === c.chapter_num).length);
  const maxCount = Math.max(...counts, 1);
  const totalEvents = events.length;
  const totalChars = new Set(chapters.flatMap(c => c.characters)).size;

  return (
    <div className="px-10 py-8 max-w-[1100px] mx-auto">
      <ViewHeader
        title="The Saltcombe Letter"
        subtitle="K. Vinter · 312 pages · 10 chapters"
        stats={[
          { v: chapters.length, l: "Chapters" },
          { v: totalEvents,     l: "Events" },
          { v: totalChars,      l: "Named characters" },
          { v: 7,               l: "Issues flagged" },
        ]}
      />

      <div style={{ border: "1px solid var(--ivy-rule)", background: "var(--ivy-bgRaised)" }} className="rounded-sm">
        {/* table header */}
        <div className="grid grid-cols-[44px_36px_minmax(0,1fr)_140px_60px_60px_24px] items-center gap-4 px-5 py-2.5 text-[10px] font-mono uppercase tracking-[0.18em]"
             style={{ color: "var(--ivy-inkFaint)", borderBottom: "1px solid var(--ivy-rule)" }}>
          <span>Ch.</span>
          <span></span>
          <span>Title</span>
          <span>Event density</span>
          <span className="text-right">Events</span>
          <span className="text-right">Char.</span>
          <span></span>
        </div>

        {chapters.map((c, i) => {
          const ce = events.filter(e => e.chapter_num === c.chapter_num).sort((a,b)=>a.order-b.order);
          const open = openIdx === i;
          return (
            <div key={c.chapter_num} style={{ borderBottom: i < chapters.length - 1 ? "1px solid var(--ivy-ruleSoft)" : "none" }}>
              <button
                onClick={() => setOpenIdx(open ? -1 : i)}
                className="grid grid-cols-[44px_36px_minmax(0,1fr)_140px_60px_60px_24px] items-center gap-4 w-full px-5 py-3.5 text-left transition-colors"
                style={{ background: open ? "var(--ivy-bgInk)" : "transparent" }}
              >
                <Mono className="text-[12px]" style={{ color: "var(--ivy-inkMute)" }}>
                  {String(c.chapter_num).padStart(2, "0")}
                </Mono>
                {/* Spine indicator: vertical bar w/ density */}
                <SpineIndicator count={ce.length} max={maxCount}/>
                <div className="min-w-0">
                  <p className="font-serif text-[15px] truncate" style={{ color: "var(--ivy-inkDeep)" }}>{c.chapter_title}</p>
                  <p className="text-[12px] truncate" style={{ color: "var(--ivy-inkMute)" }}>{c.summary[0]}</p>
                </div>
                <DensityBars count={ce.length} max={maxCount}/>
                <Mono className="text-[12px] text-right" style={{ color: "var(--ivy-ink)" }}>{ce.length}</Mono>
                <Mono className="text-[12px] text-right" style={{ color: "var(--ivy-ink)" }}>{c.characters.length}</Mono>
                <span style={{ color: "var(--ivy-inkFaint)", transform: open ? "rotate(90deg)" : "none", transition: "transform 0.2s" }}>
                  <I.arrowRight/>
                </span>
              </button>

              {open && (
                <div className="grid grid-cols-12 gap-8 px-5 pt-1 pb-6" style={{ background: "var(--ivy-bgInk)" }}>
                  <div className="col-span-7">
                    <p className="font-mono text-[10px] uppercase tracking-[0.22em] mb-2" style={{ color: "var(--ivy-inkFaint)" }}>summary</p>
                    <ul className="space-y-2 mb-5">
                      {c.summary.map((s, k) => (
                        <li key={k} className="flex gap-3 text-[14px] leading-relaxed" style={{ color: "var(--ivy-ink)" }}>
                          <Mono style={{ color: "var(--ivy-inkFaint)" }}>{String(k+1).padStart(2,"0")}</Mono>
                          <span>{s}</span>
                        </li>
                      ))}
                    </ul>
                    <p className="font-mono text-[10px] uppercase tracking-[0.22em] mb-2" style={{ color: "var(--ivy-inkFaint)" }}>key events</p>
                    <ol className="space-y-1.5">
                      {c.key_events.map((e, k) => (
                        <li key={k} className="flex items-baseline gap-3 text-[13px]" style={{ color: "var(--ivy-ink)" }}>
                          <Mono style={{ color: "var(--ivy-accent)" }}>{ce[k]?.event_id || "—"}</Mono>
                          <span>{e}</span>
                        </li>
                      ))}
                    </ol>
                  </div>
                  <div className="col-span-5 space-y-4">
                    <div>
                      <p className="font-mono text-[10px] uppercase tracking-[0.22em] mb-2" style={{ color: "var(--ivy-inkFaint)" }}>characters</p>
                      <div className="flex flex-wrap gap-1.5">
                        {c.characters.map(name => (
                          <span key={name} className="text-[12px] px-2 py-0.5 rounded-sm" style={{ border: "1px solid var(--ivy-rule)", color: "var(--ivy-ink)" }}>
                            {name}
                          </span>
                        ))}
                      </div>
                    </div>
                    <div>
                      <p className="font-mono text-[10px] uppercase tracking-[0.22em] mb-2" style={{ color: "var(--ivy-inkFaint)" }}>chronology contribution</p>
                      <ChapterRibbon events={ce} totalEvents={totalEvents}/>
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

function SpineIndicator({ count, max }) {
  // tall bar with subdivisions = events
  return (
    <div className="flex items-center justify-center" style={{ width: 24, height: 36 }}>
      <div className="relative" style={{ width: 4, height: 36, background: "var(--ivy-rule)" }}>
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="absolute left-0 right-0" style={{
            top: `${(i / Math.max(count, 1)) * 100}%`,
            height: `${Math.max(2, 100 / Math.max(count, 1) - 8)}%`,
            background: "var(--ivy-accent)"
          }}/>
        ))}
      </div>
    </div>
  );
}

function DensityBars({ count, max }) {
  // horizontal bar viz
  return (
    <div className="flex items-center gap-0.5" style={{ height: 12 }}>
      {Array.from({ length: max }).map((_, i) => (
        <span key={i} style={{
          width: 6, height: i < count ? 10 : 4,
          background: i < count ? "var(--ivy-ink)" : "var(--ivy-rule)",
        }}/>
      ))}
    </div>
  );
}

function ChapterRibbon({ events, totalEvents }) {
  // Show where this chapter's events land in the global order
  return (
    <div className="relative" style={{ height: 28 }}>
      <div className="absolute left-0 right-0 top-1/2 h-px" style={{ background: "var(--ivy-rule)" }}/>
      {events.map(e => (
        <div key={e.event_id}
          className="absolute -translate-x-1/2"
          style={{
            left: `${(e.order / totalEvents) * 100}%`,
            top: "50%", transform: "translate(-50%, -50%)",
          }}
          title={e.description}
        >
          <span className="block h-2 w-2 rounded-full" style={{ background: "var(--ivy-accent)", outline: "2px solid var(--ivy-bgInk)" }}/>
        </div>
      ))}
      <div className="absolute -bottom-1 left-0 font-mono text-[9px]" style={{ color: "var(--ivy-inkFaint)" }}>order #1</div>
      <div className="absolute -bottom-1 right-0 font-mono text-[9px]" style={{ color: "var(--ivy-inkFaint)" }}>#{totalEvents}</div>
    </div>
  );
}

function ViewHeader({ title, subtitle, stats }) {
  return (
    <div className="mb-8">
      <div className="flex items-end justify-between mb-6">
        <div>
          <h1 className="font-serif text-[40px] leading-none tracking-tight" style={{ color: "var(--ivy-inkDeep)" }}>
            {title}
          </h1>
          {subtitle && <p className="text-[13px] mt-2" style={{ color: "var(--ivy-inkMute)" }}>{subtitle}</p>}
        </div>
      </div>
      {stats && (
        <div className="grid grid-cols-4" style={{ borderTop: "1px solid var(--ivy-rule)", borderBottom: "1px solid var(--ivy-rule)" }}>
          {stats.map((s, i) => (
            <div key={i} className="px-4 py-3" style={{ borderRight: i < stats.length - 1 ? "1px solid var(--ivy-ruleSoft)" : "none" }}>
              <p className="font-serif text-[26px] leading-none" style={{ color: "var(--ivy-inkDeep)" }}>{s.v}</p>
              <p className="font-mono text-[10px] uppercase tracking-[0.18em] mt-1.5" style={{ color: "var(--ivy-inkFaint)" }}>{s.l}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

Object.assign(window, { ManuscriptView, ViewHeader });
