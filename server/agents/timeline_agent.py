"""Timeline agent for building a globally ordered story timeline."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import uuid
from typing import Any

from langgraph.func import entrypoint, task

from db.repository import ChapterRepository, JobRepository, TimelineRepository
from utils.client import (
    final_order_chat_completion,
    merge_timeline_chat_completion,
    timeline_chat_completion,
)
from utils.job import set_job_status

logger = logging.getLogger(__name__)

_MAX_TIMELINE_EVENTS = 120
_MAX_CHAPTERS_FOR_PROMPT = 200
_MAX_CHAPTER_SUMMARY_CHARS = 700
_MAX_KEY_EVENTS_PER_CHAPTER = 4
_MAX_CHARACTERS_PER_CHAPTER = 8
_MAX_TEMPORAL_MARKERS_PER_CHAPTER = 4
_MAX_EVENTS_PER_CHAPTER = 4
_MERGE_BATCH_EVENT_LIMIT = 24
_LOCAL_RETRY_ATTEMPTS = 2
_CHAPTER_CONCURRENCY = 6


# ---------------------------------------------------------------------------
# Payload / normalization helpers
# ---------------------------------------------------------------------------

def _build_local_chapter_payload(chapter: dict[str, Any]) -> dict[str, Any]:
    summary = chapter.get("summary") or []
    key_events = chapter.get("key_events") or []
    temporal_markers = chapter.get("temporal_markers") or []
    characters = chapter.get("characters") or []

    summary_text = " ".join(
        s.strip() for s in summary if isinstance(s, str) and s.strip()
    )[:_MAX_CHAPTER_SUMMARY_CHARS]

    return {
        "chapter_num": int(chapter.get("chapter_num", 0)),
        "chapter_title": str(chapter.get("title", "")).strip(),
        "summary_text": summary_text,
        "key_events": [e.strip() for e in key_events if isinstance(e, str) and e.strip()][:_MAX_KEY_EVENTS_PER_CHAPTER],
        "characters": [c.strip() for c in characters if isinstance(c, str) and c.strip()][:_MAX_CHARACTERS_PER_CHAPTER],
        "temporal_markers": [t.strip() for t in temporal_markers if isinstance(t, str) and t.strip()][:_MAX_TEMPORAL_MARKERS_PER_CHAPTER],
    }


def _normalize_local_events(chapter: dict[str, Any], raw_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    chapter_num = int(chapter.get("chapter_num", 0))
    chapter_title = str(chapter.get("title", "")).strip()
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

        normalized.append({
            "source_event_id": f"ch_{chapter_num:02d}_evt_{idx:02d}",
            "description": description.strip(),
            "chapter_num": chapter_num,
            "chapter_title": chapter_title,
            "order": idx,
            "characters_present": [str(v).strip() for v in characters_present if isinstance(v, (str, int, float)) and str(v).strip()],
            "location": location,
            "time_reference": time_reference,
            "confidence": confidence_value,
        })

    return normalized[:_MAX_EVENTS_PER_CHAPTER]


def _build_merge_payload(local_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[int, dict[str, Any]] = {}
    for event in local_events:
        chapter_num = int(event["chapter_num"])
        if chapter_num not in grouped:
            grouped[chapter_num] = {
                "chapter_num": chapter_num,
                "chapter_title": event.get("chapter_title", ""),
                "events": [],
            }
        grouped[chapter_num]["events"].append({
            "source_event_id": event["source_event_id"],
            "description": event["description"],
            "characters_present": event.get("characters_present", []),
            "location": event.get("location"),
            "time_reference": event.get("time_reference"),
            "confidence": event.get("confidence"),
        })
    return [grouped[k] for k in sorted(grouped)]


def _prepare_merged_events(raw_events: list[dict[str, Any]], local_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    local_map = {str(e["source_event_id"]): e for e in local_events if isinstance(e.get("source_event_id"), str)}
    source_ids = set(local_map.keys())
    prepared: list[dict[str, Any]] = []
    seen: set[str] = set()

    for raw in raw_events:
        sid = raw.get("source_event_id")
        if not isinstance(sid, str) or sid not in source_ids or sid in seen:
            continue
        seen.add(sid)
        local = local_map[sid]
        anchor_id = raw.get("relative_time_anchor_event_id")
        relative_anchor = f"after {anchor_id}" if isinstance(anchor_id, str) and anchor_id in source_ids else None

        prepared.append({
            "event_id": sid,
            "description": raw.get("description") or local.get("description"),
            "chapter_num": raw.get("chapter_num", local.get("chapter_num")),
            "chapter_title": raw.get("chapter_title", local.get("chapter_title")),
            "order": raw.get("order", local.get("order")),
            "local_order": local.get("order"),
            "characters_present": raw.get("characters_present", local.get("characters_present")),
            "location": raw.get("location", local.get("location")),
            "causes": [v for v in raw.get("causes", []) if isinstance(v, str) and v in source_ids],
            "caused_by": [v for v in raw.get("caused_by", []) if isinstance(v, str) and v in source_ids],
            "time_reference": raw.get("time_reference", local.get("time_reference")),
            "inferred_date": raw.get("inferred_date"),
            "inferred_year": raw.get("inferred_year"),
            "relative_time_anchor": relative_anchor,
            "confidence": raw.get("confidence", local.get("confidence")),
        })

    missing = source_ids - seen
    if missing:
        raise RuntimeError("Merge omitted source events: " + ", ".join(sorted(missing)))
    return prepared


def _build_prepared_from_local(local_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "event_id": e["source_event_id"],
        "description": e.get("description"),
        "chapter_num": e.get("chapter_num"),
        "chapter_title": e.get("chapter_title"),
        "order": e.get("order"),
        "local_order": e.get("order"),
        "characters_present": e.get("characters_present", []),
        "location": e.get("location"),
        "causes": [],
        "caused_by": [],
        "time_reference": e.get("time_reference"),
        "inferred_date": None,
        "inferred_year": None,
        "relative_time_anchor": None,
        "confidence": e.get("confidence"),
    } for e in local_events]


def _normalize_final_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
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

        confidence = raw.get("confidence")
        try:
            confidence_value: float | None = max(0.0, min(1.0, float(confidence)))
        except Exception:
            confidence_value = None

        inferred_year = raw.get("inferred_year")
        try:
            year_int = int(inferred_year)
            year_value: int | None = year_int if 1 <= year_int <= 3000 else None
        except Exception:
            year_value = None

        normalized.append({
            "_source_event_id": event_id,
            "event_id": event_id,
            "description": description.strip(),
            "chapter_num": chapter_num,
            "chapter_title": str(raw.get("chapter_title") or "").strip(),
            "order": order,
            "characters_present": [str(v).strip() for v in (raw.get("characters_present") or []) if str(v).strip()],
            "location": raw.get("location") if isinstance(raw.get("location"), str) and raw.get("location", "").strip() else None,
            "causes": [str(v).strip() for v in (raw.get("causes") or []) if isinstance(v, str) and v.strip()],
            "caused_by": [str(v).strip() for v in (raw.get("caused_by") or []) if isinstance(v, str) and v.strip()],
            "time_reference": raw.get("time_reference") if isinstance(raw.get("time_reference"), str) and raw.get("time_reference", "").strip() else None,
            "inferred_date": raw.get("inferred_date") if isinstance(raw.get("inferred_date"), str) and raw.get("inferred_date", "").strip() else None,
            "inferred_year": year_value,
            "relative_time_anchor": raw.get("relative_time_anchor") if isinstance(raw.get("relative_time_anchor"), str) and raw.get("relative_time_anchor", "").strip() else None,
            "confidence": confidence_value,
        })

    normalized.sort(key=lambda e: int(e["order"]))
    event_id_mapping: dict[str, str] = {}
    for idx, item in enumerate(normalized, start=1):
        item["order"] = idx
        new_id = f"evt_{idx:03d}"
        event_id_mapping[item["_source_event_id"]] = new_id
        item["event_id"] = new_id

    final_ids = set(event_id_mapping.values())
    for item in normalized:
        item["causes"] = _remap_refs(item.get("causes", []), event_id_mapping, final_ids)
        item["caused_by"] = _remap_refs(item.get("caused_by", []), event_id_mapping, final_ids)
        item["relative_time_anchor"] = _remap_anchor(item.get("relative_time_anchor"), event_id_mapping)
        item.pop("_source_event_id", None)

    return normalized


def _remap_refs(refs: list[str], mapping: dict[str, str], final_ids: set[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for ref in refs:
        candidate = mapping.get(ref) if ref in mapping else (ref if ref in final_ids else None)
        if candidate and candidate not in seen:
            seen.add(candidate)
            out.append(candidate)
    return out


def _remap_anchor(anchor: str | None, mapping: dict[str, str]) -> str | None:
    if not anchor or not mapping:
        return anchor
    pattern = re.compile("|".join(re.escape(k) for k in sorted(mapping.keys(), key=len, reverse=True)))
    return pattern.sub(lambda m: mapping[m.group(0)], anchor)


def _sort_local_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(events, key=lambda e: (int(e.get("chapter_num", 0)), int(e.get("order", 0)), str(e.get("source_event_id", ""))))


def _deterministic_order(prepared: list[dict[str, Any]]) -> list[str]:
    ordered = sorted(prepared, key=lambda e: (int(e.get("chapter_num", 0)), int(e.get("local_order") or e.get("order", 0) or 0)))
    return [str(e["event_id"]) for e in ordered]


def _apply_ordered_ids(prepared: list[dict[str, Any]], ordered_ids: list[str]) -> list[dict[str, Any]]:
    lookup = {str(e["event_id"]): dict(e) for e in prepared if isinstance(e.get("event_id"), str)}
    missing = set(lookup.keys()) - set(ordered_ids)
    if missing:
        raise RuntimeError("Ordered ids omitted prepared events: " + ", ".join(sorted(missing)))
    result: list[dict[str, Any]] = []
    for order, sid in enumerate(ordered_ids, start=1):
        event = lookup.get(sid)
        if event:
            event["order"] = order
            result.append(event)
    return result


# ---------------------------------------------------------------------------
# LangGraph tasks
# ---------------------------------------------------------------------------

@task
async def load_chapters(job_id: str) -> list[dict[str, Any]]:
    chapters = await ChapterRepository.get_by_job(job_id)
    if not chapters:
        raise RuntimeError(f"No chapters found for job '{job_id}'. Run ingestion first.")
    chapters = sorted(chapters, key=lambda c: int(c.get("chapter_num", 0)))
    if len(chapters) > _MAX_CHAPTERS_FOR_PROMPT:
        logger.warning("[TimelineAgent] job=%s truncating chapters from %d to %d", job_id, len(chapters), _MAX_CHAPTERS_FOR_PROMPT)
        chapters = chapters[:_MAX_CHAPTERS_FOR_PROMPT]
    logger.info("[TimelineAgent] job=%s loaded %d chapters", job_id, len(chapters))
    return chapters


@task
def extract_local_timeline_for_chapter(chapter: dict[str, Any]) -> list[dict[str, Any]]:
    chapter_num = int(chapter.get("chapter_num", 0))
    last_exc: Exception | None = None

    for attempt in range(1, _LOCAL_RETRY_ATTEMPTS + 1):
        try:
            payload = _build_local_chapter_payload(chapter)
            raw_events = timeline_chat_completion(payload)
            normalized = _normalize_local_events(chapter, raw_events)
            logger.info("[TimelineAgent] chapter=%d extracted %d event(s) (attempt %d)", chapter_num, len(normalized), attempt)
            return normalized
        except Exception as exc:
            last_exc = exc
            logger.warning("[TimelineAgent] chapter=%d attempt %d/%d failed: %r", chapter_num, attempt, _LOCAL_RETRY_ATTEMPTS, exc)

    raise RuntimeError(f"Chapter {chapter_num} local timeline failed after {_LOCAL_RETRY_ATTEMPTS} attempts: {repr(last_exc)}") from last_exc


@task
async def extract_local_timelines(chapters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    semaphore = asyncio.Semaphore(_CHAPTER_CONCURRENCY)

    async def extract_one(chapter: dict[str, Any]) -> list[dict[str, Any]] | Exception:
        async with semaphore:
            try:
                return await asyncio.to_thread(extract_local_timeline_for_chapter_sync, chapter)
            except Exception as exc:
                logger.error("[TimelineAgent] chapter=%s failed: %r", chapter.get("chapter_num"), exc)
                return exc

    results = await asyncio.gather(*[extract_one(ch) for ch in chapters])

    all_events: list[dict[str, Any]] = []
    failures = 0
    for result in results:
        if isinstance(result, Exception):
            failures += 1
        else:
            all_events.extend(result)

    if failures == len(chapters):
        raise RuntimeError(f"Local timeline extraction failed for all {failures} chapters")
    if failures:
        logger.warning("[TimelineAgent] %d/%d chapters failed local extraction", failures, len(chapters))

    logger.info("[TimelineAgent] extracted %d local events from %d chapters", len(all_events), len(chapters) - failures)
    return all_events


def extract_local_timeline_for_chapter_sync(chapter: dict[str, Any]) -> list[dict[str, Any]]:
    """Sync wrapper for use with asyncio.to_thread."""
    chapter_num = int(chapter.get("chapter_num", 0))
    last_exc: Exception | None = None

    for attempt in range(1, _LOCAL_RETRY_ATTEMPTS + 1):
        try:
            payload = _build_local_chapter_payload(chapter)
            raw_events = timeline_chat_completion(payload)
            return _normalize_local_events(chapter, raw_events)
        except Exception as exc:
            last_exc = exc
            logger.warning("[TimelineAgent] chapter=%d attempt %d/%d failed: %r", chapter_num, attempt, _LOCAL_RETRY_ATTEMPTS, exc)

    raise RuntimeError(f"Chapter {chapter_num} failed after {_LOCAL_RETRY_ATTEMPTS} attempts: {repr(last_exc)}") from last_exc


@task
def merge_batch_events(local_events: list[dict[str, Any]], batch_index: int, batch_count: int) -> list[dict[str, Any]]:
    source_ids = {e["source_event_id"] for e in local_events}
    payload = _build_merge_payload(local_events)

    try:
        raw_events = merge_timeline_chat_completion(payload)
        prepared = _prepare_merged_events(raw_events, local_events)
        logger.info("[TimelineAgent] merge batch %d/%d produced %d events", batch_index, batch_count, len(prepared))
        return prepared
    except Exception as exc:
        logger.warning("[TimelineAgent] merge batch %d/%d failed, using local fallback: %r", batch_index, batch_count, exc)
        fallback = _build_prepared_from_local(local_events)
        if {e["event_id"] for e in fallback} != source_ids:
            raise RuntimeError("Local fallback failed to preserve source event coverage") from exc
        return fallback


@task
def merge_local_timelines(local_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = _sort_local_events(local_events)
    batch_limit = _MERGE_BATCH_EVENT_LIMIT

    if len(ordered) <= batch_limit:
        logger.info("[TimelineAgent] single-pass merge with %d events", len(ordered))
        prepared = merge_batch_events_sync(ordered, 1, 1)
        return _normalize_final_events(prepared)

    batches = [ordered[i:i + batch_limit] for i in range(0, len(ordered), batch_limit)]
    logger.info("[TimelineAgent] batched merge: %d events across %d batches", len(ordered), len(batches))

    merged: list[dict[str, Any]] = []
    for i, batch in enumerate(batches, start=1):
        merged.extend(merge_batch_events_sync(batch, i, len(batches)))

    # Final global ordering pass
    final_order_payload = [{
        "source_event_id": e["event_id"],
        "description": e.get("description"),
        "chapter_num": e.get("chapter_num"),
        "chapter_title": e.get("chapter_title"),
        "local_order": e.get("local_order"),
        "time_reference": e.get("time_reference"),
        "causes": e.get("causes", []),
        "caused_by": e.get("caused_by", []),
    } for e in merged]

    try:
        source_id_set = {str(e["event_id"]) for e in merged}
        raw_ids = final_order_chat_completion(final_order_payload)
        ordered_ids = [i for i in raw_ids if i in source_id_set]
        missing = source_id_set - set(ordered_ids)
        if missing:
            raise RuntimeError("Final ordering omitted events: " + ", ".join(sorted(missing)))
        final = _apply_ordered_ids(merged, ordered_ids)
    except Exception as exc:
        logger.warning("[TimelineAgent] final ordering failed, using deterministic fallback: %r", exc)
        fallback_ids = _deterministic_order(merged)
        final = _apply_ordered_ids(merged, fallback_ids)

    return _normalize_final_events(final)


def merge_batch_events_sync(local_events: list[dict[str, Any]], batch_index: int, batch_count: int) -> list[dict[str, Any]]:
    """Sync version for use inside @task merge_local_timelines."""
    source_ids = {e["source_event_id"] for e in local_events}
    payload = _build_merge_payload(local_events)

    try:
        raw_events = merge_timeline_chat_completion(payload)
        return _prepare_merged_events(raw_events, local_events)
    except Exception as exc:
        logger.warning("[TimelineAgent] merge batch %d/%d failed, fallback: %r", batch_index, batch_count, exc)
        fallback = _build_prepared_from_local(local_events)
        if {e["event_id"] for e in fallback} != source_ids:
            raise RuntimeError("Fallback failed to preserve source coverage") from exc
        return fallback


@task
async def persist_events(job_id: str, events: list[dict[str, Any]]) -> int:
    count = 0
    for evt in events:
        await TimelineRepository.create(
            event_id=evt["event_id"],
            job_id=job_id,
            description=evt["description"],
            chapter_num=evt["chapter_num"],
            event_order=evt["order"],
            chapter_title=evt.get("chapter_title"),
            characters_present=evt.get("characters_present", []),
            location=evt.get("location"),
            causes=evt.get("causes", []),
            caused_by=evt.get("caused_by", []),
            time_reference=evt.get("time_reference"),
            inferred_date=evt.get("inferred_date"),
            inferred_year=evt.get("inferred_year"),
            relative_time_anchor=evt.get("relative_time_anchor"),
            confidence=evt.get("confidence"),
        )
        count += 1
    logger.info("[TimelineAgent] job=%s persisted %d timeline events", job_id, count)
    return count


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

@entrypoint()
async def timeline_agent(inputs: dict) -> str:
    """Load chapters → extract local timelines → merge → persist."""
    job_id: str = inputs["job_id"]
    await _update_status(job_id, "timeline_in_progress", "timeline_agent")

    try:
        chapters = await load_chapters(job_id)
        local_events = await extract_local_timelines(chapters)

        if not local_events:
            raise RuntimeError("Timeline local extraction produced no events")

        merged_events = await merge_local_timelines(local_events)
        capped = merged_events[:_MAX_TIMELINE_EVENTS]

        await persist_events(job_id, capped)

        await _update_status(
            job_id,
            "timeline_complete",
            "plot_hole_agent",
            completed_agents=["ingestion_agent", "timeline_agent"],
        )
        logger.info("[TimelineAgent] job=%s complete with %d events", job_id, len(capped))
        return job_id

    except Exception as exc:
        logger.exception("[TimelineAgent] job=%s failed", job_id)
        await _update_status(job_id, "failed", error=str(exc))
        raise


async def _update_status(job_id: str, status: str, current_agent: str | None = None, **kwargs: Any) -> None:
    await JobRepository.update_status(job_id, status=status, current_agent=current_agent, **kwargs)
    await set_job_status(
        job_id,
        status=status,
        current_agent=current_agent,
        completed_agents=kwargs.get("completed_agents", []),
        error=kwargs.get("error"),
    )
