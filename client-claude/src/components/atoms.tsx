import type { HTMLAttributes, ReactNode } from "react";

/* ── Mono number span ─────────────────────────────────────────── */
export function Mono({ children, className = "", ...rest }: HTMLAttributes<HTMLSpanElement>) {
  return (
    <span className={`font-mono tabular-nums ${className}`} {...rest}>
      {children}
    </span>
  );
}

/* ── Hairline rule ───────────────────────────────────────────── */
export function Hairline({ className = "" }: { className?: string }) {
  return <div className={`h-px w-full bg-ivy-rule ${className}`} />;
}

/* ── Severity dot ────────────────────────────────────────────── */
export function SevDot({ level }: { level: string }) {
  const cls =
    level === "high"   ? "bg-ivy-sevHigh" :
    level === "medium" ? "bg-ivy-sevMed"  : "bg-ivy-sevLow";
  return <span className={`inline-block h-2 w-2 rounded-full align-middle ${cls}`} />;
}

/* ── View header (shared across all views) ───────────────────── */
type Stat = { v: number | string; l: string };

export function ViewHeader({
  kicker, title, subtitle, stats,
}: {
  kicker: string;
  title: string;
  subtitle?: string;
  stats?: Stat[];
}) {
  return (
    <div className="mb-8">
      <div className="mb-6">
        <p className="font-mono text-[10px] uppercase tracking-[0.28em] mb-2 text-ivy-inkFaint">
          <span className="text-ivy-accent">—</span> {kicker}
        </p>
        <h1 className="font-serif text-[40px] leading-none tracking-tight text-ivy-inkDeep">
          {title}
        </h1>
        {subtitle && (
          <p className="text-[13px] mt-2 text-ivy-inkMute">{subtitle}</p>
        )}
      </div>
      {stats && (
        <div className="grid grid-cols-4 border-t border-b border-ivy-rule">
          {stats.map((s, i) => (
            <div
              key={i}
              className="px-4 py-3"
              style={{ borderRight: i < stats.length - 1 ? "1px solid var(--ivy-ruleSoft)" : "none" }}
            >
              <p className="font-serif text-[26px] leading-none text-ivy-inkDeep">{s.v}</p>
              <p className="font-mono text-[10px] uppercase tracking-[0.18em] mt-1.5 text-ivy-inkFaint">{s.l}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Detail field ────────────────────────────────────────────── */
export function DetailField({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <p className="font-mono text-[10px] uppercase tracking-[0.22em] mb-1.5 text-ivy-inkFaint">{label}</p>
      <div className="text-[13px] text-ivy-ink">{children}</div>
    </div>
  );
}
