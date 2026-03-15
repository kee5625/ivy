from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from agents.timeline_agent import TimelineAgent
from pipeline_status import STATUS_FAILED, STATUS_TIMELINE_COMPLETE, STATUS_TIMELINE_IN_PROGRESS


class FakeCompletions:
    def __init__(self, payload: dict[str, object]):
        self.payload = payload

    async def create(self, **_: object) -> SimpleNamespace:
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=json.dumps(self.payload))
                )
            ]
        )


class FakeOpenAIClient:
    def __init__(self, payload: dict[str, object]):
        self.chat = SimpleNamespace(completions=FakeCompletions(payload))


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
            "summary": [" first beat ", ""],
            "summary_text": "first beat",
            "key_events": ["event"],
            "characters": ["Harry", "Ron"],
            "temporal_markers": ["that night"],
        }
    ]


def test_normalize_events_resequences_and_remaps_references() -> None:
    agent = TimelineAgent(openai_client=object(), job_id="job-123")

    normalized = agent._normalize_events(
        [
            {
                "event_id": "evt_020",
                "description": "Second chronologically",
                "chapter_num": 2,
                "order": 2,
                "causes": [],
                "caused_by": ["evt_010"],
                "relative_time_anchor": "after evt_010",
            },
            {
                "event_id": "evt_010",
                "description": "First chronologically",
                "chapter_num": 1,
                "order": 1,
                "causes": ["evt_020", "evt_999"],
                "caused_by": [],
                "relative_time_anchor": None,
            },
            {
                "event_id": "evt_030",
                "description": "  ",
                "chapter_num": 3,
                "order": 3,
            },
        ]
    )

    assert [event["event_id"] for event in normalized] == ["evt_001", "evt_002"]
    assert normalized[0]["causes"] == ["evt_002"]
    assert normalized[1]["caused_by"] == ["evt_001"]
    assert normalized[1]["relative_time_anchor"] == "after evt_001"


@pytest.mark.asyncio
async def test_run_persists_events_and_updates_job_status(monkeypatch: pytest.MonkeyPatch) -> None:
    chapters = [
        {"chapter_num": 2, "chapter_title": "Later", "summary": [], "key_events": [], "characters": [], "temporal_markers": []},
        {"chapter_num": 1, "chapter_title": "Start", "summary": [], "key_events": [], "characters": [], "temporal_markers": []},
    ]
    llm_payload = {
        "events": [
            {
                "event_id": "evt_100",
                "description": "Late event",
                "chapter_num": 2,
                "chapter_title": "Later",
                "order": 2,
                "caused_by": ["evt_001"],
                "causes": [],
            },
            {
                "event_id": "evt_001",
                "description": "Early event",
                "chapter_num": 1,
                "chapter_title": "Start",
                "order": 1,
                "caused_by": [],
                "causes": ["evt_100"],
            },
        ]
    }
    persisted: list[dict[str, object]] = []
    status_updates: list[dict[str, object]] = []

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

    agent = TimelineAgent(openai_client=FakeOpenAIClient(llm_payload), job_id="job-abc")

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

