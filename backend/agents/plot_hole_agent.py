from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from typing import Any

from integrations.cosmos.cosmos_repository import (
    delete_plot_holes,
    get_full_job_state,
    update_job_status,
    upsert_plot_hole,
)
from pipeline_status import (
    STATUS_FAILED,
    STATUS_PLOT_HOLE_COMPLETE,
    STATUS_PLOT_HOLE_IN_PROGRESS,
)

logger = logging.getLogger(__name__)

_SUPPORTED_HOLE_TYPES = {
    "timeline_paradox",
    "location_conflict",
    "dead_character_speaks",
    "unresolved_setup",
}
_SUPPORTED_SEVERITIES = {"high", "medium", "low"}
_DEFAULT_CONFIDENCE_THRESHOLD = 0.72
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
_MAX_RELATIVE_TIME_ANCHOR_CHARS = 60
_MAX_ENTITY_NAME_CHARS = 60
_MAX_ENTITY_COUNT = 80
_RATE_LIMIT_DELAY_PATTERN = re.compile(r"try again in ([0-9]+(?:\.[0-9]+)?)s", re.IGNORECASE)


def _get_int_env(name: str, default: int) -> int:
    try:
        value = int(os.getenv(name, str(default)))
        return max(1, value)
    except (TypeError, ValueError):
        return default


