from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace

import pytest

from agents.timeline_agent import TimelineAgent
from pipeline_status import (
    STATUS_FAILED,
    STATUS_TIMELINE_COMPLETE,
    STATUS_TIMELINE_IN_PROGRESS,
)


class FakeCompletions:
    def __init__(self, responder):
        self.responder = responder

    async def create(self, **kwargs: object) -> SimpleNamespace:
        payload = self.responder(kwargs)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=json.dumps(payload))
                )
            ]
        )


class FakeOpenAIClient:
    def __init__(self, responder):
        self.chat = SimpleNamespace(completions=FakeCompletions(responder))


def _make_local_event(
    source_event_id: str,
    description: str,
    chapter_num: int,
    order: int,
    *,
    chapter_title: str | None = None,
) -> dict[str, object]:
    return {
        "source_event_id": source_event_id,
        "description": description,
        "chapter_num": chapter_num,
        "chapter_title": chapter_title or f"Chapter {chapter_num}",
        "order": order,
        "characters_present": [],
        "location": None,
        "time_reference": None,
        "confidence": 0.8,
    }


def test_build_llm_input_filters_and_limits_summary_text() -> None:
    agent = TimelineAgent(openai_client=object(), job_id="job-123")

    chapters = [
        {
            "chapter_num": "2",
            "chapter_title": "  Arrival  ",
            "summary": [" first beat ", "", 42],
            "key_events": ["event", None],
            "characters": ["Harry", None, "Ron"],
            "temporal_markers": ["that night", 7],
        }
    ]

    result = agent._build_llm_input(chapters)

    assert result == [
        {
            "chapter_num": 2,
            "chapter_title": "Arrival",
            "summary_text": "first beat",
            "key_events": ["event"],
            "characters": ["Harry", "Ron"],
            "temporal_markers": ["that night"],
        }
    ]


def test_normalize_local_events_assigns_deterministic_ids() -> None:
    agent = TimelineAgent(openai_client=object(), job_id="job-123")

    chapter = {"chapter_num": 3, "chapter_title": "The Forest"}
    raw_events = [
        {
            "description": "Harry enters the forest.",
            "characters_present": ["Harry"],
            "location": "forest",
            "time_reference": "that night",
            "confidence": 0.9,
        },
        {
            "description": "He sees something drinking blood.",
            "characters_present": ["Harry", "Firenze"],
            "location": None,
            "time_reference": None,
            "confidence": 0.85,
        },
    ]

    result = agent._normalize_local_events(chapter, raw_events)

    assert [event["source_event_id"] for event in result] == [
        "ch_03_evt_01",
        "ch_03_evt_02",
    ]
    assert result[0]["chapter_num"] == 3
    assert result[1]["order"] == 2


def test_normalize_events_resequences_chapter_scoped_ids_and_remaps_references() -> None:
    agent = TimelineAgent(openai_client=object(), job_id="job-123")

    normalized = agent._normalize_events(
        [
            {
                "event_id": "ch_02_evt_01",
                "description": "Second chronologically",
                "chapter_num": 2,
                "order": 2,
                "causes": [],
                "caused_by": ["ch_01_evt_01"],
                "relative_time_anchor": "after ch_01_evt_01",
            },
            {
                "event_id": "ch_01_evt_01",
                "description": "First chronologically",
                "chapter_num": 1,
                "order": 1,
                "causes": ["ch_02_evt_01", "missing_evt"],
                "caused_by": [],
                "relative_time_anchor": None,
            },
        ]
    )

    assert [event["event_id"] for event in normalized] == ["evt_001", "evt_002"]
    assert normalized[0]["causes"] == ["evt_002"]
    assert normalized[1]["caused_by"] == ["evt_001"]
    assert normalized[1]["relative_time_anchor"] == "after evt_001"


