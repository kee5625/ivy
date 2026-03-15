from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from typing import Any

from integrations.cosmos.cosmos_repository import (
    get_chapters,
    get_full_job_state,
    update_job_status,
    upsert_timeline_event,
)
from pipeline_status import (
    STATUS_FAILED,
    STATUS_TIMELINE_COMPLETE,
    STATUS_TIMELINE_IN_PROGRESS,
)

logger = logging.getLogger(__name__)

_MAX_TIMELINE_EVENTS = 120
_MAX_CHAPTERS_FOR_PROMPT = 200
_MAX_CHAPTER_SUMMARY_CHARS = 700
_MAX_KEY_EVENTS_PER_CHAPTER = 4
_MAX_CHARACTERS_PER_CHAPTER = 8
_MAX_TEMPORAL_MARKERS_PER_CHAPTER = 4
_LOCAL_RETRY_ATTEMPTS = 2
_MERGE_RETRY_ATTEMPTS = 2


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


def _timeline_chapter_concurrency() -> int:
    return _get_int_env("TIMELINE_CHAPTER_CONCURRENCY", 6)


def _timeline_max_events_per_chapter() -> int:
    return _get_int_env("TIMELINE_MAX_EVENTS_PER_CHAPTER", 4)


def _timeline_local_model() -> str:
    return os.getenv("TIMELINE_LOCAL_MODEL", "gpt-4o-mini")


def _timeline_merge_model() -> str:
    return os.getenv("TIMELINE_MERGE_MODEL", "gpt-4.1")


def _timeline_local_timeout_seconds() -> float:
    return _get_float_env("TIMELINE_LOCAL_TIMEOUT_SECONDS", 25.0)


def _timeline_merge_timeout_seconds() -> float:
    return _get_float_env("TIMELINE_MERGE_TIMEOUT_SECONDS", 45.0)


