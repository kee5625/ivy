/* Shared atoms: icons, hairline, mono-num, kbd, etc. */

const I = {
  // tiny line icons (24x24, currentColor, 1.5 stroke)
  library: (p={}) => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <rect x="4" y="4" width="3" height="16"/>
      <rect x="9" y="4" width="3" height="16"/>
      <path d="M14 5.5l3 -.8 3.5 14.5 -3 .8z"/>
    </svg>
  ),
  manuscript: (p={}) => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M6 3h11l3 3v15H6z"/><path d="M9 8h8M9 12h8M9 16h5"/>
    </svg>
  ),
  timeline: (p={}) => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M3 12h18"/><circle cx="7" cy="12" r="2"/><circle cx="13" cy="12" r="2"/><circle cx="19" cy="12" r="2"/>
      <path d="M7 10v-3M13 14v3M19 10v-3"/>
    </svg>
  ),
  issues: (p={}) => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M12 3l9 16H3z"/><path d="M12 10v4M12 17v.5"/>
    </svg>
  ),
  characters: (p={}) => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <circle cx="6" cy="7" r="2.5"/><circle cx="18" cy="7" r="2.5"/><circle cx="12" cy="17" r="2.5"/>
      <path d="M7.5 8.5l3 7M16.5 8.5l-3 7M8 7h8"/>
    </svg>
  ),
  upload: (p={}) => (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M12 16V4M7 9l5-5 5 5"/><path d="M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/>
    </svg>
  ),
  search: (p={}) => (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <circle cx="11" cy="11" r="6"/><path d="M20 20l-4-4"/>
    </svg>
  ),
  arrowRight: (p={}) => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M5 12h14M13 6l6 6-6 6"/>
    </svg>
  ),
  close: (p={}) => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" {...p}>
      <path d="M6 6l12 12M18 6L6 18"/>
    </svg>
  ),
  spark: (p={}) => (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...p}>
      <path d="M12 3v6M12 15v6M3 12h6M15 12h6"/>
    </svg>
  ),
};

const Mono = ({ children, className = "", ...rest }) => (
  <span className={`font-mono tabular-nums ${className}`} {...rest}>{children}</span>
);

const Hairline = ({ className = "" }) => (
  <div className={`h-px w-full ${className}`} style={{ background: "var(--ivy-rule)" }}/>
);

// Severity dot
const SevDot = ({ level }) => {
  const c = level === "high" ? "var(--ivy-sev_high)" : level === "medium" ? "var(--ivy-sev_med)" : "var(--ivy-sev_low)";
  return <span className="inline-block h-2 w-2 rounded-full align-middle" style={{ background: c }}/>;
};

// Subtle striped placeholder
const StripePlaceholder = ({ label, h = 120, className = "" }) => (
  <div
    className={`relative overflow-hidden rounded-sm ${className}`}
    style={{
      height: h,
      background: `repeating-linear-gradient(135deg, var(--ivy-bgInk) 0 8px, var(--ivy-panel) 8px 16px)`,
      border: "1px solid var(--ivy-rule)",
    }}
  >
    <span className="absolute bottom-2 left-2 font-mono text-[10px] tracking-wider uppercase" style={{ color: "var(--ivy-inkMute)" }}>
      {label}
    </span>
  </div>
);

Object.assign(window, { I, Mono, Hairline, SevDot, StripePlaceholder });
