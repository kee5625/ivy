import React, { useEffect, useRef, useState } from "react";
import type { Chapter } from "@/types/graph";

type ChapterCardProps = {
  chapter: Chapter;
  animationDelay?: number;
};

export const ChapterCard: React.FC<ChapterCardProps> = ({
  chapter,
  animationDelay = 0,
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [bodyHeight, setBodyHeight] = useState(0);
  const [visible, setVisible] = useState(false);
  const bodyRef = useRef<HTMLDivElement>(null);

  // Trigger entrance animation shortly after mount so the keyframe fires
  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 20);
    return () => clearTimeout(t);
  }, []);

  // Measure body height whenever expanded state or content changes
  useEffect(() => {
    if (bodyRef.current) {
      setBodyHeight(isExpanded ? bodyRef.current.scrollHeight : 0);
    }
  }, [isExpanded, chapter]);

  return (
    <div
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? "translateY(0)" : "translateY(14px)",
        transition: `opacity 0.4s ease ${animationDelay}ms, transform 0.4s ease ${animationDelay}ms`,
      }}
      className="rounded-2xl border border-[#c5dfbf] bg-white shadow-[0_4px_18px_-8px_rgba(50,93,60,0.18)] overflow-hidden"
    >
      {/* Header — always visible, click to expand */}
      <button
        type="button"
        onClick={() => setIsExpanded((prev) => !prev)}
        className="w-full flex items-start justify-between gap-3 px-5 py-4 text-left transition hover:bg-[#f4fbf1] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[#4f8957]/40"
        aria-expanded={isExpanded}
      >
        <div className="flex items-center gap-3 min-w-0">
          {/* Chapter number badge */}
          <span className="shrink-0 flex items-center justify-center h-8 w-8 rounded-full bg-[#eef8ea] border border-[#c5dfbf] text-xs font-bold text-[#4f8957]">
            {chapter.chapter_num}
          </span>

          <span className="font-semibold text-[#2b4a37] text-sm sm:text-base leading-snug truncate">
            {chapter.chapter_title}
          </span>
        </div>

        {/* Chevron */}
        <span
          className="shrink-0 mt-0.5 text-[#4f8957] transition-transform duration-300"
          style={{ transform: isExpanded ? "rotate(180deg)" : "rotate(0deg)" }}
          aria-hidden
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M3 6L8 11L13 6"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </span>
      </button>

      {/* Collapsible body */}
      <div
        style={{
          height: bodyHeight,
          transition: "height 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
          overflow: "hidden",
        }}
      >
        <div ref={bodyRef}>
          <div className="px-5 pb-5 pt-1 space-y-4 border-t border-[#eef8ea]">
            {/* Summary */}
            {chapter.summary.length > 0 && (
              <section>
                <h4 className="mb-2 text-xs font-bold uppercase tracking-widest text-[#4f8957]">
                  Summary
                </h4>
                <ul className="space-y-1.5">
                  {chapter.summary.map((bullet, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-[#2b4a37]">
                      <span className="mt-1.5 shrink-0 h-1.5 w-1.5 rounded-full bg-[#4f8957]" aria-hidden />
                      {bullet}
                    </li>
                  ))}
                </ul>
              </section>
            )}

            {/* Key Events */}
            {chapter.key_events.length > 0 && (
              <section>
                <h4 className="mb-2 text-xs font-bold uppercase tracking-widest text-[#4f8957]">
                  Key Events
                </h4>
                <ol className="space-y-1.5 list-none">
                  {chapter.key_events.map((event, i) => (
                    <li key={i} className="flex items-start gap-2.5 text-sm text-[#2b4a37]">
                      <span className="shrink-0 mt-0.5 flex items-center justify-center h-5 w-5 rounded-full bg-[#eef8ea] border border-[#c5dfbf] text-[10px] font-bold text-[#4f8957]">
                        {i + 1}
                      </span>
                      {event}
                    </li>
                  ))}
                </ol>
              </section>
            )}

            {/* Characters */}
            {chapter.characters.length > 0 && (
              <section>
                <h4 className="mb-2 text-xs font-bold uppercase tracking-widest text-[#4f8957]">
                  Characters
                </h4>
                <div className="flex flex-wrap gap-1.5">
                  {chapter.characters.map((name, i) => (
                    <span
                      key={i}
                      className="inline-flex items-center rounded-full border border-[#c5dfbf] bg-[#f4fbf1] px-2.5 py-0.5 text-xs font-medium text-[#2b4a37]"
                    >
                      {name}
                    </span>
                  ))}
                </div>
              </section>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
