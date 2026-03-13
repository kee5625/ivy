from __future__ import annotations

import re
import logging
from typing import TypedDict

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


class Bookmark(TypedDict):
    level: int
    title: str
    page_num: int | str
    y_coordinate: float | str


class ChapterChunk(TypedDict):
    chapter_num: int
    chapter_title: str
    text: str
    start_page: int
    end_page: int


def parse_and_clean(pdf_bytes: bytes) -> dict[str, object]:
    """
    Parse a PDF entirely with PyMuPDF (no pdfplumber/pdfminer).

    Returns
    -------
    {
        "chapters": [ChapterChunk, ...],   # pre-split chapter text
        "full_toc": [Bookmark, ...],       # raw TOC for reference
    }
    or {"error": "..."} on failure.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total_pages = len(doc)

    if total_pages == 0:
        doc.close()
        return {"error": "PDF has no pages."}

    # ── 1. Extract TOC via PyMuPDF (instant — no pdfminer) ────────────────
    raw_toc = doc.get_toc(simple=True)  # [[level, title, page], ...]
    toc = _raw_toc_to_bookmarks(raw_toc)

    if not toc:
        # No TOC at all → return entire book as a single chapter
        logger.warning("No TOC found in PDF — returning full text as one chapter")
        full_text = _extract_page_range(doc, 0, total_pages)
        doc.close()
        return {
            "chapters": [
                {
                    "chapter_num": 1,
                    "chapter_title": "Full Text",
                    "text": _normalize_text(full_text),
                    "start_page": 0,
                    "end_page": total_pages,
                }
            ],
            "full_toc": [],
        }

    # ── 2. Identify chapter page ranges ───────────────────────────────────
    chapters = _build_chapter_chunks(doc, toc, total_pages)

    doc.close()

    if not chapters:
        # Fallback: couldn't identify chapters, treat as one
        logger.warning("Could not identify chapter boundaries — returning full text")
        doc2 = fitz.open(stream=pdf_bytes, filetype="pdf")
        full_text = _extract_page_range(doc2, 0, total_pages)
        doc2.close()
        return {
            "chapters": [
                {
                    "chapter_num": 1,
                    "chapter_title": "Full Text",
                    "text": _normalize_text(full_text),
                    "start_page": 0,
                    "end_page": total_pages,
                }
            ],
            "full_toc": toc,
        }

    return {
        "chapters": chapters,
        "full_toc": toc,
    }


# ── TOC helpers ───────────────────────────────────────────────────────────────


def _raw_toc_to_bookmarks(raw_toc: list[list]) -> list[Bookmark]:
    """Convert PyMuPDF's get_toc() output to our Bookmark format.

    PyMuPDF returns [[level, title, page_number], ...] where page_number is
    1-based.  We convert to 0-based page_num for internal consistency.
    """
    bookmarks: list[Bookmark] = []
    for entry in raw_toc:
        if len(entry) < 3:
            continue
        level, title, page = entry[0], entry[1], entry[2]
        # page is 1-based in PyMuPDF; -1 means unresolved
        page_num: int | str = (page - 1) if isinstance(page, int) and page >= 1 else "Unknown"
        bookmarks.append({
            "level": level,
            "title": title.strip(),
            "page_num": page_num,
            "y_coordinate": "Unknown",
        })
    return bookmarks


# ── Chapter extraction ────────────────────────────────────────────────────────


def _build_chapter_chunks(
    doc: fitz.Document,
    toc: list[Bookmark],
    total_pages: int,
) -> list[ChapterChunk]:
    """
    Identify chapter-level entries in the TOC, compute page ranges, and
    extract text for each chapter directly from the PDF pages.
    """
    # Find chapter page bounds (start of ch1 → end of last chapter)
    chapter_entries = _find_chapter_entries(toc)

    if not chapter_entries:
        # No numbered chapters found — try using all top-level TOC entries
        # that aren't front matter
        chapter_entries = _find_top_level_content_entries(toc)

    if not chapter_entries:
        return []

    # Build page ranges for each chapter
    chunks: list[ChapterChunk] = []
    for i, entry in enumerate(chapter_entries):
        start_page = entry["page_num"]
        if not isinstance(start_page, int):
            continue

        # End page = start of next chapter, or total pages
        if i + 1 < len(chapter_entries):
            next_page = chapter_entries[i + 1]["page_num"]
            end_page = next_page if isinstance(next_page, int) else total_pages
        else:
            # For the last chapter, find the next TOC entry after it that's at
            # the same or higher level (back-matter, appendix, etc.)
            end_page = _find_end_page_for_last_chapter(
                toc, entry, total_pages
            )

        # Clamp
        start_page = max(0, min(start_page, total_pages - 1))
        end_page = max(start_page + 1, min(end_page, total_pages))

        text = _extract_page_range(doc, start_page, end_page)
        if not text.strip():
            continue

        chunks.append({
            "chapter_num": i + 1,
            "chapter_title": entry["title"],
            "text": _normalize_text(text),
            "start_page": start_page,
            "end_page": end_page,
        })

    return chunks


def _find_chapter_entries(toc: list[Bookmark]) -> list[Bookmark]:
    """
    Find numbered chapter entries (e.g., "Chapter 1", "Chapter Two", "3 The
    Beginning") in the TOC, returning only the main book body (ch1 → last
    sequential chapter).
    """
    # Collect all entries that look like numbered chapters
    numbered: list[tuple[int, int, Bookmark]] = []  # (toc_index, chapter_number, bookmark)
    for idx, item in enumerate(toc):
        if not isinstance(item["page_num"], int):
            continue
        if _is_front_matter_title(item["title"]):
            continue
        ch_num = _chapter_number(item["title"])
        if ch_num is not None:
            numbered.append((idx, ch_num, item))

    if not numbered:
        return []

    # Find the entry for "Chapter 1"
    ch1_candidates = [(idx, cn, bk) for idx, cn, bk in numbered if cn == 1]
    if not ch1_candidates:
        # No Chapter 1 found — use all numbered chapters
        return [bk for _, _, bk in numbered]

    # Use the first Chapter 1
    ch1_idx = ch1_candidates[0][0]

    # Determine the chapter level (TOC depth)
    chapter_level = toc[ch1_idx]["level"]

    # Walk forward from Chapter 1, collecting same-level chapters with
    # monotonically increasing chapter numbers
    result: list[Bookmark] = []
    highest = 0
    started = False

    for idx, cn, bk in numbered:
        if bk["level"] != chapter_level:
            continue
        if not started:
            if idx == ch1_idx:
                started = True
            else:
                continue
        if cn < highest:
            break  # hit a second "Chapter 1" or numbering reset → stop
        highest = max(highest, cn)
        result.append(bk)

    return result


def _find_top_level_content_entries(toc: list[Bookmark]) -> list[Bookmark]:
    """
    Fallback: when no numbered chapters are found, use all top-level TOC
    entries that aren't front/back matter.
    """
    if not toc:
        return []

    min_level = min(item["level"] for item in toc)
    entries = []
    for item in toc:
        if item["level"] != min_level:
            continue
        if not isinstance(item["page_num"], int):
            continue
        if _is_front_matter_title(item["title"]):
            continue
        if _is_back_matter_title(item["title"]):
            continue
        entries.append(item)

    return entries


def _find_end_page_for_last_chapter(
    toc: list[Bookmark],
    last_chapter_entry: Bookmark,
    total_pages: int,
) -> int:
    """
    For the last chapter, look for the next TOC entry at the same or higher
    (lower number) level that comes after it — typically back-matter like
    "Appendix", "Glossary", "About the Author", etc.
    """
    chapter_level = last_chapter_entry["level"]
    chapter_page = last_chapter_entry["page_num"]
    if not isinstance(chapter_page, int):
        return total_pages

    found_self = False
    for item in toc:
        if item is last_chapter_entry:
            found_self = True
            continue
        if not found_self:
            continue
        # Only consider entries at same or higher level (same or lower number)
        if item["level"] > chapter_level:
            continue
        page = item["page_num"]
        if isinstance(page, int) and page > chapter_page:
            return page

    return total_pages


# ── Text extraction ───────────────────────────────────────────────────────────


def _extract_page_range(doc: fitz.Document, start: int, end: int) -> str:
    """Extract text from pages [start, end) using PyMuPDF."""
    parts: list[str] = []
    for i in range(start, min(end, len(doc))):
        page_text = doc[i].get_text("text")
        if page_text:
            parts.append(page_text)
    return "\n".join(parts)


# ── Text normalization ────────────────────────────────────────────────────────


def _normalize_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    # Re-join hyphenated line breaks (e.g., "com-\nputer" → "computer")
    normalized = re.sub(r"-\n(?=[a-z])", "", normalized)
    # Collapse excessive blank lines
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


# ── Title classification ─────────────────────────────────────────────────────


_FRONT_MATTER_TERMS = frozenset({
    "copyright",
    "title page",
    "table of contents",
    "contents",
    "introduction",
    "preface",
    "acknowledgements",
    "acknowledgments",
    "foreword",
    "epigraph",
    "prologue",
    "testimonials",
    "praise",
    "dedication",
    "frontispiece",
    "half title",
    "also by",
    "about the author",
    "cover",
})

_BACK_MATTER_TERMS = frozenset({
    "appendix",
    "glossary",
    "bibliography",
    "index",
    "notes",
    "endnotes",
    "afterword",
    "epilogue",
    "about the author",
    "also by",
    "colophon",
    "credits",
    "further reading",
    "reading guide",
    "discussion questions",
})


def _is_front_matter_title(title: str) -> bool:
    normalized = re.sub(r"[^a-z0-9\s]", " ", title.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return any(term in normalized for term in _FRONT_MATTER_TERMS)


def _is_back_matter_title(title: str) -> bool:
    normalized = re.sub(r"[^a-z0-9\s]", " ", title.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return any(term in normalized for term in _BACK_MATTER_TERMS)


# ── Chapter number extraction ────────────────────────────────────────────────

_NUMBER_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20,
    "twenty-one": 21, "twenty-two": 22, "twenty-three": 23,
    "twenty-four": 24, "twenty-five": 25, "twenty-six": 26,
    "twenty-seven": 27, "twenty-eight": 28, "twenty-nine": 29,
    "thirty": 30, "thirty-one": 31, "thirty-two": 32,
    "thirty-three": 33, "thirty-four": 34, "thirty-five": 35,
    "thirty-six": 36, "thirty-seven": 37, "thirty-eight": 38,
    "thirty-nine": 39, "forty": 40,
}

_NUM_WORDS_PATTERN = "|".join(
    re.escape(w) for w in sorted(_NUMBER_WORDS.keys(), key=len, reverse=True)
)


def _chapter_number(title: str) -> int | None:
    # "Chapter 5", "CHAPTER 12"
    match = re.search(r"\bchapter\s+([0-9]+)\b", title, re.IGNORECASE)
    if match:
        return int(match.group(1))

    # "Chapter One", "CHAPTER TWENTY-THREE"
    word_match = re.search(
        rf"\bchapter\s+({_NUM_WORDS_PATTERN})\b", title, re.IGNORECASE
    )
    if word_match:
        return _NUMBER_WORDS.get(word_match.group(1).lower())

    # Leading number: "1 The Beginning", "12. A New Day"
    leading_number = re.match(r"^\s*(\d{1,3})\b", title)
    if leading_number:
        return int(leading_number.group(1))

    # Leading word number: "One", "Two"
    leading_word = re.match(
        rf"^\s*({_NUM_WORDS_PATTERN})\b", title, re.IGNORECASE
    )
    if leading_word:
        return _NUMBER_WORDS.get(leading_word.group(1).lower())

    return None
