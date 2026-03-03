from __future__ import annotations

import io
import re
from typing import TypedDict, Any

import pdfplumber
from pdfplumber.utils import resolve
from integrations.azure.blob_repository import download_blob_bytes

class Bookmark(TypedDict):
    level: int
    title: str
    page_num: int | str
    y_coordinate: float | str


def send_chunks(blob_name: str) -> dict[str, object]:
    pdf_bytes = download_blob_bytes(blob_name)
    return parse_and_clean(pdf_bytes)


def parse_and_clean(pdf_bytes: bytes) -> dict[str, object]:
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        toc = extract_toc(pdf)

        if not toc:
            return {"error": "No table of contents found in the PDF."}

        chapter_bounds = _find_chapter_page_bounds(toc, len(pdf.pages))
        if chapter_bounds:
            start_page, end_page = chapter_bounds
        else:
            start_page = _find_first_content_page(toc)
            end_page = len(pdf.pages)

        if isinstance(start_page, int):
            text_chunks = []
            for i in range(start_page, end_page):
                page_text = pdf.pages[i].extract_text()
                if page_text:
                    text_chunks.append(page_text)

            full_text = "\n".join(text_chunks)
        else:
            full_text = ""

        return {
            "title": "Full Book (Starting at Chapter 1)",
            "text": _normalize_text(full_text),
            "full_toc": toc
        }


def extract_section_text(pdf: pdfplumber.pdf.PDF, toc: list[Bookmark], index: int) -> str:
    """Helper to extract text from a specific TOC section until the next section begins."""
    start_page = toc[index]["page_num"]

    if not isinstance(start_page, int):
        return ""

    end_page = len(pdf.pages)

    if index + 1 < len(toc):
        next_page = toc[index + 1]["page_num"]
        if isinstance(next_page, int):
            end_page = next_page

    text_chunks = []
    for i in range(start_page, max(start_page + 1, end_page)):
        if i < len(pdf.pages):
            page_text = pdf.pages[i].extract_text()
            if page_text:
                text_chunks.append(page_text)

    return "\n".join(text_chunks)


def extract_toc(pdf: pdfplumber.pdf.PDF) -> list[Bookmark]:
    page_id_to_num = {}
    for i, page in enumerate(pdf.pages):
        page_id = _get_page_ref_id(page.page_obj)
        if page_id is not None:
            page_id_to_num[page_id] = i

    try:
        outlines = pdf.doc.get_outlines()
    except Exception:
        print("No outlines/bookmarks found in this PDF.")
        return []

    bookmarks: list[Bookmark] = []

    # Fixed loop variable name
    for outline in outlines:
        level, title, dest, action, se = outline

        page_num = "Unknown"
        y_coordinate = "Unknown"

        if dest:
            resolved_dest = resolve(dest)

            if isinstance(resolved_dest, list) and len(resolved_dest) > 0:
                page_ref = resolved_dest[0]

                page_ref_id = _get_page_ref_id(page_ref)
                if page_ref_id is not None:
                    page_num = page_id_to_num.get(page_ref_id, "Unknown")

                if len(resolved_dest) >= 4 and resolved_dest[1].name == 'XYZ':
                    y_coordinate = resolved_dest[3]
        elif action:
            resolved_action = resolve(action)
            if isinstance(resolved_action, dict):
                destination = resolved_action.get(b"D", resolved_action.get("D"))
                if destination is None:
                    destination = resolved_action.get(b"Dest", resolved_action.get("Dest"))

                if destination is not None:
                    action_dest = resolve(destination)
                else:
                    action_dest = None

                if isinstance(action_dest, list) and len(action_dest) > 0:
                    page_ref = action_dest[0]
                    page_ref_id = _get_page_ref_id(page_ref)
                    if page_ref_id is not None:
                        page_num = page_id_to_num.get(page_ref_id, "Unknown")

        bookmarks.append({
            "level": level,
            "title": title,
            "page_num": page_num,
            "y_coordinate": y_coordinate
        })

    return bookmarks


