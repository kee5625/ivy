"""Plot hole agent for analyzing & finding plot inconsistencies."""

from __future__ import annotations

import asyncio
import json
import logging
import re
import time
import uuid
from typing import Any

from langgraph.func import entrypoint, task

from db.repository import (
    ChapterRepository,
    EntityRepository,
    JobRepository,
    PlotHoleRepository,
    TimelineRepository,
)
from utils.client import plot_holes_chat_completion
from utils.job import set_job_status

logger = logging.getLogger(__name__)

_SUPPORTED_HOLE_TYPES = {
    "timeline_paradox",
    "location_conflict",
    "dead_character_speaks",
    "unresolved_setup",
}
_SUPPORTED_SEVERITIES = {"high", "medium", "low"}
_CONFIDENCE_THRESHOLD = 0.72
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 2.0
_MAX_FINDINGS = 5
_MAX_CHAPTERS_FOR_PROMPT = 200
_MAX_TIMELINE_EVENTS_FOR_PROMPT = 120
_MAX_SUMMARY_ITEMS = 3
_MAX_KEY_EVENTS = 2
_MAX_CHARACTERS = 5
_MAX_TEMPORAL_MARKERS = 3
_MAX_ENTITY_ALIASES = 2
_MAX_ENTITY_CHAPTERS = 6
_MAX_TIMELINE_CHARACTERS = 4
_MAX_DESCRIPTION_CHARS = 240
_MAX_SUMMARY_TEXT_CHARS = 240
_MAX_EVENT_DESCRIPTION_CHARS = 160
_MAX_LOCATION_CHARS = 60
_MAX_TIME_REFERENCE_CHARS = 60
_MAX_ENTITY_NAME_CHARS = 60
_MAX_ENTITY_COUNT = 80

_RATE_LIMIT_PATTERN = re.compile(r"try again in ([0-9]+(?:\.[0-9]+)?)s", re.IGNORECASE)


# =============================================================================
# String helpers
# =============================================================================

def _clean_string_list(values: Any, *, limit: int | None = None) -> list[str]:
    if not isinstance(values, list):
        return []
    cleaned: list[str] = []
    for value in values:
        if not isinstance(value, (str, int, float)):
            continue
        normalized = str(value).strip()
        if not normalized or normalized in cleaned:
            continue
        cleaned.append(normalized)
        if limit is not None and len(cleaned) >= limit:
            break
    return cleaned


def _clean_optional_string(value: Any) -> str | None:
    if not isinstance(value, (str, int, float)):
        return None
    normalized = str(value).strip()
    return normalized or None


def _trim_text(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    if max_chars <= 3:
        return value[:max_chars]
    return value[: max_chars - 3].rstrip() + "..."


def _trim_optional_text(value: Any, max_chars: int) -> str | None:
    normalized = _clean_optional_string(value)
    if normalized is None:
        return None
    return _trim_text(normalized, max_chars)


def _clean_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _clean_confidence(value: Any) -> float | None:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(1.0, confidence))


# =============================================================================
# Payload builders
# =============================================================================

def _build_story_end_payload(story_state: dict[str, Any]) -> dict[str, Any]:
    chapters = story_state.get("chapters", [])
    timeline = story_state.get("timeline", [])
    final_chapter_num = max(
        (int(c.get("chapter_num", 0) or 0) for c in chapters), default=0
    )
    final_event_id = (
        str(timeline[-1].get("event_id", "")).strip() or None if timeline else None
    )
    return {
        "final_chapter_num": final_chapter_num,
        "final_event_id": final_event_id,
        "timeline_event_count": len(timeline),
    }


def _build_chapter_payload(chapter: dict[str, Any]) -> dict[str, Any]:
    summary_items = _clean_string_list(chapter.get("summary"), limit=_MAX_SUMMARY_ITEMS)
    return {
        "chapter_num": int(chapter.get("chapter_num", 0)),
        "chapter_title": _trim_text(
            str(chapter.get("title", "")).strip(), _MAX_LOCATION_CHARS
        ),
        "summary_text": _trim_text(" ".join(summary_items), _MAX_SUMMARY_TEXT_CHARS),
        "key_events": _clean_string_list(
            [
                _trim_text(v, _MAX_EVENT_DESCRIPTION_CHARS)
                for v in chapter.get("key_events", [])
            ],
            limit=_MAX_KEY_EVENTS,
        ),
        "characters": _clean_string_list(
            chapter.get("characters"), limit=_MAX_CHARACTERS
        ),
        "temporal_markers": _clean_string_list(
            chapter.get("temporal_markers"), limit=_MAX_TEMPORAL_MARKERS
        ),
    }


