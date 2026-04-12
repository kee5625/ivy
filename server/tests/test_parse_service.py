from __future__ import annotations

from services.parse_service import (
    _chapter_number,
    _find_top_level_content_entries,
    _normalize_text,
)


def test_normalize_text_joins_hyphenated_line_breaks() -> None:
    text = "com-\nputer\n\n\nscience"

    assert _normalize_text(text) == "computer\n\nscience"


def test_chapter_number_handles_numeric_and_word_titles() -> None:
    assert _chapter_number("Chapter 5") == 5
    assert _chapter_number("Chapter Twenty-Three") == 23
    assert _chapter_number("12. A New Day") == 12
    assert _chapter_number("No chapter here") is None


def test_find_top_level_content_entries_skips_front_and_back_matter() -> None:
    toc = [
        {"level": 1, "title": "Contents", "page_num": 0, "y_coordinate": "Unknown"},
        {"level": 1, "title": "Part One", "page_num": 1, "y_coordinate": "Unknown"},
        {"level": 2, "title": "Hidden detail", "page_num": 2, "y_coordinate": "Unknown"},
        {"level": 1, "title": "Afterword", "page_num": 40, "y_coordinate": "Unknown"},
    ]

    result = _find_top_level_content_entries(toc)

    assert result == [
        {"level": 1, "title": "Part One", "page_num": 1, "y_coordinate": "Unknown"}
    ]
