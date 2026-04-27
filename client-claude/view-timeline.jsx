/* Timeline view: horizontal fish-skeleton chronology.
   Spine runs left-right; ribs project up (above-the-line) and down (below-the-line)
   to event nodes. Hover scrubs a detail rail. Click pins selection. */

function TimelineView() {
  const events = window.IVY_DATA.TIMELINE_EVENTS.slice().sort((a,b)=>a.order-b.order);
  const [hoverId, setHoverId] = React.useState(null);
  const [pinId, setPinId] = React.useState("E001");
  const activeId = hoverId || pinId;
  const active = events.find(e => e.event_id === activeId);

  const containerRef = React.useRef(null);
  const [w, setW] = React.useState(900);
  React.useEffect(() => {
    const update = () => { if (containerRef.current) setW(containerRef.current.clientWidth); };
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  // Layout: pad left + right
  const padX = 60, padY = 100;
  const minWidth = events.length * 70;
  const innerW = Math.max(w - padX*2, minWidth);
  const totalW = innerW + padX*2;
  const spineY = padY + 110;
  const xFor = (i) => padX + (i / (events.length - 1)) * innerW;

  // Alternate up/down ribs; rib length scales with number of cause/caused_by edges
  const layout = events.map((e, i) => {
    const above = i % 2 === 0;
    const linkCount = e.causes.length + e.caused_by.length;
    const ribLen = 30 + linkCount * 16 + (e.confidence ? (1 - (e.confidence ?? 0.5)) * 20 : 10);
    const x = xFor(i);
    const y = above ? spineY - ribLen : spineY + ribLen;
    return { ...e, x, y, above, ribLen };
  });

  // Causality chords (subtle)
  const idToPt = Object.fromEntries(layout.map(p => [p.event_id, p]));

  // Year ticks: derive from inferred_year where present
  const years = Array.from(new Set(events.map(e => e.inferred_year).filter(Boolean))).sort();

  // Chapter bands: contiguous spans on the spine grouped by chapter_num
  const chapterBands = [];
  layout.forEach((p, i) => {
    const last = chapterBands[chapterBands.length - 1];
    if (last && last.chapter_num === p.chapter_num) {
      last.endX = p.x; last.count += 1;
    } else {
      chapterBands.push({ chapter_num: p.chapter_num, chapter_title: p.chapter_title, startX: p.x, endX: p.x, count: 1 });
    }
  });

  return (
    <div className="px-10 py-8 max-w-[1400px] mx-auto">
      <ViewHeader
        kicker="Story chronology"
        title="Timeline"
        subtitle="Merged from 10 chapters into 19 globally ordered events"
        stats={[
          { v: events.length, l: "Events" },
          { v: events.filter(e => e.causes.length || e.caused_by.length).length, l: "Linked" },
          { v: events.filter(e => e.time_reference || e.inferred_date).length, l: "Time-anchored" },
          { v: years.length, l: "Year markers" },
        ]}
      />

      {/* Skeleton */}
      <div ref={containerRef} className="rounded-sm overflow-x-auto" style={{ border: "1px solid var(--ivy-rule)", background: "var(--ivy-bgRaised)" }}>
        <div style={{ width: totalW, position: "relative" }}>
          <svg width={totalW} height={spineY * 2} style={{ display: "block" }}>
            {/* dotted year band */}
            <line x1={padX} y1={spineY-150} x2={totalW-padX} y2={spineY-150} stroke="var(--ivy-ruleSoft)" strokeWidth="1" strokeDasharray="2 4"/>
            <line x1={padX} y1={spineY+150} x2={totalW-padX} y2={spineY+150} stroke="var(--ivy-ruleSoft)" strokeWidth="1" strokeDasharray="2 4"/>

            {/* major ticks */}
            {layout.map((p, i) => (
              <g key={`tick-${i}`}>
                <line x1={p.x} y1={spineY - 6} x2={p.x} y2={spineY + 6} stroke="var(--ivy-inkMute)" strokeWidth="0.8"/>
                <text x={p.x} y={spineY + 22} fontSize="9" fontFamily="ui-monospace, monospace" textAnchor="middle" fill="var(--ivy-inkFaint)">
                  #{String(i+1).padStart(2,"0")}
                </text>
              </g>
            ))}

            {/* chapter band — sits just above the spine */}
            {chapterBands.map((b, i) => {
              const x1 = b.startX - 12, x2 = b.endX + 12;
              const isActive = active && b.chapter_num === active.chapter_num;
              return (
                <g key={`band-${i}-${b.chapter_num}`}>
                  <rect x={x1} y={spineY - 50} width={x2 - x1} height={14}
                    fill={isActive ? "var(--ivy-accentSoft)" : (i % 2 === 0 ? "var(--ivy-bgInk)" : "var(--ivy-panel)")}
                    stroke={isActive ? "var(--ivy-accent)" : "var(--ivy-ruleSoft)"} strokeWidth="0.6"/>
                  <text x={(x1 + x2) / 2} y={spineY - 40} textAnchor="middle"
                    fontSize="9" fontFamily="ui-monospace, monospace"
                    fill={isActive ? "var(--ivy-accentInk)" : "var(--ivy-inkMute)"}
                    letterSpacing="0.5">
                    CH.{String(b.chapter_num).padStart(2,"0")}
                  </text>
                  <line x1={(x1+x2)/2} y1={spineY - 36} x2={(x1+x2)/2} y2={spineY - 8}
                    stroke="var(--ivy-ruleSoft)" strokeWidth="0.6" strokeDasharray="1 2"/>
                </g>
              );
            })}

            {/* spine */}
            <line x1={padX} y1={spineY} x2={totalW - padX} y2={spineY} stroke="var(--ivy-inkDeep)" strokeWidth="1.4"/>
            {/* arrowheads */}
            <polygon points={`${padX-2},${spineY} ${padX+6},${spineY-3} ${padX+6},${spineY+3}`} fill="var(--ivy-inkDeep)"/>
            <polygon points={`${totalW-padX+2},${spineY} ${totalW-padX-6},${spineY-3} ${totalW-padX-6},${spineY+3}`} fill="var(--ivy-inkDeep)"/>

            {/* causality chords (curve through spine) */}
            {layout.map(p =>
              p.causes.map(cid => {
                const target = idToPt[cid];
                if (!target) return null;
                const x1 = p.x, x2 = target.x;
                const mx = (x1 + x2) / 2;
                const dim = activeId && (activeId === p.event_id || activeId === cid);
                return (
                  <path
                    key={`${p.event_id}->${cid}`}
                    d={`M ${x1} ${spineY} Q ${mx} ${spineY + (x2 > x1 ? 36 : -36)} ${x2} ${spineY}`}
                    fill="none"
                    stroke={dim ? "var(--ivy-accent)" : "var(--ivy-rule)"}
                    strokeWidth={dim ? 1.2 : 0.8}
                    opacity={dim ? 0.95 : 0.55}
                  />
                );
              })
            )}

            {/* ribs */}
            {layout.map(p => {
              const isActive = p.event_id === activeId;
              const isPinned = p.event_id === pinId;
              return (
                <g key={p.event_id}>
                  <line
                    x1={p.x} y1={spineY} x2={p.x} y2={p.y}
                    stroke={isActive ? "var(--ivy-accent)" : "var(--ivy-inkMute)"}
                    strokeWidth={isActive ? 1.4 : 0.9}
                  />
                  {/* node */}
                  <circle
                    cx={p.x} cy={p.y}
                    r={isActive ? 6 : 4}
                    fill={isActive ? "var(--ivy-accent)" : "var(--ivy-bgRaised)"}
                    stroke={isActive ? "var(--ivy-accent)" : "var(--ivy-inkDeep)"}
                    strokeWidth="1.2"
                  />
                  {/* halo for pin */}
                  {isPinned && !hoverId && (
                    <circle cx={p.x} cy={p.y} r="10" fill="none" stroke="var(--ivy-accent)" strokeWidth="0.8" opacity="0.5"/>
                  )}
                  {/* event id label */}
                  <text
                    x={p.x}
                    y={p.above ? p.y - 12 : p.y + 16}
                    fontSize="9"
                    fontFamily="ui-monospace, monospace"
                    textAnchor="middle"
                    fill={isActive ? "var(--ivy-accent)" : "var(--ivy-inkMute)"}
                    style={{ letterSpacing: "0.5px" }}
                  >
                    {p.event_id}
                  </text>
                  {/* year tick (only if present, drawn farther out) */}
                  {p.inferred_year && (
                    <text
                      x={p.x}
                      y={p.above ? p.y - 26 : p.y + 30}
                      fontSize="9"
                      fontFamily="ui-monospace, monospace"
                      textAnchor="middle"
                      fill="var(--ivy-inkFaint)"
                    >
                      {p.inferred_year}
                    </text>
                  )}
                  {/* hit area */}
                  <circle
                    cx={p.x} cy={p.y} r="14" fill="transparent"
                    onMouseEnter={() => setHoverId(p.event_id)}
                    onMouseLeave={() => setHoverId(null)}
                    onClick={() => setPinId(p.event_id)}
                    style={{ cursor: "pointer" }}
                  />
                </g>
              );
            })}

            {/* spine annotation */}
            <text x={padX} y={spineY - 178} fontSize="9" fontFamily="ui-monospace, monospace" fill="var(--ivy-inkFaint)" letterSpacing="1">
              ABOVE THE LINE — EARLIER STORY ORDER WITHIN PAIR
            </text>
            <text x={padX} y={spineY + 188} fontSize="9" fontFamily="ui-monospace, monospace" fill="var(--ivy-inkFaint)" letterSpacing="1">
              BELOW THE LINE — LATER STORY ORDER WITHIN PAIR
            </text>
          </svg>
        </div>
      </div>

      {/* Detail rail + legend */}
      <div className="grid grid-cols-12 gap-6 mt-6">
        <div className="col-span-8">
          {active && <EventDetail event={active} pinned={active.event_id === pinId} onPin={() => setPinId(active.event_id)}/>}
        </div>
        <div className="col-span-4">
          <TimelineLegend/>
          <div className="mt-4">
            <p className="font-mono text-[10px] uppercase tracking-[0.22em] mb-3" style={{ color: "var(--ivy-inkFaint)" }}>navigate</p>
            <div className="flex flex-wrap gap-1">
              {events.map(e => (
                <button
                  key={e.event_id}
                  onMouseEnter={() => setHoverId(e.event_id)}
                  onMouseLeave={() => setHoverId(null)}
                  onClick={() => setPinId(e.event_id)}
                  className="font-mono text-[10px] px-1.5 py-0.5 rounded-sm"
                  style={{
                    border: "1px solid var(--ivy-rule)",
                    color: e.event_id === activeId ? "var(--ivy-bgRaised)" : "var(--ivy-inkMute)",
                    background: e.event_id === activeId ? "var(--ivy-accent)" : "transparent",
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

function EventDetail({ event, pinned, onPin }) {
  return (
    <article className="rounded-sm" style={{ border: "1px solid var(--ivy-rule)", background: "var(--ivy-bgRaised)" }}>
      <div className="px-5 py-4 flex items-start justify-between gap-4" style={{ borderBottom: "1px solid var(--ivy-ruleSoft)" }}>
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-2">
            <Mono className="text-[11px] px-1.5 py-0.5 rounded-sm" style={{ background: "var(--ivy-accentSoft)", color: "var(--ivy-accentInk)" }}>{event.event_id}</Mono>
            <span className="font-mono text-[10px] uppercase tracking-[0.18em]" style={{ color: "var(--ivy-inkFaint)" }}>
              order #{String(event.order).padStart(2,"0")} · ch. {event.chapter_num}
            </span>
            {!pinned && <span className="font-mono text-[10px] uppercase tracking-[0.18em]" style={{ color: "var(--ivy-inkFaint)" }}>· hover</span>}
          </div>
          <h3 className="font-serif text-[20px] leading-snug" style={{ color: "var(--ivy-inkDeep)" }}>{event.description}</h3>
          <p className="text-[12px] mt-1" style={{ color: "var(--ivy-inkMute)" }}>From "{event.chapter_title}"</p>
        </div>
        <div className="flex flex-col items-end gap-1.5 shrink-0">
          <ConfidenceMeter value={event.confidence}/>
          <span className="font-mono text-[10px] uppercase tracking-[0.18em]" style={{ color: "var(--ivy-inkFaint)" }}>confidence</span>
        </div>
      </div>

      <div className="grid grid-cols-3 px-5 py-4 gap-6">
        <DetailField label="When">
          {event.time_reference || event.inferred_date || event.relative_time_anchor || "—"}
          {event.inferred_year && <Mono className="ml-2 text-[11px]" style={{ color: "var(--ivy-inkFaint)" }}>({event.inferred_year})</Mono>}
        </DetailField>
        <DetailField label="Where">
          {event.location || "—"}
        </DetailField>
        <DetailField label="Who">
          <div className="flex flex-wrap gap-1 mt-0.5">
            {event.characters_present.map(c => (
              <span key={c} className="text-[12px] px-1.5 py-0.5 rounded-sm" style={{ border: "1px solid var(--ivy-rule)" }}>{c}</span>
            ))}
          </div>
        </DetailField>
      </div>

      <div className="grid grid-cols-2 px-5 pb-5 gap-6">
        <DetailField label={`Caused by (${event.caused_by.length})`}>
          {event.caused_by.length === 0 ? <span style={{ color: "var(--ivy-inkFaint)" }}>nothing in scope</span> :
            <div className="flex flex-wrap gap-1 mt-0.5">{event.caused_by.map(id => (
              <Mono key={id} className="text-[11px] px-1.5 py-0.5 rounded-sm" style={{ border: "1px solid var(--ivy-rule)", color: "var(--ivy-ink)" }}>{id}</Mono>
            ))}</div>
          }
        </DetailField>
        <DetailField label={`Causes (${event.causes.length})`}>
          {event.causes.length === 0 ? <span style={{ color: "var(--ivy-inkFaint)" }}>nothing in scope</span> :
            <div className="flex flex-wrap gap-1 mt-0.5">{event.causes.map(id => (
              <Mono key={id} className="text-[11px] px-1.5 py-0.5 rounded-sm" style={{ background: "var(--ivy-accentSoft)", color: "var(--ivy-accentInk)" }}>{id}</Mono>
            ))}</div>
          }
        </DetailField>
      </div>
    </article>
  );
}

function DetailField({ label, children }) {
  return (
    <div>
      <p className="font-mono text-[10px] uppercase tracking-[0.22em] mb-1.5" style={{ color: "var(--ivy-inkFaint)" }}>{label}</p>
      <div className="text-[13px]" style={{ color: "var(--ivy-ink)" }}>{children}</div>
    </div>
  );
}

function ConfidenceMeter({ value }) {
  const v = value ?? 0;
  return (
    <div className="flex items-center gap-2">
      <Mono className="text-[13px]" style={{ color: "var(--ivy-inkDeep)" }}>{Math.round(v * 100)}%</Mono>
      <div style={{ width: 60, height: 6, background: "var(--ivy-rule)" }}>
        <div style={{ width: `${v*100}%`, height: "100%", background: "var(--ivy-accent)" }}/>
      </div>
    </div>
  );
}

function TimelineLegend() {
  return (
    <div className="rounded-sm p-4" style={{ border: "1px solid var(--ivy-rule)", background: "var(--ivy-bgRaised)" }}>
      <p className="font-mono text-[10px] uppercase tracking-[0.22em] mb-3" style={{ color: "var(--ivy-inkFaint)" }}>legend</p>
      <ul className="space-y-2 text-[12px]" style={{ color: "var(--ivy-ink)" }}>
        <li className="flex items-center gap-2.5">
          <svg width="20" height="14"><line x1="0" y1="7" x2="20" y2="7" stroke="var(--ivy-inkDeep)" strokeWidth="1.4"/></svg>
          <span>Spine — story order, left → right</span>
        </li>
        <li className="flex items-center gap-2.5">
          <svg width="20" height="14"><line x1="10" y1="0" x2="10" y2="14" stroke="var(--ivy-inkMute)" strokeWidth="1"/><circle cx="10" cy="0" r="3" fill="var(--ivy-bgRaised)" stroke="var(--ivy-inkDeep)"/></svg>
          <span>Rib length ∝ link density × uncertainty</span>
        </li>
        <li className="flex items-center gap-2.5">
          <svg width="20" height="14"><path d="M2 7 Q10 14 18 7" fill="none" stroke="var(--ivy-rule)" strokeWidth="0.8"/></svg>
          <span>Curve — causality chord</span>
        </li>
        <li className="flex items-center gap-2.5">
          <span className="inline-block h-2 w-2 rounded-full" style={{ background: "var(--ivy-accent)" }}/>
          <span>Active / pinned event</span>
        </li>
      </ul>
    </div>
  );
}

Object.assign(window, { TimelineView });