@pytest.mark.asyncio
async def test_extract_local_timelines_respects_configured_concurrency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("TIMELINE_CHAPTER_CONCURRENCY", "2")
    agent = TimelineAgent(openai_client=object(), job_id="job-123")

    chapters = [
        {"chapter_num": 1},
        {"chapter_num": 2},
        {"chapter_num": 3},
        {"chapter_num": 4},
    ]

    active = 0
    max_active = 0

    async def fake_with_retry(chapter: dict[str, object]) -> list[dict[str, object]]:
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        await asyncio.sleep(0.01)
        active -= 1
        return [
            {
                "source_event_id": f"ch_{int(chapter['chapter_num']):02d}_evt_01",
                "description": "event",
                "chapter_num": chapter["chapter_num"],
                "chapter_title": "",
                "order": 1,
                "characters_present": [],
                "location": None,
                "time_reference": None,
                "confidence": 0.8,
            }
        ]

    monkeypatch.setattr(
        agent,
        "_extract_local_timeline_for_chapter_with_retry",
        fake_with_retry,
    )

    results = await agent._extract_local_timelines(chapters)

    assert len(results) == 4
    assert max_active <= 2


@pytest.mark.asyncio
async def test_local_timeline_retries_once_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    agent = TimelineAgent(openai_client=object(), job_id="job-123")
    chapter = {"chapter_num": 1, "chapter_title": "Start"}
    attempts = {"count": 0}

    async def fake_request(chapter_arg: dict[str, object], attempt: int) -> list[dict[str, object]]:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("timeout")
        return [
            {
                "source_event_id": "ch_01_evt_01",
                "description": "Recovered",
                "chapter_num": 1,
                "chapter_title": "Start",
                "order": 1,
                "characters_present": [],
                "location": None,
                "time_reference": None,
                "confidence": 0.7,
            }
        ]

    monkeypatch.setattr(agent, "_request_local_timeline", fake_request)

    result = await agent._extract_local_timeline_for_chapter_with_retry(chapter)

    assert len(result) == 1
    assert attempts["count"] == 2


@pytest.mark.asyncio
async def test_merge_retries_once_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TIMELINE_MERGE_ENDPOINT", raising=False)
    monkeypatch.delenv("TIMELINE_MERGE_FALLBACK_ENDPOINT", raising=False)
    agent = TimelineAgent(openai_client=object(), job_id="job-123")
    local_events = [
        {
            "source_event_id": "ch_01_evt_01",
            "description": "First",
            "chapter_num": 1,
            "chapter_title": "Start",
            "order": 1,
            "characters_present": ["Harry"],
            "location": None,
            "time_reference": None,
            "confidence": 0.8,
        }
    ]
    attempts = {"count": 0}

    async def fake_create(**kwargs: object) -> SimpleNamespace:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("timeout")
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content=json.dumps(
                            {
                                "events": [
                                    {
                                        "source_event_id": "ch_01_evt_01",
                                        "description": "First",
                                        "chapter_num": 1,
                                        "chapter_title": "Start",
                                        "order": 1,
                                        "characters_present": ["Harry"],
                                        "location": None,
                                        "causes": [],
                                        "caused_by": [],
                                        "time_reference": None,
                                        "inferred_date": None,
                                        "inferred_year": None,
                                        "relative_time_anchor_event_id": None,
                                        "confidence": 0.8,
                                    }
                                ]
                            }
                        )
                    )
                )
            ]
        )

    agent.openai = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=fake_create)))

    result = await agent._merge_local_timelines(local_events)

    assert result[0]["event_id"] == "evt_001"
    assert attempts["count"] == 2