def _build_timeline_payload(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": str(event.get("event_id", "")).strip(),
        "order": int(event.get("event_order", 0) or 0),
        "chapter_num": int(event.get("chapter_num", 0) or 0),
        "description": _trim_text(
            str(event.get("description", "")).strip(), _MAX_EVENT_DESCRIPTION_CHARS
        ),
        "characters_present": _clean_string_list(
            event.get("characters_present"), limit=_MAX_TIMELINE_CHARACTERS
        ),
        "location": _trim_optional_text(event.get("location"), _MAX_LOCATION_CHARS),
        "causes": _clean_string_list(event.get("causes"), limit=2),
        "caused_by": _clean_string_list(event.get("caused_by"), limit=2),
        "time_reference": _trim_optional_text(
            event.get("time_reference"), _MAX_TIME_REFERENCE_CHARS
        ),
        "inferred_date": _clean_optional_string(event.get("inferred_date")),
        "inferred_year": _clean_int(event.get("inferred_year")),
        "relative_time_anchor": _trim_optional_text(
            event.get("relative_time_anchor"), _MAX_TIME_REFERENCE_CHARS
        ),
        "confidence": _clean_confidence(event.get("confidence")),
    }


def _build_entity_payload(entity: dict[str, Any]) -> dict[str, Any]:
    return {
        "entity_id": _trim_text(
            str(entity.get("entity_id", "")).strip(), _MAX_ENTITY_NAME_CHARS
        ),
        "name": _trim_text(
            str(entity.get("name", "")).strip(), _MAX_ENTITY_NAME_CHARS
        ),
        "entity_type": str(entity.get("entity_type", "")).strip(),
        "appears_in_chapters": sorted(
            {
                int(v)
                for v in entity.get("appears_in_chapters", [])
                if isinstance(v, int)
            }
        )[:_MAX_ENTITY_CHAPTERS],
        "aliases": _clean_string_list(
            [
                _trim_text(v, _MAX_ENTITY_NAME_CHARS)
                for v in entity.get("aliases", [])
            ],
            limit=_MAX_ENTITY_ALIASES,
        ),
        "role": _clean_optional_string(entity.get("role")),
    }


