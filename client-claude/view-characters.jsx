/* Characters view: placeholder for future networkx graph + a static character ledger
   so the section reads as already-useful, not just empty space. */

function CharactersView() {
  const chars = window.IVY_DATA.CHARACTERS;
  const events = window.IVY_DATA.TIMELINE_EVENTS;
  const [activeName, setActiveName] = React.useState(chars[0].name);

  // Build co-occurrence edges from events
  const edges = [];
  events.forEach(e => {
    const ps = e.characters_present;
    for (let i = 0; i < ps.length; i++)
      for (let j = i+1; j < ps.length; j++)
        edges.push([ps[i], ps[j]]);
  });
  // Weighted edge map
  const weightMap = {};
  edges.forEach(([a, b]) => {
    const k = [a, b].sort().join("||");
    weightMap[k] = (weightMap[k] || 0) + 1;
  });

  return (
    <div className="px-10 py-8 max-w-[1300px] mx-auto">
      <ViewHeader
        kicker="Character network"
        title="Characters"
        subtitle="Co-occurrence graph derived from scene-level presence"
        stats={[
          { v: chars.length, l: "Named" },
          { v: Object.keys(weightMap).length, l: "Edges" },
          { v: chars.reduce((m, c) => Math.max(m, c.event_count), 0), l: "Top arc" },
          { v: "v0.1", l: "Status" },
        ]}
      />

      <div className="rounded-sm overflow-hidden mb-6 relative" style={{ border: "1px solid var(--ivy-rule)", background: "var(--ivy-bgRaised)" }}>
        <div className="px-5 py-3 flex items-center justify-between" style={{ borderBottom: "1px solid var(--ivy-ruleSoft)" }}>
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.22em]" style={{ color: "var(--ivy-inkFaint)" }}>fig. 03 · preview</p>
            <h3 className="font-serif text-[18px]" style={{ color: "var(--ivy-inkDeep)" }}>Network preview</h3>
          </div>
          <span className="font-mono text-[10px] uppercase tracking-[0.18em] px-2 py-1 rounded-sm" style={{ border: "1px solid var(--ivy-rule)", color: "var(--ivy-inkMute)" }}>
            networkx · planned for v1.0
          </span>
        </div>

        <CharacterNetwork chars={chars} weightMap={weightMap} activeName={activeName} setActiveName={setActiveName}/>
      </div>

      {/* Ledger */}
      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-7">
          <div className="rounded-sm" style={{ border: "1px solid var(--ivy-rule)", background: "var(--ivy-bgRaised)" }}>
            <div className="grid grid-cols-[minmax(0,1fr)_120px_70px_70px] items-center gap-3 px-5 py-2.5 text-[10px] font-mono uppercase tracking-[0.18em]"
                 style={{ color: "var(--ivy-inkFaint)", borderBottom: "1px solid var(--ivy-rule)" }}>
              <span>character</span><span>role</span><span className="text-right">events</span><span className="text-right">ch.</span>
            </div>
            {chars.map((c, i) => (
              <button
                key={c.name}
                onClick={() => setActiveName(c.name)}
                className="grid grid-cols-[minmax(0,1fr)_120px_70px_70px] items-center gap-3 w-full px-5 py-3 text-left transition-colors"
                style={{
                  borderBottom: i < chars.length - 1 ? "1px solid var(--ivy-ruleSoft)" : "none",
                  background: activeName === c.name ? "var(--ivy-bgInk)" : "transparent",
                }}
              >
                <span className="flex items-center gap-2.5">
                  <span className="h-2 w-2 rounded-full" style={{ background: activeName === c.name ? "var(--ivy-accent)" : "var(--ivy-inkMute)" }}/>
                  <span className="font-serif text-[15px]" style={{ color: "var(--ivy-inkDeep)" }}>{c.name}</span>
                </span>
                <span className="font-mono text-[11px] uppercase tracking-[0.16em]" style={{ color: "var(--ivy-inkMute)" }}>{c.role}</span>
                <Mono className="text-[12px] text-right" style={{ color: "var(--ivy-ink)" }}>{c.event_count}</Mono>
                <Mono className="text-[12px] text-right" style={{ color: "var(--ivy-ink)" }}>{c.chapters.length}</Mono>
              </button>
            ))}
          </div>
        </div>
        <div className="col-span-5">
          <CharacterDetail char={chars.find(c => c.name === activeName)} weightMap={weightMap}/>
        </div>
      </div>
    </div>
  );
}