def _normalize_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"-\n(?=[a-z])", "", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def _find_chapter_page_bounds(
    toc: list[Bookmark],
    total_pages: int,
) -> tuple[int, int] | None:
    chapter_entries: list[tuple[int, int]] = []

    for idx, item in enumerate(toc):
        page_num = item["page_num"]
        if not isinstance(page_num, int):
            continue
        if _is_front_matter_title(item["title"]):
            continue
        if _chapter_number(item["title"]) is not None:
            chapter_entries.append((idx, page_num))

    if not chapter_entries:
        return None

    first_chapter_one_idx = next(
        (idx for idx, _ in chapter_entries if _chapter_number(toc[idx]["title"]) == 1), None
    )
    if first_chapter_one_idx is None:
        return None

    start_page = toc[first_chapter_one_idx]["page_num"]
    if not isinstance(start_page, int):
        return None

    # Determine the level of top-level chapters (e.g. level=1 for "Chapter 1")
    chapter_level = min(toc[idx]["level"] for idx, _ in chapter_entries)

    # Only consider top-level chapter entries — ignore sub-sections like "1.1 Intro"
    top_level_chapters = [
        (idx, pg) for idx, pg in chapter_entries
        if toc[idx]["level"] == chapter_level
    ]
    last_top_chapter_idx = top_level_chapters[-1][0]

    # Walk forward past any sub-entries of the last chapter;
    # stop at the first same-or-higher-level entry (back matter, index, etc.)
    end_page = total_pages
    for i in range(last_top_chapter_idx + 1, len(toc)):
        if toc[i]["level"] > chapter_level:
            continue  # skip sub-sections of the last chapter
        page_num = toc[i]["page_num"]
        if isinstance(page_num, int):
            end_page = page_num
            break

    end_page = max(start_page + 1, min(total_pages, end_page))
    return start_page, end_page


def _chapter_number(title: str) -> int | None:
    match = re.search(r"\bchapter\s+([0-9]+)\b", title, re.IGNORECASE)
    if match:
        return int(match.group(1))

    number_words = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
        "thirteen": 13,
        "fourteen": 14,
        "fifteen": 15,
        "sixteen": 16,
        "seventeen": 17,
        "eighteen": 18,
        "nineteen": 19,
        "twenty": 20,
        "twenty-one": 21,
        "twenty-two": 22,
        "twenty-three": 23,
        "twenty-four": 24,
        "twenty-five": 25,
        "twenty-six": 26,
        "twenty-seven": 27,
        "twenty-eight": 28,
        "twenty-nine": 29,
        "thirty": 30,
    }

    _num_words_pattern = "|".join(number_words.keys())
    word_match = re.search(r"\bchapter\s+({_num_words_pattern})\b", title, re.IGNORECASE)
    if word_match:
        return number_words[word_match.group(1).lower()]

    leading_number = re.match(r"^\s*(\d{1,3})\b", title)
    if leading_number:
        return int(leading_number.group(1))

    leading_word = re.match(r"^\s*(one|two|three|four|five|six|seven|eight|nine|ten)\b", title, re.IGNORECASE)
    if leading_word:
        return number_words[leading_word.group(1).lower()]

    return None


def _is_front_matter_title(title: str) -> bool:
    normalized = re.sub(r"[^a-z0-9\s]", " ", title.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()

    front_matter_terms = (
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
    )
    return any(term in normalized for term in front_matter_terms)


def _find_first_content_page(toc: list[Bookmark]) -> int | str:
    for item in toc:
        if _is_front_matter_title(item["title"]):
            continue

        if isinstance(item["page_num"], int):
            return item["page_num"]

    return toc[0]["page_num"]


def _get_page_ref_id(page_ref: Any) -> int | None:
    for attr in ("objid", "pageid"):
        value = getattr(page_ref, attr, None)
        if isinstance(value, int):
            return value

    return None