@pytest.mark.asyncio
async def test_merge_uses_timeline_merge_endpoint_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    endpoint = (
        "https://example-resource.cognitiveservices.azure.com/openai/deployments/"
        "gpt-4.1/chat/completions?api-version=2024-05-01-preview"
    )
    monkeypatch.setenv("TIMELINE_MERGE_ENDPOINT", endpoint)
    monkeypatch.setenv("TIMELINE_MERGE_KEY", "merge-key-123")
    agent = TimelineAgent(openai_client=object(), job_id="job-123")
    local_events = [
        _make_local_event("ch_01_evt_01", "First local", 1, 1),
    ]
    captured: dict[str, object] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "events": [
                                        {
                                            "source_event_id": "ch_01_evt_01",
                                            "description": "Merged first",
                                            "chapter_num": 1,
                                            "chapter_title": "Chapter 1",
                                            "order": 1,
                                            "characters_present": [],
                                            "location": None,
                                            "causes": [],
                                            "caused_by": [],
                                            "time_reference": None,
                                            "inferred_date": None,
                                            "inferred_year": None,
                                            "relative_time_anchor_event_id": None,
                                            "confidence": 0.8,
                                        }
                                    ]
                                }
                            )
                        }
                    }
                ]
            }

    class FakeAsyncClient:
        def __init__(self, **kwargs: object) -> None:
            captured["timeout"] = kwargs["timeout"]

        async def __aenter__(self) -> "FakeAsyncClient":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:
            return None

        async def post(
            self,
            url: str,
            *,
            headers: dict[str, str],
            json: dict[str, object],
        ) -> FakeResponse:
            captured["url"] = url
            captured["headers"] = headers
            captured["json"] = json
            return FakeResponse()

    monkeypatch.setattr("agents.timeline_agent.httpx.AsyncClient", FakeAsyncClient)

    result = await agent._merge_local_timelines(local_events)

    assert result[0]["event_id"] == "evt_001"
    assert captured["url"] == endpoint
    assert captured["headers"] == {
        "api-key": "merge-key-123",
        "Content-Type": "application/json",
    }
    assert "model" not in captured["json"]


