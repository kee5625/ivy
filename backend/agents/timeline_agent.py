from __future__ import annotations

import json
import logging
import os
import re
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
_MAX_CHAPTER_SUMMARY_CHARS = 1800
_MAX_RETRIES = 3


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

    async def run(self) -> str:
        if self.openai is None:
            raise RuntimeError(
                "OpenAI client is not configured. Set OPENAI_API_KEY in your .env file."
            )

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
            return self.job_id
        except Exception as exc:
            logger.exception("[TimelineAgent] job=%s timeline failed", self.job_id)
            update_job_status(self.job_id, status=STATUS_FAILED, error=str(exc))
            raise

    def _load_chapters(self) -> list[dict[str, Any]]:
        chapters = get_chapters(self.job_id)
        chapters = sorted(chapters, key=lambda c: int(c.get("chapter_num", 0)))
        if len(chapters) > _MAX_CHAPTERS_FOR_PROMPT:
            chapters = chapters[:_MAX_CHAPTERS_FOR_PROMPT]
        return chapters

    async def _generate_timeline_events(
        self,
        chapters: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        payload = self._build_llm_input(chapters)

        prompt = (
            "You are a narrative timeline analyst.\n"
            "Build a globally ordered event timeline from chapter-level story data.\n\n"
            "Requirements:\n"
            "1) Produce one globally ordered list of events across all chapters.\n"
            "2) Preserve narrative causality when ordering events.\n"
            "3) Keep events concise and concrete.\n"
            "4) Include temporal detail when present:\n"
            "   - inferred_date: ISO date YYYY-MM-DD only if explicit/highly reliable.\n"
            "   - inferred_year: integer year only when confidently inferable.\n"
            "   - time_reference: short phrase from source (e.g., 'later that evening').\n"
            "   - relative_time_anchor: optional relation like 'after evt_003'.\n"
            "5) Use event_ids exactly in format evt_001, evt_002, ... with no gaps.\n"
            "6) `order` must be a 1-based integer and match list order.\n"
            "7) Keep `confidence` between 0.0 and 1.0.\n"
            "8) `characters_present` can use normalized slugs if obvious, else plain names.\n"
            "9) `causes` and `caused_by` must reference other event_ids in your output.\n"
            "10) Do NOT invent specifics unsupported by the chapter data.\n\n"
            "Return ONLY valid JSON with this exact top-level shape:\n"
            "{\n"
            '  "events": [\n'
            "    {\n"
            '      "event_id": "evt_001",\n'
            '      "description": "Short event statement",\n'
            '      "chapter_num": 1,\n'
            '      "chapter_title": "Chapter title",\n'
            '      "order": 1,\n'
            '      "characters_present": ["harry_potter"],\n'
            '      "location": null,\n'
            '      "causes": ["evt_002"],\n'
            '      "caused_by": [],\n'
            '      "time_reference": "that night",\n'
            '      "inferred_date": null,\n'
            '      "inferred_year": 1997,\n'
            '      "relative_time_anchor": null,\n'
            '      "confidence": 0.82\n'
            "    }\n"
            "  ]\n"
            "}\n\n"
            f"Input chapter data:\n{json.dumps(payload, ensure_ascii=False)}"
        )

        last_exc: Exception | None = None
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                response = await self.openai.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    timeout=90.0,
                )
                raw_content = response.choices[0].message.content
                parsed = json.loads(raw_content)
                events = parsed.get("events", [])
                if not isinstance(events, list):
                    raise RuntimeError("LLM output invalid: 'events' is not a list")
                normalized = self._normalize_events(events)
                return normalized[:_MAX_TIMELINE_EVENTS]
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "[TimelineAgent] job=%s attempt %d/%d failed: %r",
                    self.job_id,
                    attempt,
                    _MAX_RETRIES,
                    exc,
                )

        raise RuntimeError(
            f"Timeline generation failed after {_MAX_RETRIES} attempts: {repr(last_exc)}"
        ) from last_exc

    def _build_llm_input(self, chapters: list[dict[str, Any]]) -> list[dict[str, Any]]:
        compact: list[dict[str, Any]] = []
        for ch in chapters:
            summary = ch.get("summary") or []
            key_events = ch.get("key_events") or []
            temporal_markers = ch.get("temporal_markers") or []
            characters = ch.get("characters") or []

            summary_text = " ".join(
                s.strip() for s in summary if isinstance(s, str) and s.strip()
            )[:_MAX_CHAPTER_SUMMARY_CHARS]

            compact.append(
                {
                    "chapter_num": int(ch.get("chapter_num", 0)),
                    "chapter_title": str(ch.get("chapter_title", "")).strip(),
                    "summary": [s for s in summary if isinstance(s, str)],
                    "summary_text": summary_text,
                    "key_events": [e for e in key_events if isinstance(e, str)],
                    "characters": [c for c in characters if isinstance(c, str)],
                    "temporal_markers": [
                        t for t in temporal_markers if isinstance(t, str)
                    ],
                }
            )
        return compact

    def _normalize_events(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for i, raw in enumerate(events, start=1):
            event_id = raw.get("event_id")
            if not isinstance(event_id, str) or not event_id.strip():
                event_id = f"evt_{i:03d}"

            description = raw.get("description")
            if not isinstance(description, str) or not description.strip():
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
                final_event_ids,
            )
            item.pop("_source_event_id", None)
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
        final_event_ids: set[str],
    ) -> str | None:
        if relative_time_anchor is None:
            return None

        def _replace(match: re.Match[str]) -> str:
            event_id = match.group(0)
            if event_id in event_id_mapping:
                return event_id_mapping[event_id]
            if event_id in final_event_ids:
                return event_id
            return event_id

        return re.sub(r"\bevt_\d{3}\b", _replace, relative_time_anchor)

    def _persist_events(self, events: list[dict[str, Any]]) -> int:
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
