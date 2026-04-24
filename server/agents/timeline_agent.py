"""Timeline agent for building a globally ordered story timeline."""

import json
import re
from typing import Any

from langgraph.func import entrypoint, task

from utils.client import timeline_chat_completion

_MAX_TIMELINE_EVENTS = 120
_MAX_CHAPTERS_FOR_PROMPT = 200
_MAX_CHAPTER_SUMMARY_CHARS = 700
_MAX_KEY_EVENTS_PER_CHAPTER = 4
_MAX_CHARACTERS_PER_CHAPTER = 8
_MAX_TEMPORAL_MARKERS_PER_CHAPTER = 4
_MAX_EVENTS_PER_CHAPTER = 4
_MERGE_BATCH_EVENT_LIMIT = 24


# ---------------------------------------------------------------------------
# Payload / normalization helpers
# ---------------------------------------------------------------------------

def build_local_chapter_payload(chapter: dict[str, Any]) -> dict[str, Any]:
    summary = chapter.get("summary") or []
    key_events = chapter.get("key_events") or []
    temporal_markers = chapter.get("temporal_markers") or []
    characters = chapter.get("characters") or []

    summary_text = " ".join(
        s.strip() for s in summary if isinstance(s, str) and s.strip()
    )[:_MAX_CHAPTER_SUMMARY_CHARS]

    return {
        "chapter_num": int(chapter.get("chapter_num", 0)),
        "chapter_title": str(chapter.get("chapter_title", "")).strip(),
        "summary_text": summary_text,
        "key_events": [
            e.strip() for e in key_events if isinstance(e, str) and e.strip()
        ][:_MAX_KEY_EVENTS_PER_CHAPTER],
        "characters": [
            c.strip() for c in characters if isinstance(c, str) and c.strip()
        ][:_MAX_CHARACTERS_PER_CHAPTER],
        "temporal_markers": [
            t.strip() for t in temporal_markers if isinstance(t, str) and t.strip()
        ][:_MAX_TEMPORAL_MARKERS_PER_CHAPTER],
    }