class TimelineAgent:
    """
    Builds a globally ordered timeline from ingested chapter data.

    Inputs:
      - chapters from Cosmos (`type == "chapter"`), including:
        - chapter_num
        - chapter_title
        - summary
        - key_events
        - characters
        - temporal_markers (if available)
    Outputs:
      - timeline_event documents in Cosmos (`type == "timeline_event"`),
        including chronology and lightweight temporal metadata.
    """

    def __init__(self, openai_client, job_id: str):
        self.openai = openai_client
        self.job_id = job_id
        self._local_semaphore = asyncio.Semaphore(_timeline_chapter_concurrency())

    async def run(self) -> str:
        if self.openai is None:
            raise RuntimeError(
                "OpenAI client is not configured. Set OPENAI_API_KEY in your .env file."
            )

        total_start = time.perf_counter()
        logger.info("[TimelineAgent] job=%s starting timeline pipeline", self.job_id)

        update_job_status(
            self.job_id,
            status=STATUS_TIMELINE_IN_PROGRESS,
            current_agent="timeline_agent",
        )

        try:
            chapters = self._load_chapters()
            if not chapters:
                raise RuntimeError(
                    f"No chapters found for job '{self.job_id}'. "
                    "Ingestion must complete before timeline generation."
                )

            events = await self._generate_timeline_events(chapters)
            if not events:
                raise RuntimeError("Timeline generation produced no events.")

            persisted_count = self._persist_events(events)
            logger.info(
                "[TimelineAgent] job=%s wrote %d timeline events",
                self.job_id,
                persisted_count,
            )

            update_job_status(
                self.job_id,
                status=STATUS_TIMELINE_COMPLETE,
                current_agent="plot_hole_agent",
                completed_agents=self._merge_completed_agents("timeline_agent"),
            )
            logger.info(
                "[TimelineAgent] job=%s finished timeline pipeline in %.2fs; next_agent=plot_hole_agent",
                self.job_id,
                time.perf_counter() - total_start,
            )
            return self.job_id
        except Exception as exc:
            logger.exception("[TimelineAgent] job=%s timeline failed", self.job_id)
            update_job_status(self.job_id, status=STATUS_FAILED, error=str(exc))
            raise

    def _load_chapters(self) -> list[dict[str, Any]]:
        logger.info("[TimelineAgent] job=%s loading chapters from Cosmos", self.job_id)
        chapters = get_chapters(self.job_id)
        original_count = len(chapters)
        chapters = sorted(chapters, key=lambda c: int(c.get("chapter_num", 0)))
        if len(chapters) > _MAX_CHAPTERS_FOR_PROMPT:
            chapters = chapters[:_MAX_CHAPTERS_FOR_PROMPT]
            logger.warning(
                "[TimelineAgent] job=%s chapter list truncated from %d to %d for prompt budget",
                self.job_id,
                original_count,
                len(chapters),
            )

        logger.info(
            "[TimelineAgent] job=%s loaded %d chapter(s) for timeline generation",
            self.job_id,
            len(chapters),
        )
        return chapters

    async def _generate_timeline_events(
        self,
        chapters: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        local_events = await self._extract_local_timelines(chapters)
        if not local_events:
            raise RuntimeError("Timeline local extraction produced no events.")

        logger.info(
            "[TimelineAgent] job=%s moving to merge pass with %d local event(s)",
            self.job_id,
            len(local_events),
        )
        merged_events = await self._merge_local_timelines(local_events)
        logger.info(
            "[TimelineAgent] job=%s merge pass produced %d merged event(s)",
            self.job_id,
            len(merged_events),
        )
        return merged_events[:_MAX_TIMELINE_EVENTS]

    async def _extract_local_timelines(
        self,
        chapters: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        logger.info(
            "[TimelineAgent] job=%s starting local timeline extraction across %d chapter(s) with concurrency=%d",
            self.job_id,
            len(chapters),
            _timeline_chapter_concurrency(),
        )
        tasks = [self._extract_local_timeline_for_chapter(chapter) for chapter in chapters]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_events: list[dict[str, Any]] = []
        failures = 0
        for chapter, result in zip(chapters, results):
            if isinstance(result, Exception):
                failures += 1
                logger.error(
                    "[TimelineAgent] job=%s chapter=%s local timeline failed: %r",
                    self.job_id,
                    chapter.get("chapter_num"),
                    result,
                )
                continue
            all_events.extend(result)

        if failures == len(chapters):
            raise RuntimeError(
                f"Timeline local extraction failed for all {failures} chapter(s)."
            )
        if failures:
            logger.warning(
                "[TimelineAgent] job=%s local timeline failed for %d/%d chapter(s); continuing with partial results",
                self.job_id,
                failures,
                len(chapters),
            )

        logger.info(
            "[TimelineAgent] job=%s completed local extraction: %d chapter(s) succeeded, %d local event(s) produced",
            self.job_id,
            len(chapters) - failures,
            len(all_events),
        )
        return all_events

    async def _extract_local_timeline_for_chapter(
        self,
        chapter: dict[str, Any],
    ) -> list[dict[str, Any]]:
        async with self._local_semaphore:
            return await self._extract_local_timeline_for_chapter_with_retry(chapter)

    async def _extract_local_timeline_for_chapter_with_retry(
        self,
        chapter: dict[str, Any],
    ) -> list[dict[str, Any]]:
        last_exc: Exception | None = None
        chapter_num = int(chapter.get("chapter_num", 0))
        for attempt in range(1, _LOCAL_RETRY_ATTEMPTS + 1):
            try:
                return await self._request_local_timeline(chapter, attempt)
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "[TimelineAgent] job=%s chapter=%d local attempt %d/%d failed: %r",
                    self.job_id,
                    chapter_num,
                    attempt,
                    _LOCAL_RETRY_ATTEMPTS,
                    exc,
                )

        raise RuntimeError(
            f"Chapter {chapter_num} local timeline failed after {_LOCAL_RETRY_ATTEMPTS} attempts: {repr(last_exc)}"
        ) from last_exc

    async def _request_local_timeline(
        self,
        chapter: dict[str, Any],
        attempt: int,
    ) -> list[dict[str, Any]]:
        chapter_num = int(chapter.get("chapter_num", 0))
        payload = self._build_local_chapter_payload(chapter)
        payload_bytes = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        model_name = _timeline_local_model()
        start = time.perf_counter()

        logger.info(
            "[TimelineAgent] job=%s chapter=%d sending local timeline request to model=%s attempt=%d/%d payload_bytes=%d",
            self.job_id,
            chapter_num,
            model_name,
            attempt,
            _LOCAL_RETRY_ATTEMPTS,
            payload_bytes,
        )

        prompt = (
            "You are a narrative analyst working on one chapter only.\n"
            "Using only the provided chapter data, produce a small ordered list of the most important events in this chapter.\n\n"
            f"Requirements:\n"
            f"1) Return at most {_timeline_max_events_per_chapter()} events.\n"
            "2) Keep each event short, concrete, and chapter-local.\n"
            "3) Preserve order within the chapter only.\n"
            "4) Do not invent events unsupported by the chapter data.\n"
            "5) `characters_present` should contain names/slugs only.\n"
            "6) `time_reference` should be null unless the chapter data provides one.\n"
            "7) `confidence` must be between 0.0 and 1.0.\n\n"
            f"Chapter data:\n{json.dumps(payload, ensure_ascii=False)}"
        )

        response = await self.openai.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            response_format=self._local_response_format(),
            timeout=_timeline_local_timeout_seconds(),
        )
        elapsed = time.perf_counter() - start
        raw_content = response.choices[0].message.content
        parsed = json.loads(raw_content)
        raw_events = parsed.get("events", [])
        if not isinstance(raw_events, list):
            raise RuntimeError("Local timeline output invalid: 'events' is not a list")

        normalized = self._normalize_local_events(chapter, raw_events)
        logger.info(
            "[TimelineAgent] job=%s chapter=%d local timeline completed in %.2fs with %d event(s)",
            self.job_id,
            chapter_num,
            elapsed,
            len(normalized),
        )
        return normalized

    async def _merge_local_timelines(
        self,
        local_events: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        payload = self._build_merge_payload(local_events)
        payload_bytes = len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        logger.info(
            "[TimelineAgent] job=%s preparing merge request with %d local event(s), %d payload bytes",
            self.job_id,
            len(local_events),
            payload_bytes,
        )

        last_exc: Exception | None = None
        for attempt in range(1, _MERGE_RETRY_ATTEMPTS + 1):
            try:
                model_name = _timeline_merge_model()
                start = time.perf_counter()
                logger.info(
                    "[TimelineAgent] job=%s sending merge request to model=%s attempt=%d/%d",
                    self.job_id,
                    model_name,
                    attempt,
                    _MERGE_RETRY_ATTEMPTS,
                )
                prompt = (
                    "You are a narrative timeline analyst.\n"
                    "Merge chapter-local events into one globally ordered story timeline.\n\n"
                    "Requirements:\n"
                    "1) Every `source_event_id` from the input must appear exactly once in the output.\n"
                    "2) Produce a single globally ordered list across all chapters.\n"
                    "3) Preserve narrative causality when setting `causes` and `caused_by`.\n"
                    "4) Use `source_event_id` values from the input when referencing related events.\n"
                    "5) `relative_time_anchor_event_id` must be null or one input `source_event_id`.\n"
                    "6) Keep events concise and do not invent unsupported specifics.\n"
                    "7) `confidence` must stay between 0.0 and 1.0.\n\n"
                    f"Input local events:\n{json.dumps(payload, ensure_ascii=False)}"
                )

                response = await self.openai.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    response_format=self._merge_response_format(),
                    timeout=_timeline_merge_timeout_seconds(),
                )
                elapsed = time.perf_counter() - start
                logger.info(
                    "[TimelineAgent] job=%s merge request completed in %.2fs",
                    self.job_id,
                    elapsed,
                )

                raw_content = response.choices[0].message.content
                parsed = json.loads(raw_content)
                raw_events = parsed.get("events", [])
                if not isinstance(raw_events, list):
                    raise RuntimeError("Merge output invalid: 'events' is not a list")

                source_event_ids = {event["source_event_id"] for event in local_events}
                return self._normalize_merged_events(raw_events, source_event_ids)
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "[TimelineAgent] job=%s merge attempt %d/%d failed: %r",
                    self.job_id,
                    attempt,
                    _MERGE_RETRY_ATTEMPTS,
                    exc,
                )

        raise RuntimeError(
            f"Timeline merge failed after {_MERGE_RETRY_ATTEMPTS} attempts: {repr(last_exc)}"
        ) from last_exc

    def _build_local_chapter_payload(self, chapter: dict[str, Any]) -> dict[str, Any]:
        summary = chapter.get("summary") or []
        key_events = chapter.get("key_events") or []
        temporal_markers = chapter.get("temporal_markers") or []
        characters = chapter.get("characters") or []

        summary_text = " ".join(
            s.strip() for s in summary if isinstance(s, str) and s.strip()
        )[:_MAX_CHAPTER_SUMMARY_CHARS]
        key_event_values = [
            e.strip() for e in key_events if isinstance(e, str) and e.strip()
        ][:_MAX_KEY_EVENTS_PER_CHAPTER]
        character_values = [
            c.strip() for c in characters if isinstance(c, str) and c.strip()
        ][:_MAX_CHARACTERS_PER_CHAPTER]
        temporal_marker_values = [
            t.strip() for t in temporal_markers if isinstance(t, str) and t.strip()
        ][:_MAX_TEMPORAL_MARKERS_PER_CHAPTER]

        return {
            "chapter_num": int(chapter.get("chapter_num", 0)),
            "chapter_title": str(chapter.get("chapter_title", "")).strip(),
            "summary_text": summary_text,
            "key_events": key_event_values,
            "characters": character_values,
            "temporal_markers": temporal_marker_values,
        }

    def _build_llm_input(self, chapters: list[dict[str, Any]]) -> list[dict[str, Any]]:
        compact = [self._build_local_chapter_payload(chapter) for chapter in chapters]
        logger.info(
            "[TimelineAgent] job=%s built compact chapter payload with %d chapter(s)",
            self.job_id,
            len(compact),
        )
        return compact

    def _normalize_local_events(
        self,
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
                if confidence_value < 0.0:
                    confidence_value = 0.0
                elif confidence_value > 1.0:
                    confidence_value = 1.0
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
                        str(value).strip()
                        for value in characters_present
                        if isinstance(value, (str, int, float)) and str(value).strip()
                    ],
                    "location": location,
                    "time_reference": time_reference,
                    "confidence": confidence_value,
                }
            )

        return normalized[:_timeline_max_events_per_chapter()]

    def _build_merge_payload(self, local_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
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

        payload = [grouped[key] for key in sorted(grouped)]
        logger.info(
            "[TimelineAgent] job=%s built merge payload spanning %d chapter(s)",
            self.job_id,
            len(payload),
        )
        return payload

    def _normalize_merged_events(
        self,
        raw_events: list[dict[str, Any]],
        source_event_ids: set[str],
    ) -> list[dict[str, Any]]:
        prepared: list[dict[str, Any]] = []
        seen_source_ids: set[str] = set()
        for raw in raw_events:
            source_event_id = raw.get("source_event_id")
            if not isinstance(source_event_id, str) or source_event_id not in source_event_ids:
                continue
            if source_event_id in seen_source_ids:
                continue
            seen_source_ids.add(source_event_id)

            relative_anchor_event_id = raw.get("relative_time_anchor_event_id")
            if (
                not isinstance(relative_anchor_event_id, str)
                or relative_anchor_event_id not in source_event_ids
            ):
                relative_anchor = None
            else:
                relative_anchor = f"after {relative_anchor_event_id}"

            prepared.append(
                {
                    "event_id": source_event_id,
                    "description": raw.get("description"),
                    "chapter_num": raw.get("chapter_num"),
                    "chapter_title": raw.get("chapter_title"),
                    "order": raw.get("order"),
                    "characters_present": raw.get("characters_present"),
                    "location": raw.get("location"),
                    "causes": [
                        value
                        for value in raw.get("causes", [])
                        if isinstance(value, str) and value in source_event_ids
                    ],
                    "caused_by": [
                        value
                        for value in raw.get("caused_by", [])
                        if isinstance(value, str) and value in source_event_ids
                    ],
                    "time_reference": raw.get("time_reference"),
                    "inferred_date": raw.get("inferred_date"),
                    "inferred_year": raw.get("inferred_year"),
                    "relative_time_anchor": relative_anchor,
                    "confidence": raw.get("confidence"),
                }
            )

        missing_source_ids = source_event_ids - seen_source_ids
        if missing_source_ids:
            raise RuntimeError(
                "Merge output omitted source events: "
                + ", ".join(sorted(missing_source_ids))
            )

        normalized = self._normalize_events(prepared)
        logger.info(
            "[TimelineAgent] job=%s normalized %d merged timeline event(s) from %d raw merge event(s)",
            self.job_id,
            len(normalized),
            len(raw_events),
        )
        return normalized

    def _normalize_events(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        skipped_events = 0
        for i, raw in enumerate(events, start=1):
            event_id = raw.get("event_id")
            if not isinstance(event_id, str) or not event_id.strip():
                event_id = f"evt_{i:03d}"

            description = raw.get("description")
            if not isinstance(description, str) or not description.strip():
                skipped_events += 1
                continue

            chapter_num = raw.get("chapter_num")
            try:
                chapter_num = int(chapter_num)
            except Exception:
                chapter_num = 0

            order = raw.get("order")
            try:
                order = int(order)
            except Exception:
                order = i

            chapter_title = raw.get("chapter_title")
            if not isinstance(chapter_title, str):
                chapter_title = ""

            characters_present = raw.get("characters_present")
            if not isinstance(characters_present, list):
                characters_present = []
            characters_present = [
                str(v).strip()
                for v in characters_present
                if isinstance(v, (str, int, float)) and str(v).strip()
            ]

            location = raw.get("location")
            if not isinstance(location, str) or not location.strip():
                location = None

            causes = raw.get("causes")
            caused_by = raw.get("caused_by")
            if not isinstance(causes, list):
                causes = []
            if not isinstance(caused_by, list):
                caused_by = []
            causes = [str(v).strip() for v in causes if isinstance(v, str) and v.strip()]
            caused_by = [
                str(v).strip() for v in caused_by if isinstance(v, str) and v.strip()
            ]

            time_reference = raw.get("time_reference")
            if not isinstance(time_reference, str) or not time_reference.strip():
                time_reference = None

            inferred_date = raw.get("inferred_date")
            if not isinstance(inferred_date, str) or not inferred_date.strip():
                inferred_date = None

            inferred_year = raw.get("inferred_year")
            if inferred_year is None:
                year_value: int | None = None
            else:
                try:
                    year_int = int(inferred_year)
                    year_value = year_int if 1 <= year_int <= 3000 else None
                except Exception:
                    year_value = None

            relative_time_anchor = raw.get("relative_time_anchor")
            if (
                not isinstance(relative_time_anchor, str)
                or not relative_time_anchor.strip()
            ):
                relative_time_anchor = None

            confidence = raw.get("confidence")
            confidence_value: float | None
            try:
                confidence_value = float(confidence)
                if confidence_value < 0.0:
                    confidence_value = 0.0
                elif confidence_value > 1.0:
                    confidence_value = 1.0
            except Exception:
                confidence_value = None

            normalized.append(
                {
                    "_source_event_id": event_id,
                    "event_id": event_id,
                    "description": description.strip(),
                    "chapter_num": chapter_num,
                    "chapter_title": chapter_title.strip(),
                    "order": order,
                    "characters_present": characters_present,
                    "location": location,
                    "causes": causes,
                    "caused_by": caused_by,
                    "time_reference": time_reference,
                    "inferred_date": inferred_date,
                    "inferred_year": year_value,
                    "relative_time_anchor": relative_time_anchor,
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
            item["causes"] = self._remap_event_references(
                item.get("causes", []),
                event_id_mapping,
                final_event_ids,
            )
            item["caused_by"] = self._remap_event_references(
                item.get("caused_by", []),
                event_id_mapping,
                final_event_ids,
            )
            item["relative_time_anchor"] = self._remap_relative_time_anchor(
                item.get("relative_time_anchor"),
                event_id_mapping,
            )
            item.pop("_source_event_id", None)

        if skipped_events:
            logger.warning(
                "[TimelineAgent] job=%s skipped %d malformed timeline event(s) with empty descriptions",
                self.job_id,
                skipped_events,
            )
        return normalized

    def _remap_event_references(
        self,
        references: list[str],
        event_id_mapping: dict[str, str],
        final_event_ids: set[str],
    ) -> list[str]:
        remapped: list[str] = []
        seen: set[str] = set()
        for reference in references:
            if reference in event_id_mapping:
                candidate = event_id_mapping[reference]
            elif reference in final_event_ids:
                candidate = reference
            else:
                continue

            if candidate not in seen:
                seen.add(candidate)
                remapped.append(candidate)

        return remapped

    def _remap_relative_time_anchor(
        self,
        relative_time_anchor: str | None,
        event_id_mapping: dict[str, str],
    ) -> str | None:
        if relative_time_anchor is None:
            return None
        if not event_id_mapping:
            return relative_time_anchor

        pattern = re.compile(
            "|".join(
                re.escape(source_id)
                for source_id in sorted(event_id_mapping.keys(), key=len, reverse=True)
            )
        )
        return pattern.sub(lambda match: event_id_mapping[match.group(0)], relative_time_anchor)

    def _persist_events(self, events: list[dict[str, Any]]) -> int:
        logger.info(
            "[TimelineAgent] job=%s persisting %d timeline event(s) to Cosmos",
            self.job_id,
            len(events),
        )
        count = 0
        for evt in events:
            upsert_timeline_event(
                job_id=self.job_id,
                event_id=evt["event_id"],
                description=evt["description"],
                chapter_num=evt["chapter_num"],
                chapter_title=evt.get("chapter_title"),
                order=evt["order"],
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
        if events:
            logger.info(
                "[TimelineAgent] job=%s persisted timeline range %s -> %s",
                self.job_id,
                events[0]["event_id"],
                events[-1]["event_id"],
            )
        return count

    def _merge_completed_agents(self, new_agent: str) -> list[str]:
        existing: set[str] = set()
        try:
            full_state = get_full_job_state(self.job_id)
            job = full_state.get("job", {})
            completed_agents = job.get("completed_agents", [])
            if isinstance(completed_agents, list):
                existing.update(
                    str(agent).strip()
                    for agent in completed_agents
                    if isinstance(agent, str) and agent.strip()
                )
        except Exception:
            existing = set()

        # ingestion is always required before timeline in current pipeline
        baseline = {"ingestion_agent"}
        if new_agent:
            baseline.add(new_agent)
        baseline.update(existing)
        return sorted(baseline)

    def _local_response_format(self) -> dict[str, Any]:
        max_events = _timeline_max_events_per_chapter()
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "chapter_local_timeline",
                "strict": True,
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "events": {
                            "type": "array",
                            "maxItems": max_events,
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "description": {"type": "string"},
                                    "characters_present": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "location": {
                                        "anyOf": [{"type": "string"}, {"type": "null"}]
                                    },
                                    "time_reference": {
                                        "anyOf": [{"type": "string"}, {"type": "null"}]
                                    },
                                    "confidence": {
                                        "anyOf": [{"type": "number"}, {"type": "null"}]
                                    },
                                },
                                "required": [
                                    "description",
                                    "characters_present",
                                    "location",
                                    "time_reference",
                                    "confidence",
                                ],
                            },
                        }
                    },
                    "required": ["events"],
                },
            },
        }

    def _merge_response_format(self) -> dict[str, Any]:
        return {
            "type": "json_schema",
            "json_schema": {
                "name": "merged_story_timeline",
                "strict": True,
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "events": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "additionalProperties": False,
                                "properties": {
                                    "source_event_id": {"type": "string"},
                                    "description": {"type": "string"},
                                    "chapter_num": {"type": "integer"},
                                    "chapter_title": {"type": "string"},
                                    "order": {"type": "integer"},
                                    "characters_present": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "location": {
                                        "anyOf": [{"type": "string"}, {"type": "null"}]
                                    },
                                    "causes": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "caused_by": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                    },
                                    "time_reference": {
                                        "anyOf": [{"type": "string"}, {"type": "null"}]
                                    },
                                    "inferred_date": {
                                        "anyOf": [{"type": "string"}, {"type": "null"}]
                                    },
                                    "inferred_year": {
                                        "anyOf": [{"type": "integer"}, {"type": "null"}]
                                    },
                                    "relative_time_anchor_event_id": {
                                        "anyOf": [{"type": "string"}, {"type": "null"}]
                                    },
                                    "confidence": {
                                        "anyOf": [{"type": "number"}, {"type": "null"}]
                                    },
                                },
                                "required": [
                                    "source_event_id",
                                    "description",
                                    "chapter_num",
                                    "chapter_title",
                                    "order",
                                    "characters_present",
                                    "location",
                                    "causes",
                                    "caused_by",
                                    "time_reference",
                                    "inferred_date",
                                    "inferred_year",
                                    "relative_time_anchor_event_id",
                                    "confidence",
                                ],
                            },
                        }
                    },
                    "required": ["events"],
                },
            },
        }
