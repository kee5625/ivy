import { useMemo, useState } from "react";
import { Mono, ViewHeader } from "@/components/atoms";
import type { Character, TimelineEvent } from "@/types/graph";

/* ── Chapter strip ───────────────────────────────────────────── */
function ChapterStrip({ chapters, total }: { chapters: number[]; total: number }) {
  return (
    <div className="flex gap-0.5">
      {Array.from({ length: total }).map((_, i) => {
        const present = chapters.includes(i + 1);
        return (
          <div key={i} className="flex-1 flex flex-col items-center gap-1">
            <span
              className="block w-full"
              style={{ height: 18, background: present ? "var(--ivy-accent)" : "var(--ivy-rule)" }}
            />
            <Mono
              className="text-[9px]"
              style={{ color: present ? "var(--ivy-ink)" : "var(--ivy-inkFaint)" }}
            >
              {i + 1}
            </Mono>
          </div>
        );
      })}
    </div>
  );
}

/* ── Character detail ────────────────────────────────────────── */
function CharacterDetail({
  char,
  weightMap,
}: {
  char: Character;
  weightMap: Record<string, number>;
}) {
  const partners = Object.entries(weightMap)
    .filter(([k]) => k.includes(char.name))
    .map(([k, w]) => ({ name: k.split("||").find((n) => n !== char.name) ?? "", weight: w }))
    .sort((a, b) => b.weight - a.weight);

  const maxW = partners[0]?.weight ?? 1;

  return (
    <article className="rounded-sm border border-ivy-rule bg-ivy-bgRaised">
      <div className="px-5 py-4 border-b border-ivy-ruleSoft">
        <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-ivy-inkFaint">character</p>
        <h3 className="font-serif text-[24px] mt-1 text-ivy-inkDeep">{char.name}</h3>
        <p className="text-[12px] mt-1 text-ivy-inkMute">
          present in {char.event_count} events across {char.chapters.length} chapters
        </p>
      </div>
      <div className="px-5 py-4 space-y-4">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.22em] mb-2 text-ivy-inkFaint">
            chapter presence
          </p>
          <ChapterStrip chapters={char.chapters} total={Math.max(...char.chapters, 10)} />
        </div>
        <div>
          <p className="font-mono text-[10px] uppercase tracking-[0.22em] mb-2 text-ivy-inkFaint">
            strongest co-occurrences
          </p>
          <ul className="space-y-1.5">
            {partners.slice(0, 5).map((p) => (
              <li
                key={p.name}
                className="grid items-center gap-2 text-[13px]"
                style={{ gridTemplateColumns: "minmax(0,1fr) 60px 30px" }}
              >
                <span className="text-ivy-ink">{p.name}</span>
                <div className="h-1 bg-ivy-rule">
                  <div
                    className="h-full bg-ivy-accent"
                    style={{ width: `${(p.weight / maxW) * 100}%` }}
                  />
                </div>
                <Mono className="text-[11px] text-right text-ivy-inkMute">{p.weight}</Mono>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </article>
  );
}

/* ── Character network (radial) ──────────────────────────────── */
function CharacterNetwork({
  chars,
  weightMap,
  activeName,
  setActiveName,
}: {
  chars: Character[];
  weightMap: Record<string, number>;
  activeName: string;
  setActiveName: (n: string) => void;
}) {
  const W = 1100, H = 380;
  const cx = W / 2, cy = H / 2;
  const maxArc = Math.max(...chars.map((c) => c.event_count), 1);

  const positions: Record<string, { x: number; y: number }> = {};
  chars.forEach((c, i) => {
    const angle = (i / chars.length) * Math.PI * 2 - Math.PI / 2;
    const r = 70 + (1 - c.event_count / maxArc) * 110;
    positions[c.name] = { x: cx + Math.cos(angle) * r, y: cy + Math.sin(angle) * r };
  });

  return (
    <div className="relative bg-ivy-bgInk">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ height: H, display: "block" }}>
        <defs>
          <pattern id="netdots" width="14" height="14" patternUnits="userSpaceOnUse">
            <circle cx="0.5" cy="0.5" r="0.5" fill="var(--ivy-rule)" />
          </pattern>
        </defs>
        <rect x="0" y="0" width={W} height={H} fill="url(#netdots)" opacity="0.55" />

        {/* edges */}
        {Object.entries(weightMap).map(([key, w]) => {
          const [a, b] = key.split("||");
          const pa = positions[a], pb = positions[b];
          if (!pa || !pb) return null;
          const isActive = activeName === a || activeName === b;
          return (
            <line key={key} x1={pa.x} y1={pa.y} x2={pb.x} y2={pb.y}
              stroke={isActive ? "var(--ivy-accent)" : "var(--ivy-inkMute)"}
              strokeWidth={Math.min(0.6 + w * 0.35, 2.4)}
              opacity={isActive ? 0.9 : 0.35} />
          );
        })}

        {/* nodes */}
        {chars.map((c) => {
          const p = positions[c.name];
          if (!p) return null;
          const r = 6 + (c.event_count / maxArc) * 8;
          const active = activeName === c.name;
          return (
            <g key={c.name} onClick={() => setActiveName(c.name)} style={{ cursor: "pointer" }}>
              {active && (
                <circle cx={p.x} cy={p.y} r={r + 6} fill="none"
                  stroke="var(--ivy-accent)" strokeWidth="0.8" opacity="0.45" />
              )}
              <circle cx={p.x} cy={p.y} r={r}
                fill={active ? "var(--ivy-accent)" : "var(--ivy-bgRaised)"}
                stroke={active ? "var(--ivy-accent)" : "var(--ivy-inkDeep)"}
                strokeWidth="1.2" />
              <text x={p.x} y={p.y + r + 14} textAnchor="middle"
                fontSize="11" fontFamily="ui-serif,Georgia"
                fill={active ? "var(--ivy-inkDeep)" : "var(--ivy-ink)"}>
                {c.name}
              </text>
              <text x={p.x} y={p.y + r + 26} textAnchor="middle"
                fontSize="9" fontFamily="ui-monospace,monospace" fill="var(--ivy-inkFaint)">
                {c.event_count} ev.
              </text>
            </g>
          );
        })}

        <text x="20" y="22" fontSize="9" fontFamily="ui-monospace,monospace"
          fill="var(--ivy-inkFaint)" letterSpacing="1.2">
          NODE SIZE ∝ EVENT PRESENCE  ·  EDGE WEIGHT ∝ CO-OCCURRENCE
        </text>
      </svg>
    </div>
  );
}