def _get_float_env(name: str, default: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
        return value if value > 0 else default
    except (TypeError, ValueError):
        return default


def _plot_hole_model() -> str:
    return os.getenv("PLOT_HOLE_MODEL", "gpt-4o-mini")


def _plot_hole_fallback_model() -> str:
    return os.getenv("PLOT_HOLE_FALLBACK_MODEL", "gpt-4o-mini")


def _plot_hole_timeout_seconds() -> float:
    return _get_float_env("PLOT_HOLE_TIMEOUT_SECONDS", 45.0)


def _plot_hole_max_retries() -> int:
    return _get_int_env("PLOT_HOLE_MAX_RETRIES", 2)


def _plot_hole_max_findings() -> int:
    return _get_int_env("PLOT_HOLE_MAX_FINDINGS", 5)


def _plot_hole_retry_base_delay_seconds() -> float:
    return _get_float_env("PLOT_HOLE_RETRY_BASE_DELAY_SECONDS", 2.0)


def _plot_hole_confidence_threshold() -> float:
    return _get_float_env(
        "PLOT_HOLE_CONFIDENCE_THRESHOLD",
        _DEFAULT_CONFIDENCE_THRESHOLD,
    )


def _is_timeout_error(exc: Exception) -> bool:
    timeout_names = {"APITimeoutError", "ReadTimeout", "TimeoutException", "TimeoutError"}
    current: BaseException | None = exc
    while current is not None:
        if current.__class__.__name__ in timeout_names:
            return True
        message = str(current).lower()
        if "timed out" in message or "timeout" in message:
            return True
        current = current.__cause__ or current.__context__
    return False


class PlotHoleAgent:
    def __init__(self, openai_client, job_id: str):
        self.openai = openai_client
        self.job_id = job_id

    async def run(self) -> str:
        if self.openai is None:
            raise RuntimeError(
                "Azure AI Foundry client is not configured. "
                "Set PROJECT_KEY and OPENAI_ENDPOINT (or PROJECT_ENDPOINT)."
            )

        start = time.perf_counter()
        logger.info("[PlotHoleAgent] job=%s starting plot-hole analysis", self.job_id)
        update_job_status(
            self.job_id,
            status=STATUS_PLOT_HOLE_IN_PROGRESS,
            current_agent="plot_hole_agent",
        )

        try:
            story_state = self._load_story_state()
            findings = await self._extract_plot_holes_with_retry(story_state)
            persisted_count = self._persist_findings(findings)
            update_job_status(
                self.job_id,
                status=STATUS_PLOT_HOLE_COMPLETE,
                current_agent=None,
                completed_agents=self._merge_completed_agents(story_state, "plot_hole_agent"),
                error=None,
            )
            logger.info(
                "[PlotHoleAgent] job=%s finished in %.2fs with %d plot hole(s)",
                self.job_id,
                time.perf_counter() - start,
                persisted_count,
            )
            return self.job_id
        except Exception as exc:
            logger.exception("[PlotHoleAgent] job=%s plot-hole analysis failed", self.job_id)
            update_job_status(
                self.job_id,
                status=STATUS_FAILED,
                current_agent="plot_hole_agent",
                error=str(exc),
            )
            raise

    def _load_story_state(self) -> dict[str, Any]:
        full_state = get_full_job_state(self.job_id)
        chapters = full_state.get("chapters", [])
        timeline = full_state.get("timeline", [])
        if not chapters:
            raise RuntimeError(
                f"No chapters found for job '{self.job_id}'. Plot-hole analysis requires ingestion output."
            )
        if not timeline:
            raise RuntimeError(
                f"No timeline events found for job '{self.job_id}'. Plot-hole analysis requires timeline output."
            )

        full_state["chapters"] = sorted(
            chapters,
            key=lambda chapter: int(chapter.get("chapter_num", 0)),
        )[:_MAX_CHAPTERS_FOR_PROMPT]
        full_state["timeline"] = sorted(
            timeline,
            key=lambda event: int(event.get("order", 0)),
        )[:_MAX_TIMELINE_EVENTS_FOR_PROMPT]
        full_state["entities"] = sorted(
            full_state.get("entities", []),
            key=lambda entity: str(entity.get("name", "")).lower(),
        )
        return full_state

    async def _extract_plot_holes_with_retry(
        self,
        story_state: dict[str, Any],
    ) -> list[dict[str, Any]]:
        last_exc: Exception | None = None
        retry_count = _plot_hole_max_retries()
        for attempt in range(1, retry_count + 1):
            model_name = self._model_for_attempt(attempt)
            try:
                return await self._request_plot_holes(story_state, attempt, model_name)
            except Exception as exc:
                last_exc = exc
                if attempt >= retry_count:
                    break

                delay = self._retry_delay_seconds(exc, attempt)
                if _is_timeout_error(exc):
                    logger.warning(
                        "[PlotHoleAgent] job=%s attempt %d/%d timed out on model=%s; retrying in %.2fs",
                        self.job_id,
                        attempt,
                        retry_count,
                        model_name,
                        delay,
                    )
                elif self._is_rate_limit_error(exc):
                    logger.warning(
                        "[PlotHoleAgent] job=%s attempt %d/%d hit rate limits on model=%s; retrying in %.2fs",
                        self.job_id,
                        attempt,
                        retry_count,
                        model_name,
                        delay,
                    )
                else:
                    logger.warning(
                        "[PlotHoleAgent] job=%s attempt %d/%d failed on model=%s; retrying in %.2fs: %r",
                        self.job_id,
                        attempt,
                        retry_count,
                        model_name,
                        delay,
                        exc,
                    )
                await asyncio.sleep(delay)
        raise RuntimeError(
            f"Plot-hole analysis failed after {retry_count} attempt(s): {repr(last_exc)}"
        ) from last_exc

    async def _request_plot_holes(
        self,
        story_state: dict[str, Any],
        attempt: int,
        model_name: str,
    ) -> list[dict[str, Any]]:
        payload = self._build_prompt_payload(story_state)
        payload_bytes = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        logger.info(
            "[PlotHoleAgent] job=%s sending plot-hole request to model=%s attempt=%d/%d payload_bytes=%d",
            self.job_id,
            model_name,
            attempt,
            _plot_hole_max_retries(),
            payload_bytes,
        )

        prompt = (
            "You are a conservative fiction continuity analyst.\n"
            "Review the structured story state and return only high-signal plot holes that are directly supported by the provided evidence.\n\n"
            "Allowed hole types:\n"
            "- timeline_paradox: chronology or causality contradicts itself.\n"
            "- location_conflict: the same person or event is placed in incompatible locations at the same time.\n"
            "- dead_character_speaks: a character appears active after a supported death/absence contradiction.\n"
            "- unresolved_setup: the story strongly sets up a concrete thread that remains unresolved by the end of the provided material.\n\n"
            "Rules:\n"
            "1) Be conservative. Return fewer findings rather than speculative ones.\n"
            "2) Return zero findings if the evidence is ambiguous.\n"
            "3) Use only the provided chapters, timeline events, and entities.\n"
            "4) Keep descriptions concise and evidence-based. Mention the contradiction or unresolved setup explicitly.\n"
            "5) `confidence` must reflect how explicit the support is, from 0.0 to 1.0.\n"
            "6) Only use event ids and chapter numbers that exist in the input.\n\n"
            f"Story state:\n{json.dumps(payload, ensure_ascii=False)}"
        )

        response = await self.openai.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            response_format=self._response_format(),
            timeout=_plot_hole_timeout_seconds(),
        )
        parsed = json.loads(response.choices[0].message.content)
        findings = parsed.get("findings", [])
        if not isinstance(findings, list):
            raise RuntimeError("Plot-hole output invalid: 'findings' is not a list")
        return self._normalize_findings(story_state, findings)

    def _build_prompt_payload(self, story_state: dict[str, Any]) -> dict[str, Any]:
        chapters = story_state.get("chapters", [])
        timeline = story_state.get("timeline", [])
        entities = self._select_entities_for_prompt(story_state.get("entities", []))

        return {
            "story_end": self._build_story_end_payload(story_state),
            "chapters": [self._build_chapter_payload(chapter) for chapter in chapters],
            "timeline_events": [self._build_timeline_payload(event) for event in timeline],
            "entities": [self._build_entity_payload(entity) for entity in entities],
        }

    def _select_entities_for_prompt(
        self,
        entities: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        prioritized = sorted(
            entities,
            key=lambda entity: (
                0
                if str(entity.get("entity_type", "")).strip() == "character"
                else 1,
                str(entity.get("name", "")).lower(),
            ),
        )
        return prioritized[:_MAX_ENTITY_COUNT]

    def _build_story_end_payload(self, story_state: dict[str, Any]) -> dict[str, Any]:
        chapters = story_state.get("chapters", [])
        timeline = story_state.get("timeline", [])
        final_chapter_num = 0
        if chapters:
            final_chapter_num = max(
                int(chapter.get("chapter_num", 0) or 0) for chapter in chapters
            )
        final_event_id = None
        if timeline:
            final_event_id = str(timeline[-1].get("event_id", "")).strip() or None

        return {
            "final_chapter_num": final_chapter_num,
            "final_event_id": final_event_id,
            "timeline_event_count": len(timeline),
        }

    def _build_chapter_payload(self, chapter: dict[str, Any]) -> dict[str, Any]:
        summary_items = self._clean_string_list(chapter.get("summary"), limit=_MAX_SUMMARY_ITEMS)
        summary_text = self._trim_text(" ".join(summary_items), _MAX_SUMMARY_TEXT_CHARS)
        return {
            "chapter_num": int(chapter.get("chapter_num", 0)),
            "chapter_title": self._trim_text(
                str(chapter.get("chapter_title", "")).strip(),
                _MAX_LOCATION_CHARS,
            ),
            "summary_text": summary_text,
            "key_events": self._clean_string_list(
                [
                    self._trim_text(value, _MAX_EVENT_DESCRIPTION_CHARS)
                    for value in chapter.get("key_events", [])
                ],
                limit=_MAX_KEY_EVENTS,
            ),
            "characters": self._clean_string_list(
                chapter.get("characters"),
                limit=_MAX_CHARACTERS,
            ),
            "temporal_markers": self._clean_string_list(
                chapter.get("temporal_markers"),
                limit=_MAX_TEMPORAL_MARKERS,
            ),
        }

    def _build_timeline_payload(self, event: dict[str, Any]) -> dict[str, Any]:
        return {
            "event_id": str(event.get("event_id", "")).strip(),
            "order": int(event.get("order", 0) or 0),
            "chapter_num": int(event.get("chapter_num", 0) or 0),
            "description": self._trim_text(
                str(event.get("description", "")).strip(),
                _MAX_EVENT_DESCRIPTION_CHARS,
            ),
            "characters_present": self._clean_string_list(
                event.get("characters_present"),
                limit=_MAX_TIMELINE_CHARACTERS,
            ),
            "location": self._trim_optional_text(
                event.get("location"),
                _MAX_LOCATION_CHARS,
            ),
            "causes": self._clean_string_list(event.get("causes"), limit=2),
            "caused_by": self._clean_string_list(event.get("caused_by"), limit=2),
            "time_reference": self._trim_optional_text(
                event.get("time_reference"),
                _MAX_TIME_REFERENCE_CHARS,
            ),
            "inferred_date": self._clean_optional_string(event.get("inferred_date")),
            "inferred_year": self._clean_int(event.get("inferred_year")),
            "relative_time_anchor": self._trim_optional_text(
                event.get("relative_time_anchor"),
                _MAX_RELATIVE_TIME_ANCHOR_CHARS,
            ),
            "confidence": self._clean_confidence(event.get("confidence")),
        }

    def _build_entity_payload(self, entity: dict[str, Any]) -> dict[str, Any]:
        return {
            "entity_id": self._trim_text(
                str(entity.get("entity_id", "")).strip(),
                _MAX_ENTITY_NAME_CHARS,
            ),
            "name": self._trim_text(
                str(entity.get("name", "")).strip(),
                _MAX_ENTITY_NAME_CHARS,
            ),
            "entity_type": str(entity.get("entity_type", "")).strip(),
            "appears_in_chapters": sorted(
                {
                    int(value)
                    for value in entity.get("appears_in_chapters", [])
                    if isinstance(value, int)
                }
            )[:_MAX_ENTITY_CHAPTERS],
            "aliases": self._clean_string_list(
                [
                    self._trim_text(value, _MAX_ENTITY_NAME_CHARS)
                    for value in entity.get("aliases", [])
                ],
                limit=_MAX_ENTITY_ALIASES,
            ),
            "role": self._clean_optional_string(entity.get("role")),
        }

    def _normalize_findings(
        self,
        story_state: dict[str, Any],
        raw_findings: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        valid_event_ids = {
            str(event.get("event_id")).strip()
            for event in story_state.get("timeline", [])
            if isinstance(event.get("event_id"), str) and str(event.get("event_id")).strip()
        }
        valid_chapters = {
            int(chapter.get("chapter_num", 0))
            for chapter in story_state.get("chapters", [])
            if isinstance(chapter.get("chapter_num"), int)
            or str(chapter.get("chapter_num", "")).isdigit()
        }
        character_lookup = self._build_character_lookup(story_state)

        normalized: list[dict[str, Any]] = []
        seen_signatures: set[tuple[Any, ...]] = set()
        for raw_finding in raw_findings:
            if not isinstance(raw_finding, dict):
                continue

            hole_type = str(raw_finding.get("hole_type", "")).strip().lower()
            if hole_type not in _SUPPORTED_HOLE_TYPES:
                continue

            description = self._clean_optional_string(raw_finding.get("description"))
            if description is None:
                continue

            severity = str(raw_finding.get("severity", "medium")).strip().lower()
            if severity not in _SUPPORTED_SEVERITIES:
                severity = "medium"

            confidence = self._clean_confidence(raw_finding.get("confidence"))
            if confidence is None or confidence < _plot_hole_confidence_threshold():
                continue

            chapters_involved = sorted(
                {
                    value
                    for value in (
                        self._clean_int(item)
                        for item in raw_finding.get("chapters_involved", [])
                    )
                    if value is not None and value in valid_chapters
                }
            )

            events_involved = []
            for event_id in self._clean_string_list(raw_finding.get("events_involved")):
                if event_id in valid_event_ids and event_id not in events_involved:
                    events_involved.append(event_id)

            characters_involved = []
            for value in self._clean_string_list(raw_finding.get("characters_involved")):
                normalized_character = character_lookup.get(value.casefold(), value.strip())
                if normalized_character and normalized_character not in characters_involved:
                    characters_involved.append(normalized_character)

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
            key=lambda finding: (
                severity_rank.get(finding["severity"], 3),
                -float(finding["confidence"]),
                finding["chapters_involved"][:1] or [9999],
                finding["description"].casefold(),
            )
        )
        return normalized[: _plot_hole_max_findings()]

    def _model_for_attempt(self, attempt: int) -> str:
        if attempt <= 1:
            return _plot_hole_model()
        fallback_model = _plot_hole_fallback_model().strip()
        return fallback_model or _plot_hole_model()

    def _retry_delay_seconds(self, exc: Exception, attempt: int) -> float:
        delay = _plot_hole_retry_base_delay_seconds() * (2 ** (attempt - 1))
        message = str(exc)
        match = _RATE_LIMIT_DELAY_PATTERN.search(message)
        if match is not None:
            try:
                parsed_delay = float(match.group(1)) + 0.5
                return max(delay, parsed_delay)
            except ValueError:
                return delay
        return delay

    def _is_rate_limit_error(self, exc: Exception) -> bool:
        current: BaseException | None = exc
        while current is not None:
            if current.__class__.__name__ == "RateLimitError":
                return True
            message = str(current).lower()
            if "rate limit" in message or "rate_limit_exceeded" in message:
                return True
            current = current.__cause__ or current.__context__
        return False

    def _persist_findings(self, findings: list[dict[str, Any]]) -> int:
        deleted = delete_plot_holes(self.job_id)
        if deleted:
            logger.info(
                "[PlotHoleAgent] job=%s cleared %d stale plot hole(s)",
                self.job_id,
                deleted,
            )

        for index, finding in enumerate(findings, start=1):
            upsert_plot_hole(
                job_id=self.job_id,
                hole_id=f"hole_{index:03d}",
                hole_type=finding["hole_type"],
                severity=finding["severity"],
                description=finding["description"],
                chapters_involved=finding["chapters_involved"],
                characters_involved=finding["characters_involved"],
                events_involved=finding["events_involved"],
            )
        return len(findings)

    def _merge_completed_agents(
        self,
        story_state: dict[str, Any],
        new_agent: str,
    ) -> list[str]:
        existing = {
            str(agent).strip()
            for agent in story_state.get("job", {}).get("completed_agents", [])
            if isinstance(agent, str) and agent.strip()
        }
        existing.update({"ingestion_agent", "timeline_agent"})
        if new_agent:
            existing.add(new_agent)
        return sorted(existing)

    def _build_character_lookup(self, story_state: dict[str, Any]) -> dict[str, str]:
        lookup: dict[str, str] = {}
        for entity in story_state.get("entities", []):
            name = self._clean_optional_string(entity.get("name"))
            if not name:
                continue
            lookup[name.casefold()] = name
            for alias in self._clean_string_list(entity.get("aliases")):
                lookup[alias.casefold()] = name

        for chapter in story_state.get("chapters", []):
            for character in self._clean_string_list(chapter.get("characters")):
                lookup.setdefault(character.casefold(), character)

        for event in story_state.get("timeline", []):
            for character in self._clean_string_list(event.get("characters_present")):
                lookup.setdefault(character.casefold(), character)
        return lookup

    def _response_format(self) -> dict[str, Any]:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "plot_hole_analysis",
                "strict": True,
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "findings": {
                            "type": "array",
                            "maxItems": _plot_hole_max_findings(),
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "hole_type": {"type": "string"},
                                    "severity": {"type": "string"},
                                    "description": {"type": "string"},
                                    "chapters_involved": {
                                        "type": "array",
                                        "items": {"type": "integer"},
                                    },
                                    "characters_involved": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "events_involved": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "confidence": {
                                        "anyOf": [{"type": "number"}, {"type": "null"}]
                                    },
                                },
                                "required": [
                                    "hole_type",
                                    "severity",
                                    "description",
                                    "chapters_involved",
                                    "characters_involved",
                                    "events_involved",
                                    "confidence",
                                ],
                            },
                        }
                    },
                    "required": ["findings"],
                },
            },
        }

    def _clean_string_list(
        self,
        values: Any,
        *,
        limit: int | None = None,
    ) -> list[str]:
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

    def _clean_optional_string(self, value: Any) -> str | None:
        if not isinstance(value, (str, int, float)):
            return None
        normalized = str(value).strip()
        return normalized or None

    def _trim_text(self, value: str, max_chars: int) -> str:
        if len(value) <= max_chars:
            return value
        if max_chars <= 3:
            return value[:max_chars]
        return value[: max_chars - 3].rstrip() + "..."

    def _trim_optional_text(self, value: Any, max_chars: int) -> str | None:
        normalized = self._clean_optional_string(value)
        if normalized is None:
            return None
        return self._trim_text(normalized, max_chars)

    def _clean_int(self, value: Any) -> int | None:
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _clean_confidence(self, value: Any) -> float | None:
        try:
            confidence = float(value)
        except (TypeError, ValueError):
            return None
        if confidence < 0.0:
            return 0.0
        if confidence > 1.0:
            return 1.0
        return confidence