@pytest.mark.asyncio
async def test_large_merge_batches_and_final_order(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TIMELINE_MERGE_ENDPOINT", raising=False)
    monkeypatch.delenv("TIMELINE_MERGE_FALLBACK_ENDPOINT", raising=False)
    monkeypatch.setenv("TIMELINE_MERGE_BATCH_EVENT_LIMIT", "2")
    agent = TimelineAgent(openai_client=None, job_id="job-123")
    local_events = [
        _make_local_event("ch_01_evt_01", "First local", 1, 1),
        _make_local_event("ch_01_evt_02", "Second local", 1, 2),
        _make_local_event("ch_02_evt_01", "Third local", 2, 1),
        _make_local_event("ch_02_evt_02", "Fourth local", 2, 2),
    ]

    def responder(kwargs: dict[str, object]) -> dict[str, object]:
        prompt = str(kwargs["messages"][0]["content"])
        if "Return the globally ordered list of source event ids" in prompt:
            return {
                "ordered_source_event_ids": [
                    "ch_02_evt_01",
                    "ch_01_evt_01",
                    "ch_01_evt_02",
                    "ch_02_evt_02",
                ]
            }
        if '"source_event_id": "ch_01_evt_01"' in prompt:
            return {
                "events": [
                    {
                        "source_event_id": "ch_01_evt_01",
                        "description": "Batch one first",
                        "chapter_num": 1,
                        "chapter_title": "Chapter 1",
                        "order": 1,
                        "characters_present": [],
                        "location": None,
                        "causes": ["ch_01_evt_02"],
                        "caused_by": [],
                        "time_reference": None,
                        "inferred_date": None,
                        "inferred_year": None,
                        "relative_time_anchor_event_id": None,
                        "confidence": 0.9,
                    },
                    {
                        "source_event_id": "ch_01_evt_02",
                        "description": "Batch one second",
                        "chapter_num": 1,
                        "chapter_title": "Chapter 1",
                        "order": 2,
                        "characters_present": [],
                        "location": None,
                        "causes": [],
                        "caused_by": ["ch_01_evt_01"],
                        "time_reference": None,
                        "inferred_date": None,
                        "inferred_year": None,
                        "relative_time_anchor_event_id": "ch_01_evt_01",
                        "confidence": 0.9,
                    },
                ]
            }
        return {
            "events": [
                {
                    "source_event_id": "ch_02_evt_01",
                    "description": "Batch two first",
                    "chapter_num": 2,
                    "chapter_title": "Chapter 2",
                    "order": 1,
                    "characters_present": [],
                    "location": None,
                    "causes": [],
                    "caused_by": [],
                    "time_reference": None,
                    "inferred_date": None,
                    "inferred_year": None,
                    "relative_time_anchor_event_id": None,
                    "confidence": 0.9,
                },
                {
                    "source_event_id": "ch_02_evt_02",
                    "description": "Batch two second",
                    "chapter_num": 2,
                    "chapter_title": "Chapter 2",
                    "order": 2,
                    "characters_present": [],
                    "location": None,
                    "causes": [],
                    "caused_by": [],
                    "time_reference": None,
                    "inferred_date": None,
                    "inferred_year": None,
                    "relative_time_anchor_event_id": None,
                    "confidence": 0.9,
                },
            ]
        }

    agent.openai = FakeOpenAIClient(responder)
    result = await agent._merge_local_timelines(local_events)

    assert [event["description"] for event in result] == [
        "Batch two first",
        "Batch one first",
        "Batch one second",
        "Batch two second",
    ]
    assert result[1]["causes"] == ["evt_003"]
    assert result[2]["caused_by"] == ["evt_002"]
    assert result[2]["relative_time_anchor"] == "after evt_002"


@pytest.mark.asyncio
async def test_batched_merge_timeout_uses_fallback_model_then_local_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TIMELINE_MERGE_ENDPOINT", raising=False)
    monkeypatch.delenv("TIMELINE_MERGE_FALLBACK_ENDPOINT", raising=False)
    monkeypatch.setenv("TIMELINE_MERGE_BATCH_EVENT_LIMIT", "2")
    monkeypatch.setenv("TIMELINE_MERGE_FALLBACK_MODEL", "gpt-4o-mini")
    agent = TimelineAgent(openai_client=None, job_id="job-123")
    local_events = [
        _make_local_event("ch_01_evt_01", "First local", 1, 1),
        _make_local_event("ch_01_evt_02", "Second local", 1, 2),
        _make_local_event("ch_02_evt_01", "Third local", 2, 1),
    ]
    models: list[str] = []

    def responder(kwargs: dict[str, object]) -> dict[str, object]:
        prompt = str(kwargs["messages"][0]["content"])
        models.append(str(kwargs["model"]))
        if "Return the globally ordered list of source event ids" in prompt:
            return {
                "ordered_source_event_ids": [
                    "ch_01_evt_01",
                    "ch_01_evt_02",
                    "ch_02_evt_01",
                ]
            }
        if '"source_event_id": "ch_01_evt_01"' in prompt:
            raise RuntimeError("Request timed out.")
        return {
            "events": [
                {
                    "source_event_id": "ch_02_evt_01",
                    "description": "Recovered third",
                    "chapter_num": 2,
                    "chapter_title": "Chapter 2",
                    "order": 1,
                    "characters_present": [],
                    "location": None,
                    "causes": [],
                    "caused_by": [],
                    "time_reference": None,
                    "inferred_date": None,
                    "inferred_year": None,
                    "relative_time_anchor_event_id": None,
                    "confidence": 0.8,
                }
            ]
        }

    agent.openai = FakeOpenAIClient(responder)
    result = await agent._merge_local_timelines(local_events)

    assert models[:2] == ["gpt-4.1", "gpt-4o-mini"]
    assert [event["description"] for event in result] == [
        "First local",
        "Second local",
        "Recovered third",
    ]
    assert any("batch 1/2" in reason for reason in agent._merge_degraded_reasons)


@pytest.mark.asyncio
async def test_final_order_timeout_degrades_to_chapter_local_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TIMELINE_MERGE_ENDPOINT", raising=False)
    monkeypatch.delenv("TIMELINE_MERGE_FALLBACK_ENDPOINT", raising=False)
    monkeypatch.setenv("TIMELINE_MERGE_BATCH_EVENT_LIMIT", "2")
    agent = TimelineAgent(openai_client=None, job_id="job-123")
    local_events = [
        _make_local_event("ch_01_evt_01", "First local", 1, 1),
        _make_local_event("ch_01_evt_02", "Second local", 1, 2),
        _make_local_event("ch_02_evt_01", "Third local", 2, 1),
        _make_local_event("ch_02_evt_02", "Fourth local", 2, 2),
    ]

    def responder(kwargs: dict[str, object]) -> dict[str, object]:
        prompt = str(kwargs["messages"][0]["content"])
        if "Return the globally ordered list of source event ids" in prompt:
            raise RuntimeError("Request timed out.")
        if '"source_event_id": "ch_01_evt_01"' in prompt:
            return {
                "events": [
                    {
                        "source_event_id": "ch_01_evt_01",
                        "description": "First merged",
                        "chapter_num": 1,
                        "chapter_title": "Chapter 1",
                        "order": 2,
                        "characters_present": [],
                        "location": None,
                        "causes": [],
                        "caused_by": [],
                        "time_reference": None,
                        "inferred_date": None,
                        "inferred_year": None,
                        "relative_time_anchor_event_id": None,
                        "confidence": 0.9,
                    },
                    {
                        "source_event_id": "ch_01_evt_02",
                        "description": "Second merged",
                        "chapter_num": 1,
                        "chapter_title": "Chapter 1",
                        "order": 1,
                        "characters_present": [],
                        "location": None,
                        "causes": [],
                        "caused_by": [],
                        "time_reference": None,
                        "inferred_date": None,
                        "inferred_year": None,
                        "relative_time_anchor_event_id": None,
                        "confidence": 0.9,
                    },
                ]
            }
        return {
            "events": [
                {
                    "source_event_id": "ch_02_evt_01",
                    "description": "Third merged",
                    "chapter_num": 2,
                    "chapter_title": "Chapter 2",
                    "order": 2,
                    "characters_present": [],
                    "location": None,
                    "causes": [],
                    "caused_by": [],
                    "time_reference": None,
                    "inferred_date": None,
                    "inferred_year": None,
                    "relative_time_anchor_event_id": None,
                    "confidence": 0.9,
                },
                {
                    "source_event_id": "ch_02_evt_02",
                    "description": "Fourth merged",
                    "chapter_num": 2,
                    "chapter_title": "Chapter 2",
                    "order": 1,
                    "characters_present": [],
                    "location": None,
                    "causes": [],
                    "caused_by": [],
                    "time_reference": None,
                    "inferred_date": None,
                    "inferred_year": None,
                    "relative_time_anchor_event_id": None,
                    "confidence": 0.9,
                },
            ]
        }

    agent.openai = FakeOpenAIClient(responder)
    result = await agent._merge_local_timelines(local_events)

    assert [event["description"] for event in result] == [
        "First merged",
        "Second merged",
        "Third merged",
        "Fourth merged",
    ]
    assert any("final compact ordering" in reason for reason in agent._merge_degraded_reasons)


@pytest.mark.asyncio
async def test_run_persists_events_and_updates_job_status(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TIMELINE_MERGE_ENDPOINT", raising=False)
    monkeypatch.delenv("TIMELINE_MERGE_FALLBACK_ENDPOINT", raising=False)
    chapters = [
        {
            "chapter_num": 2,
            "chapter_title": "Later",
            "summary": [],
            "key_events": [],
            "characters": [],
            "temporal_markers": [],
        },
        {
            "chapter_num": 1,
            "chapter_title": "Start",
            "summary": [],
            "key_events": [],
            "characters": [],
            "temporal_markers": [],
        },
    ]
    persisted: list[dict[str, object]] = []
    status_updates: list[dict[str, object]] = []

    def responder(kwargs: dict[str, object]) -> dict[str, object]:
        prompt = str(kwargs["messages"][0]["content"])
        if "working on one chapter only" in prompt and '"chapter_num": 1' in prompt:
            return {
                "events": [
                    {
                        "description": "Early event",
                        "characters_present": ["Harry"],
                        "location": None,
                        "time_reference": "that night",
                        "confidence": 0.88,
                    }
                ]
            }
        if "working on one chapter only" in prompt and '"chapter_num": 2' in prompt:
            return {
                "events": [
                    {
                        "description": "Late event",
                        "characters_present": ["Ron"],
                        "location": None,
                        "time_reference": None,
                        "confidence": 0.8,
                    }
                ]
            }
        return {
            "events": [
                {
                    "source_event_id": "ch_01_evt_01",
                    "description": "Early event",
                    "chapter_num": 1,
                    "chapter_title": "Start",
                    "order": 1,
                    "characters_present": ["Harry"],
                    "location": None,
                    "causes": ["ch_02_evt_01"],
                    "caused_by": [],
                    "time_reference": "that night",
                    "inferred_date": None,
                    "inferred_year": None,
                    "relative_time_anchor_event_id": None,
                    "confidence": 0.88,
                },
                {
                    "source_event_id": "ch_02_evt_01",
                    "description": "Late event",
                    "chapter_num": 2,
                    "chapter_title": "Later",
                    "order": 2,
                    "characters_present": ["Ron"],
                    "location": None,
                    "causes": [],
                    "caused_by": ["ch_01_evt_01"],
                    "time_reference": None,
                    "inferred_date": None,
                    "inferred_year": None,
                    "relative_time_anchor_event_id": "ch_01_evt_01",
                    "confidence": 0.8,
                },
            ]
        }

    monkeypatch.setattr("agents.timeline_agent.get_chapters", lambda job_id: chapters)
    monkeypatch.setattr(
        "agents.timeline_agent.upsert_timeline_event",
        lambda **kwargs: persisted.append(kwargs),
    )
    monkeypatch.setattr(
        "agents.timeline_agent.update_job_status",
        lambda job_id, **kwargs: status_updates.append({"job_id": job_id, **kwargs}),
    )
    monkeypatch.setattr(
        "agents.timeline_agent.get_full_job_state",
        lambda job_id: {"job": {"completed_agents": ["ingestion_agent"]}},
    )

    agent = TimelineAgent(openai_client=FakeOpenAIClient(responder), job_id="job-abc")

    result = await agent.run()

    assert result == "job-abc"
    assert [item["status"] for item in status_updates] == [
        STATUS_TIMELINE_IN_PROGRESS,
        STATUS_TIMELINE_COMPLETE,
    ]
    assert status_updates[-1]["completed_agents"] == ["ingestion_agent", "timeline_agent"]
    assert [event["event_id"] for event in persisted] == ["evt_001", "evt_002"]
    assert persisted[0]["causes"] == ["evt_002"]
    assert persisted[1]["caused_by"] == ["evt_001"]
    assert persisted[1]["relative_time_anchor"] == "after evt_001"


@pytest.mark.asyncio
async def test_run_marks_job_failed_when_no_chapters_found(monkeypatch: pytest.MonkeyPatch) -> None:
    status_updates: list[dict[str, object]] = []

    monkeypatch.setattr("agents.timeline_agent.get_chapters", lambda job_id: [])
    monkeypatch.setattr(
        "agents.timeline_agent.update_job_status",
        lambda job_id, **kwargs: status_updates.append({"job_id": job_id, **kwargs}),
    )

    agent = TimelineAgent(openai_client=object(), job_id="job-empty")

    with pytest.raises(RuntimeError, match="No chapters found"):
        await agent.run()

    assert status_updates[0]["status"] == STATUS_TIMELINE_IN_PROGRESS
    assert status_updates[-1]["status"] == STATUS_FAILED
    assert "No chapters found" in status_updates[-1]["error"]