/* ── Characters view ─────────────────────────────────────────── */
export default function CharactersView({ events }: { events: TimelineEvent[] }) {
  // Derive characters from events
  const chars = useMemo<Character[]>(() => {
    const map = new Map<string, { chapters: Set<number>; count: number }>();
    events.forEach((e) => {
      e.characters_present.forEach((name) => {
        if (!map.has(name)) map.set(name, { chapters: new Set(), count: 0 });
        const entry = map.get(name)!;
        entry.count++;
        entry.chapters.add(e.chapter_num);
      });
    });
    return Array.from(map.entries())
      .map(([name, { chapters, count }]) => ({
        name,
        event_count: count,
        chapters: Array.from(chapters).sort((a, b) => a - b),
      }))
      .sort((a, b) => b.event_count - a.event_count);
  }, [events]);

  // Co-occurrence weight map
  const weightMap = useMemo<Record<string, number>>(() => {
    const wm: Record<string, number> = {};
    events.forEach((e) => {
      const ps = e.characters_present;
      for (let i = 0; i < ps.length; i++) {
        for (let j = i + 1; j < ps.length; j++) {
          const key = [ps[i], ps[j]].sort().join("||");
          wm[key] = (wm[key] ?? 0) + 1;
        }
      }
    });
    return wm;
  }, [events]);

  const [activeName, setActiveName] = useState(chars[0]?.name ?? "");
  const activeChar = chars.find((c) => c.name === activeName);

  return (
    <div className="px-10 py-8 max-w-[1300px] mx-auto">
      <ViewHeader
        title="Characters"
        subtitle="Co-occurrence graph derived from scene-level presence"
        stats={[
          { v: chars.length,                  l: "Named" },
          { v: Object.keys(weightMap).length, l: "Edges" },
          { v: chars[0]?.event_count ?? 0,    l: "Top arc" },
          { v: "v0.1",                         l: "Status" },
        ]}
      />

      <div className="rounded-sm overflow-hidden mb-6 border border-ivy-rule bg-ivy-bgRaised">
        <div className="px-5 py-3 flex items-center justify-between border-b border-ivy-ruleSoft">
          <div>
            <p className="font-mono text-[10px] uppercase tracking-[0.22em] text-ivy-inkFaint">
              fig. 03 · preview
            </p>
            <h3 className="font-serif text-[18px] text-ivy-inkDeep">Network preview</h3>
          </div>
          <span className="font-mono text-[10px] uppercase tracking-[0.18em] px-2 py-1 rounded-sm border border-ivy-rule text-ivy-inkMute">
            force-layout · planned for v1.0
          </span>
        </div>
        <CharacterNetwork
          chars={chars}
          weightMap={weightMap}
          activeName={activeName}
          setActiveName={setActiveName}
        />
      </div>

      <div className="grid grid-cols-12 gap-6">
        <div className="col-span-7">
          <div className="rounded-sm border border-ivy-rule bg-ivy-bgRaised">
            <div
              className="grid items-center gap-3 px-5 py-2.5 text-[10px] font-mono uppercase tracking-[0.18em] text-ivy-inkFaint border-b border-ivy-rule"
              style={{ gridTemplateColumns: "minmax(0,1fr) 120px 70px 70px" }}
            >
              <span>character</span>
              <span>chapters</span>
              <span className="text-right">events</span>
              <span className="text-right">ch.</span>
            </div>
            {chars.map((c, i) => (
              <button
                key={c.name}
                onClick={() => setActiveName(c.name)}
                className="grid items-center gap-3 w-full px-5 py-3 text-left"
                style={{
                  gridTemplateColumns: "minmax(0,1fr) 120px 70px 70px",
                  borderBottom: i < chars.length - 1 ? "1px solid var(--ivy-ruleSoft)" : "none",
                  background: activeName === c.name ? "var(--ivy-bgInk)" : "transparent",
                }}
              >
                <span className="flex items-center gap-2.5">
                  <span
                    className="h-2 w-2 rounded-full"
                    style={{ background: activeName === c.name ? "var(--ivy-accent)" : "var(--ivy-inkMute)" }}
                  />
                  <span className="font-serif text-[15px] text-ivy-inkDeep">{c.name}</span>
                </span>
                <div className="flex flex-wrap gap-0.5">
                  {c.chapters.slice(0, 6).map((ch) => (
                    <span key={ch} className="font-mono text-[9px] px-1 rounded-sm bg-ivy-bgInk border border-ivy-ruleSoft text-ivy-inkFaint">
                      {ch}
                    </span>
                  ))}
                  {c.chapters.length > 6 && (
                    <span className="font-mono text-[9px] text-ivy-inkFaint">+{c.chapters.length - 6}</span>
                  )}
                </div>
                <Mono className="text-[12px] text-right text-ivy-ink">{c.event_count}</Mono>
                <Mono className="text-[12px] text-right text-ivy-ink">{c.chapters.length}</Mono>
              </button>
            ))}
          </div>
        </div>
        <div className="col-span-5">
          {activeChar && <CharacterDetail char={activeChar} weightMap={weightMap} />}
        </div>
      </div>
    </div>
  );
}