def normalize_local_events(
    chapter: dict[str, Any],
    raw_events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    chapter_num = int(chapter.get("chapter_num", 0))
    chapter_title = str(chapter.get("chapter_title", "")).strip()
    normalized: list[dict[str, Any]] = []

    for idx, raw in enumerate(raw_events, start=1):
        description = raw.get("description")
        if not isinstance(description, str) or not description.strip():
            continue

        characters_present = raw.get("characters_present")
        if not isinstance(characters_present, list):
            characters_present = []

        location = raw.get("location")
        if not isinstance(location, str) or not location.strip():
            location = None

        time_reference = raw.get("time_reference")
        if not isinstance(time_reference, str) or not time_reference.strip():
            time_reference = None

        confidence = raw.get("confidence")
        try:
            confidence_value = float(confidence)
            confidence_value = max(0.0, min(1.0, confidence_value))
        except Exception:
            confidence_value = None

        normalized.append(
            {
                "source_event_id": f"ch_{chapter_num:02d}_evt_{idx:02d}",
                "description": description.strip(),
                "chapter_num": chapter_num,
                "chapter_title": chapter_title,
                "order": idx,
                "characters_present": [
                    str(v).strip()
                    for v in characters_present
                    if isinstance(v, (str, int, float)) and str(v).strip()
                ],
                "location": location,
                "time_reference": time_reference,
                "confidence": confidence_value,
            }
        )

    return normalized[:_MAX_EVENTS_PER_CHAPTER]


def build_merge_payload(local_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[int, dict[str, Any]] = {}
    for event in local_events:
        chapter_num = int(event["chapter_num"])
        if chapter_num not in grouped:
            grouped[chapter_num] = {
                "chapter_num": chapter_num,
                "chapter_title": event.get("chapter_title", ""),
                "events": [],
            }
        grouped[chapter_num]["events"].append(
            {
                "source_event_id": event["source_event_id"],
                "description": event["description"],
                "characters_present": event.get("characters_present", []),
                "location": event.get("location"),
                "time_reference": event.get("time_reference"),
                "confidence": event.get("confidence"),
            }
        )
    return [grouped[key] for key in sorted(grouped)]


def prepare_merged_events(
    raw_events: list[dict[str, Any]],
    local_events: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    local_event_map = {
        str(event["source_event_id"]): event
        for event in local_events
        if isinstance(event.get("source_event_id"), str)
    }
    source_event_ids = set(local_event_map.keys())
    prepared: list[dict[str, Any]] = []
    seen_source_ids: set[str] = set()

    for raw in raw_events:
        source_event_id = raw.get("source_event_id")
        if not isinstance(source_event_id, str) or source_event_id not in source_event_ids:
            continue
        if source_event_id in seen_source_ids:
            continue
        seen_source_ids.add(source_event_id)

        local_event = local_event_map[source_event_id]
        relative_anchor_id = raw.get("relative_time_anchor_event_id")
        relative_anchor = (
            f"after {relative_anchor_id}"
            if isinstance(relative_anchor_id, str) and relative_anchor_id in source_event_ids
            else None
        )

        prepared.append(
            {
                "event_id": source_event_id,
                "description": raw.get("description") or local_event.get("description"),
                "chapter_num": raw.get("chapter_num", local_event.get("chapter_num")),
                "chapter_title": raw.get("chapter_title", local_event.get("chapter_title")),
                "order": raw.get("order", local_event.get("order")),
                "local_order": local_event.get("order"),
                "characters_present": raw.get("characters_present", local_event.get("characters_present")),
                "location": raw.get("location", local_event.get("location")),
                "causes": [v for v in raw.get("causes", []) if isinstance(v, str) and v in source_event_ids],
                "caused_by": [v for v in raw.get("caused_by", []) if isinstance(v, str) and v in source_event_ids],
                "time_reference": raw.get("time_reference", local_event.get("time_reference")),
                "inferred_date": raw.get("inferred_date"),
                "inferred_year": raw.get("inferred_year"),
                "relative_time_anchor": relative_anchor,
                "confidence": raw.get("confidence", local_event.get("confidence")),
            }
        )

    missing = source_event_ids - seen_source_ids
    if missing:
        raise RuntimeError("Merge output omitted source events: " + ", ".join(sorted(missing)))

    return prepared


def normalize_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for i, raw in enumerate(events, start=1):
        event_id = raw.get("event_id")
        if not isinstance(event_id, str) or not event_id.strip():
            event_id = f"evt_{i:03d}"

        description = raw.get("description")
        if not isinstance(description, str) or not description.strip():
            continue

        try:
            chapter_num = int(raw.get("chapter_num"))
        except Exception:
            chapter_num = 0

        try:
            order = int(raw.get("order"))
        except Exception:
            order = i

        characters_present = raw.get("characters_present") or []
        if not isinstance(characters_present, list):
            characters_present = []

        confidence = raw.get("confidence")
        try:
            confidence_value: float | None = float(confidence)
            confidence_value = max(0.0, min(1.0, confidence_value))
        except Exception:
            confidence_value = None

        inferred_year = raw.get("inferred_year")
        try:
            year_int = int(inferred_year)
            year_value: int | None = year_int if 1 <= year_int <= 3000 else None
        except Exception:
            year_value = None

        normalized.append(
            {
                "_source_event_id": event_id,
                "event_id": event_id,
                "description": description.strip(),
                "chapter_num": chapter_num,
                "chapter_title": str(raw.get("chapter_title") or "").strip(),
                "order": order,
                "characters_present": [str(v).strip() for v in characters_present if str(v).strip()],
                "location": raw.get("location") if isinstance(raw.get("location"), str) and raw.get("location").strip() else None,
                "causes": [str(v).strip() for v in (raw.get("causes") or []) if isinstance(v, str) and v.strip()],
                "caused_by": [str(v).strip() for v in (raw.get("caused_by") or []) if isinstance(v, str) and v.strip()],
                "time_reference": raw.get("time_reference") if isinstance(raw.get("time_reference"), str) and raw.get("time_reference").strip() else None,
                "inferred_date": raw.get("inferred_date") if isinstance(raw.get("inferred_date"), str) and raw.get("inferred_date").strip() else None,
                "inferred_year": year_value,
                "relative_time_anchor": raw.get("relative_time_anchor") if isinstance(raw.get("relative_time_anchor"), str) and raw.get("relative_time_anchor").strip() else None,
                "confidence": confidence_value,
            }
        )

    normalized.sort(key=lambda e: int(e["order"]))
    event_id_mapping: dict[str, str] = {}
    for idx, item in enumerate(normalized, start=1):
        item["order"] = idx
        new_event_id = f"evt_{idx:03d}"
        event_id_mapping[item["_source_event_id"]] = new_event_id
        item["event_id"] = new_event_id

    final_event_ids = set(event_id_mapping.values())
    for item in normalized:
        item["causes"] = _remap_event_references(item.get("causes", []), event_id_mapping, final_event_ids)
        item["caused_by"] = _remap_event_references(item.get("caused_by", []), event_id_mapping, final_event_ids)
        item["relative_time_anchor"] = _remap_relative_time_anchor(item.get("relative_time_anchor"), event_id_mapping)
        item.pop("_source_event_id", None)

    return normalized


def _remap_event_references(
    references: list[str],
    event_id_mapping: dict[str, str],
    final_event_ids: set[str],
) -> list[str]:
    remapped: list[str] = []
    seen: set[str] = set()
    for ref in references:
        candidate = event_id_mapping.get(ref) if ref in event_id_mapping else (ref if ref in final_event_ids else None)
        if candidate and candidate not in seen:
            seen.add(candidate)
            remapped.append(candidate)
    return remapped


def _remap_relative_time_anchor(
    anchor: str | None,
    event_id_mapping: dict[str, str],
) -> str | None:
    if not anchor or not event_id_mapping:
        return anchor
    pattern = re.compile(
        "|".join(re.escape(k) for k in sorted(event_id_mapping.keys(), key=len, reverse=True))
    )
    return pattern.sub(lambda m: event_id_mapping[m.group(0)], anchor)


# ---------------------------------------------------------------------------
# LangGraph tasks
# ---------------------------------------------------------------------------

@task
def load_chapters(job_id: str) -> list[dict[str, Any]]:
    """Load chapters from database for timeline generation."""
    pass


@task
def generate_timeline_events(chapters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Generate timeline events from chapters."""
    pass


@task
def extract_local_timelines(chapters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract local timelines from each chapter."""
    pass


@task
def extract_local_timeline_for_chapter(chapter: dict[str, Any]) -> list[dict[str, Any]]:
    payload = build_local_chapter_payload(chapter)
    raw_events = timeline_chat_completion(payload)
    return normalize_local_events(chapter, raw_events)


@task
def merge_local_timelines(local_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge local timelines into a global story timeline."""
    pass


@task
def merge_batch_events(
    local_events: list[dict[str, Any]],
    batch_index: int,
    batch_count: int,
) -> list[dict[str, Any]]:
    """Merge a batch of local events."""
    pass


@task
def request_compact_final_order(prepared_events: list[dict[str, Any]]) -> list[str]:
    """Request final ordering of events from LLM."""
    pass


@task
def persist_events(job_id: str, events: list[dict[str, Any]]) -> int:
    """Persist timeline events to database."""
    pass


@entrypoint()
def timeline_agent(job_id: str) -> list[dict[str, Any]]:
    """Main timeline generation workflow."""
    pass
