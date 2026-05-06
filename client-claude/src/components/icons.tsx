import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

function base(content: React.ReactNode, size = 18) {
  return (p: IconProps) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" {...p}>
      {content}
    </svg>
  );
}

export const IconLibrary = base(
  <><rect x="4" y="4" width="3" height="16"/><rect x="9" y="4" width="3" height="16"/><path d="M14 5.5l3-.8 3.5 14.5-3 .8z"/></>
);
export const IconManuscript = base(
  <><path d="M6 3h11l3 3v15H6z"/><path d="M9 8h8M9 12h8M9 16h5"/></>
);
export const IconTimeline = base(
  <><path d="M3 12h18"/><circle cx="7" cy="12" r="2"/><circle cx="13" cy="12" r="2"/><circle cx="19" cy="12" r="2"/><path d="M7 10v-3M13 14v3M19 10v-3"/></>
);
export const IconIssues = base(
  <><path d="M12 3l9 16H3z"/><path d="M12 10v4M12 17v.5"/></>
);
export const IconCharacters = base(
  <><circle cx="6" cy="7" r="2.5"/><circle cx="18" cy="7" r="2.5"/><circle cx="12" cy="17" r="2.5"/><path d="M7.5 8.5l3 7M16.5 8.5l-3 7M8 7h8"/></>
);
export const IconUpload = base(
  <><path d="M12 16V4M7 9l5-5 5 5"/><path d="M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"/></>
);
export const IconSearch = base(
  <><circle cx="11" cy="11" r="6"/><path d="M20 20l-4-4"/></>,
  16
);
export const IconArrowRight = (p: IconProps) => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" {...p}>
    <path d="M5 12h14M13 6l6 6-6 6"/>
  </svg>
);
export const IconClose = (p: IconProps) => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" {...p}>
    <path d="M6 6l12 12M18 6L6 18"/>
  </svg>
);