def _select_entities_for_prompt(
    entities: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    prioritized = sorted(
        entities,
        key=lambda e: (
            0 if str(e.get("entity_type", "")).strip() == "character" else 1,
            str(e.get("name", "")).lower(),
        ),
    )
    return prioritized[:_MAX_ENTITY_COUNT]


def _build_prompt_payload(story_state: dict[str, Any]) -> dict[str, Any]:
    chapters = story_state.get("chapters", [])
    timeline = story_state.get("timeline", [])
    entities = _select_entities_for_prompt(story_state.get("entities", []))
    return {
        "story_end": _build_story_end_payload(story_state),
        "chapters": [_build_chapter_payload(c) for c in chapters],
        "timeline_events": [_build_timeline_payload(e) for e in timeline],
        "entities": [_build_entity_payload(e) for e in entities],
    }


def _build_character_lookup(story_state: dict[str, Any]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for entity in story_state.get("entities", []):
        name = _clean_optional_string(entity.get("name"))
        if not name:
            continue
        lookup[name.casefold()] = name
        for alias in _clean_string_list(entity.get("aliases")):
            lookup[alias.casefold()] = name
    for chapter in story_state.get("chapters", []):
        for character in _clean_string_list(chapter.get("characters")):
            lookup.setdefault(character.casefold(), character)
    for event in story_state.get("timeline", []):
        for character in _clean_string_list(event.get("characters_present")):
            lookup.setdefault(character.casefold(), character)
    return lookup


def _normalize_findings(
    story_state: dict[str, Any],
    raw_findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    valid_event_ids = {
        str(e.get("event_id")).strip()
        for e in story_state.get("timeline", [])
        if isinstance(e.get("event_id"), str) and str(e.get("event_id")).strip()
    }
    valid_chapters = {
        int(c.get("chapter_num", 0))
        for c in story_state.get("chapters", [])
    }
    character_lookup = _build_character_lookup(story_state)

    normalized: list[dict[str, Any]] = []
    seen_signatures: set[tuple] = set()

    for raw in raw_findings:
        if not isinstance(raw, dict):
            continue
        hole_type = str(raw.get("hole_type", "")).strip().lower()
        if hole_type not in _SUPPORTED_HOLE_TYPES:
            continue
        description = _clean_optional_string(raw.get("description"))
        if not description:
            continue
        severity = str(raw.get("severity", "medium")).strip().lower()
        if severity not in _SUPPORTED_SEVERITIES:
            severity = "medium"
        confidence = _clean_confidence(raw.get("confidence"))
        if confidence is None or confidence < _CONFIDENCE_THRESHOLD:
            continue

        chapters_involved = sorted(
            {
                v
                for v in (_clean_int(item) for item in raw.get("chapters_involved", []))
                if v is not None and v in valid_chapters
            }
        )
        events_involved: list[str] = []
        for eid in _clean_string_list(raw.get("events_involved")):
            if eid in valid_event_ids and eid not in events_involved:
                events_involved.append(eid)
        characters_involved: list[str] = []
        for val in _clean_string_list(raw.get("characters_involved")):
            norm = character_lookup.get(val.casefold(), val.strip())
            if norm and norm not in characters_involved:
                characters_involved.append(norm)

        signature = (
            hole_type,
            description.casefold(),
            tuple(chapters_involved),
            tuple(events_involved),
            tuple(characters_involved),
        )
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)

        normalized.append(
            {
                "hole_type": hole_type,
                "severity": severity,
                "description": description[:_MAX_DESCRIPTION_CHARS],
                "chapters_involved": chapters_involved,
                "characters_involved": characters_involved,
                "events_involved": events_involved,
                "confidence": confidence,
            }
        )

    severity_rank = {"high": 0, "medium": 1, "low": 2}
    normalized.sort(
        key=lambda f: (
            severity_rank.get(f["severity"], 3),
            -float(f["confidence"]),
            f["chapters_involved"][:1] or [9999],
            f["description"].casefold(),
        )
    )
    return normalized[:_MAX_FINDINGS]


def _retry_delay(exc: Exception, attempt: int) -> float:
    delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
    match = _RATE_LIMIT_PATTERN.search(str(exc))
    if match:
        try:
            return max(delay, float(match.group(1)) + 0.5)
        except ValueError:
            pass
    return delay


# =============================================================================
# LangGraph tasks
# =============================================================================

@task
async def load_story_state(job_id: str) -> dict[str, Any]:
    t0 = time.perf_counter()
    chapters = await ChapterRepository.get_by_job(job_id)
    timeline = await TimelineRepository.get_by_job(job_id)
    entities = await EntityRepository.get_by_job(job_id)

    if not chapters:
        raise RuntimeError(f"No chapters for job '{job_id}'. Run ingestion first.")
    if not timeline:
        raise RuntimeError(f"No timeline events for job '{job_id}'. Run timeline agent first.")

    chapters_capped = sorted(chapters, key=lambda c: int(c.get("chapter_num", 0)))[
        :_MAX_CHAPTERS_FOR_PROMPT
    ]
    timeline_capped = sorted(timeline, key=lambda e: int(e.get("event_order", 0)))[
        :_MAX_TIMELINE_EVENTS_FOR_PROMPT
    ]
    entities_sorted = sorted(entities, key=lambda e: str(e.get("name", "")).lower())

    logger.info(
        "[PlotHoleAgent] job=%s story state loaded: %d chapters, %d timeline events, %d entities in %.2fs",
        job_id,
        len(chapters_capped),
        len(timeline_capped),
        len(entities_sorted),
        time.perf_counter() - t0,
    )
    return {
        "chapters": chapters_capped,
        "timeline": timeline_capped,
        "entities": entities_sorted,
    }


@task
async def extract_plot_holes_with_retry(
    story_state: dict[str, Any], job_id: str
) -> list[dict[str, Any]]:
    last_exc: Exception | None = None
    payload = _build_prompt_payload(story_state)
    payload_bytes = len(json.dumps(payload, ensure_ascii=False).encode())
    logger.info(
        "[PlotHoleAgent] job=%s sending plot-hole request: payload=%.1fKB",
        job_id, payload_bytes / 1024,
    )

    for attempt in range(1, _MAX_RETRIES + 1):
        t0 = time.perf_counter()
        try:
            raw_findings = await asyncio.to_thread(
                plot_holes_chat_completion, payload, attempt
            )
            normalized = _normalize_findings(story_state, raw_findings)
            logger.info(
                "[PlotHoleAgent] job=%s attempt %d/%d succeeded: %d raw → %d normalized findings in %.2fs",
                job_id, attempt, _MAX_RETRIES,
                len(raw_findings), len(normalized),
                time.perf_counter() - t0,
            )
            return normalized
        except Exception as exc:
            last_exc = exc
            if attempt >= _MAX_RETRIES:
                break
            delay = _retry_delay(exc, attempt)
            logger.warning(
                "[PlotHoleAgent] job=%s attempt %d/%d failed in %.2fs: %r, retry in %.1fs",
                job_id, attempt, _MAX_RETRIES,
                time.perf_counter() - t0, exc, delay,
            )
            await asyncio.sleep(delay)

    raise RuntimeError(
        f"Plot-hole analysis failed after {_MAX_RETRIES} attempts: {repr(last_exc)}"
    ) from last_exc


@task
async def persist_findings(job_id: str, findings: list[dict[str, Any]]) -> int:
    deleted = await PlotHoleRepository.delete_by_job(job_id)
    if deleted:
        logger.info(
            "[PlotHoleAgent] job=%s cleared %d stale plot hole(s)", job_id, deleted
        )

    for index, finding in enumerate(findings, start=1):
        await PlotHoleRepository.create(
            hole_id=f"hole_{index:03d}_{job_id[:8]}",
            job_id=job_id,
            hole_type=finding["hole_type"],
            severity=finding["severity"],
            description=finding["description"],
            chapters_involved=finding["chapters_involved"],
            characters_involved=finding["characters_involved"],
            events_involved=finding["events_involved"],
            confidence=finding["confidence"],
        )

    logger.info(
        "[PlotHoleAgent] job=%s persisted %d finding(s)", job_id, len(findings)
    )
    return len(findings)


# =============================================================================
# Entrypoint
# =============================================================================

@entrypoint()
async def plot_hole_agent(inputs: dict) -> list[dict[str, Any]]:
    """Load story state → extract plot holes → persist findings."""
    job_id: str = inputs["job_id"]

    logger.info("[PlotHoleAgent] job=%s starting", job_id)
    t0 = time.perf_counter()

    await _update_status(
        job_id,
        status="plot_hole_in_progress",
        current_agent="plot_hole_agent",
    )

    try:
        story_state = await load_story_state(job_id)
        findings = await extract_plot_holes_with_retry(story_state, job_id)
        count = await persist_findings(job_id, findings)

        elapsed = time.perf_counter() - t0
        logger.info(
            "[PlotHoleAgent] job=%s COMPLETE: %d finding(s) in %.2fs",
            job_id, count, elapsed,
        )

        await _update_status(
            job_id,
            status="plot_hole_complete",
            current_agent=None,
            completed_agents=["ingestion_agent", "timeline_agent", "plot_hole_agent"],
        )
        return findings
    except Exception as exc:
        logger.exception(
            "[PlotHoleAgent] job=%s FAILED after %.2fs: %s",
            job_id, time.perf_counter() - t0, exc,
        )
        await _update_status(job_id, status="failed", error=str(exc))
        raise


async def _update_status(job_id: str, status: str, **kwargs) -> None:
    logger.debug("[PlotHoleAgent] job=%s status → %s", job_id, status)
    await JobRepository.update_status(job_id, status=status, **kwargs)
    await set_job_status(
        job_id,
        status=status,
        current_agent=kwargs.get("current_agent"),
        completed_agents=kwargs.get("completed_agents", []),
        error=kwargs.get("error"),
    )