function CharacterNetwork({ chars, weightMap, activeName, setActiveName }) {
  // Deterministic radial layout — characters around a soft circle, hub-weighted by event_count
  const W = 1100, H = 380;
  const cx = W/2, cy = H/2;
  const maxArc = Math.max(...chars.map(c => c.event_count));
  const positions = {};
  chars.forEach((c, i) => {
    const angle = (i / chars.length) * Math.PI * 2 - Math.PI/2;
    const r = 70 + (1 - c.event_count / maxArc) * 110;
    positions[c.name] = { x: cx + Math.cos(angle) * r, y: cy + Math.sin(angle) * r, c };
  });

  return (
    <div className="relative" style={{ background: "var(--ivy-bgInk)" }}>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ height: H, display: "block" }}>
        <defs>
          <pattern id="netdots" width="14" height="14" patternUnits="userSpaceOnUse">
            <circle cx="0.5" cy="0.5" r="0.5" fill="var(--ivy-rule)"/>
          </pattern>
        </defs>
        <rect x="0" y="0" width={W} height={H} fill="url(#netdots)" opacity="0.55"/>

        {/* edges */}
        {Object.entries(weightMap).map(([key, w]) => {
          const [a, b] = key.split("||");
          const pa = positions[a], pb = positions[b];
          if (!pa || !pb) return null;
          const isActive = activeName === a || activeName === b;
          return (
            <line
              key={key}
              x1={pa.x} y1={pa.y} x2={pb.x} y2={pb.y}
              stroke={isActive ? "var(--ivy-accent)" : "var(--ivy-inkMute)"}
              strokeWidth={Math.min(0.6 + w * 0.35, 2.4)}
              opacity={isActive ? 0.9 : 0.35}
            />
          );
        })}
        {/* nodes */}
        {chars.map(c => {
          const p = positions[c.name];
          const r = 6 + (c.event_count / maxArc) * 8;
          const active = activeName === c.name;
          return (
            <g key={c.name} onClick={() => setActiveName(c.name)} style={{ cursor: "pointer" }}>
              {active && <circle cx={p.x} cy={p.y} r={r + 6} fill="none" stroke="var(--ivy-accent)" strokeWidth="0.8" opacity="0.45"/>}
              <circle cx={p.x} cy={p.y} r={r} fill={active ? "var(--ivy-accent)" : "var(--ivy-bgRaised)"} stroke={active ? "var(--ivy-accent)" : "var(--ivy-inkDeep)"} strokeWidth="1.2"/>
              <text x={p.x} y={p.y + r + 14} textAnchor="middle" fontSize="11" fontFamily="ui-serif, Georgia" fill={active ? "var(--ivy-inkDeep)" : "var(--ivy-ink)"}>
                {c.name}
              </text>
              <text x={p.x} y={p.y + r + 26} textAnchor="middle" fontSize="9" fontFamily="ui-monospace, monospace" fill="var(--ivy-inkFaint)">
                {c.event_count} ev.
              </text>
            </g>
          );
        })}

        {/* annotation */}
        <text x="20" y="22" fontSize="9" fontFamily="ui-monospace, monospace" fill="var(--ivy-inkFaint)" letterSpacing="1.2">
          NODE SIZE ∝ EVENT PRESENCE  ·  EDGE WEIGHT ∝ CO-OCCURRENCE
        </text>
      </svg>
    </div>
  );
}

function CharacterDetail({ char, weightMap }) {
  if (!char) return null;
  // Top co-occurrences for this char
  const partners = Object.entries(weightMap)
    .filter(([k]) => k.includes(char.name))
    .map(([k, w]) => ({ name: k.split("||").find(n => n !== char.name), weight: w }))
    .sort((a, b) => b.weight - a.weight);

  return (
    <article className="rounded-sm" style={{ border: "1px solid var(--ivy-rule)", background: "var(--ivy-bgRaised)" }}>
      <div className="px-5 py-4" style={{ borderBottom: "1px solid var(--ivy-ruleSoft)" }}>
        <p className="font-mono text-[10px] uppercase tracking-[0.18em]" style={{ color: "var(--ivy-inkFaint)" }}>{char.role}</p>
        <h3 className="font-serif text-[24px] mt-1" style={{ color: "var(--ivy-inkDeep)" }}>{char.name}</h3>
        <p className="text-[12px] mt-1" style={{ color: "var(--ivy-inkMute)" }}>
          present in {char.event_count} events across {char.chapters.length} chapters
        </p>
      </div>
      <div className="px-5 py-4 space-y-4">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.22em] mb-2" style={{ color: "var(--ivy-inkFaint)" }}>chapter presence</p>
          <ChapterStrip chapters={char.chapters} total={10}/>
        </div>
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.22em] mb-2" style={{ color: "var(--ivy-inkFaint)" }}>strongest co-occurrences</p>
          <ul className="space-y-1.5">
            {partners.slice(0, 5).map(p => (
              <li key={p.name} className="grid grid-cols-[minmax(0,1fr)_60px_30px] items-center gap-2 text-[13px]">
                <span style={{ color: "var(--ivy-ink)" }}>{p.name}</span>
                <div className="h-1" style={{ background: "var(--ivy-rule)" }}>
                  <div style={{ width: `${(p.weight / partners[0].weight) * 100}%`, height: "100%", background: "var(--ivy-accent)" }}/>
                </div>
                <Mono className="text-[11px] text-right" style={{ color: "var(--ivy-inkMute)" }}>{p.weight}</Mono>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </article>
  );
}

function ChapterStrip({ chapters, total }) {
  return (
    <div className="flex gap-0.5">
      {Array.from({ length: total }).map((_, i) => {
        const present = chapters.includes(i+1);
        return (
          <div key={i} className="flex-1 flex flex-col items-center gap-1">
            <span className="block w-full" style={{ height: 18, background: present ? "var(--ivy-accent)" : "var(--ivy-rule)" }}/>
            <Mono className="text-[9px]" style={{ color: present ? "var(--ivy-ink)" : "var(--ivy-inkFaint)" }}>{i+1}</Mono>
          </div>
        );
      })}
    </div>
  );
}

Object.assign(window, { CharactersView });
