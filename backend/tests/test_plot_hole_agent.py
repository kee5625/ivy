from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from agents.plot_hole_agent import PlotHoleAgent
from pipeline_status import (
    STATUS_FAILED,
    STATUS_PLOT_HOLE_COMPLETE,
    STATUS_PLOT_HOLE_IN_PROGRESS,
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


def _story_state() -> dict[str, object]:
    return {
        "job": {
            "completed_agents": ["ingestion_agent", "timeline_agent"],
        },
        "chapters": [
            {
                "chapter_num": 1,
                "chapter_title": "Arrival",
                "summary": ["Mira arrives in the city."],
                "key_events": ["Mira hides a device in the archive."],
                "characters": ["Mira", "Jon"],
                "temporal_markers": ["that night"],
            },
            {
                "chapter_num": 2,
                "chapter_title": "Aftermath",
                "summary": ["Jon speaks to Mira after her confirmed death."],
                "key_events": ["Jon hears Mira answer over the radio."],
                "characters": ["Jon", "Mira"],
                "temporal_markers": ["the next morning"],
            },
        ],
        "entities": [
            {
                "entity_id": "mira",
                "name": "Mira",
                "entity_type": "character",
                "appears_in_chapters": [1, 2],
                "aliases": ["Captain Mira"],
                "role": "protagonist",
            }
        ],
        "timeline": [
            {
                "event_id": "evt_001",
                "description": "Mira dies in the archive collapse.",
                "chapter_num": 1,
                "chapter_title": "Arrival",
                "order": 1,
                "characters_present": ["Mira", "Jon"],
                "location": "archive",
                "causes": ["evt_002"],
                "caused_by": [],
                "time_reference": "that night",
                "inferred_date": None,
                "inferred_year": None,
                "relative_time_anchor": None,
                "confidence": 0.94,
            },
            {
                "event_id": "evt_002",
                "description": "Jon hears Mira answer over the radio the next morning.",
                "chapter_num": 2,
                "chapter_title": "Aftermath",
                "order": 2,
                "characters_present": ["Jon", "Mira"],
                "location": "watchtower",
                "causes": [],
                "caused_by": ["evt_001"],
                "time_reference": "the next morning",
                "inferred_date": None,
                "inferred_year": None,
                "relative_time_anchor": "after evt_001",
                "confidence": 0.92,
            },
        ],
        "plot_holes": [],
    }


@pytest.mark.asyncio
async def test_run_persists_plot_holes_and_updates_job_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    status_updates: list[dict[str, object]] = []
    persisted: list[dict[str, object]] = []

    monkeypatch.setattr(
        "agents.plot_hole_agent.get_full_job_state",
        lambda job_id: _story_state(),
    )
    monkeypatch.setattr(
        "agents.plot_hole_agent.delete_plot_holes",
        lambda job_id: 0,
    )
    monkeypatch.setattr(
        "agents.plot_hole_agent.upsert_plot_hole",
        lambda **kwargs: persisted.append(kwargs),
    )
    monkeypatch.setattr(
        "agents.plot_hole_agent.update_job_status",
        lambda job_id, **kwargs: status_updates.append({"job_id": job_id, **kwargs}),
    )

    def responder(_: dict[str, object]) -> dict[str, object]:
        return {
            "findings": [
                {
                    "hole_type": "dead_character_speaks",
                    "severity": "high",
                    "description": "Mira is confirmed dead in evt_001, but evt_002 presents her as actively answering Jon the next morning.",
                    "chapters_involved": [1, 2],
                    "characters_involved": ["Captain Mira"],
                    "events_involved": ["evt_001", "evt_002"],
                    "confidence": 0.93,
                }
            ]
        }

    agent = PlotHoleAgent(openai_client=FakeOpenAIClient(responder), job_id="job-123")

    result = await agent.run()

    assert result == "job-123"
    assert [item["status"] for item in status_updates] == [
        STATUS_PLOT_HOLE_IN_PROGRESS,
        STATUS_PLOT_HOLE_COMPLETE,
    ]
    assert status_updates[-1]["current_agent"] is None
    assert status_updates[-1]["completed_agents"] == [
        "ingestion_agent",
        "plot_hole_agent",
        "timeline_agent",
    ]
    assert persisted == [
        {
            "job_id": "job-123",
            "hole_id": "hole_001",
            "hole_type": "dead_character_speaks",
            "severity": "high",
            "description": "Mira is confirmed dead in evt_001, but evt_002 presents her as actively answering Jon the next morning.",
            "chapters_involved": [1, 2],
            "characters_involved": ["Mira"],
            "events_involved": ["evt_001", "evt_002"],
        }
    ]


@pytest.mark.asyncio
async def test_run_succeeds_with_no_findings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    status_updates: list[dict[str, object]] = []
    deleted_counts: list[int] = []
    persisted: list[dict[str, object]] = []

    monkeypatch.setattr(
        "agents.plot_hole_agent.get_full_job_state",
        lambda job_id: _story_state(),
    )
    monkeypatch.setattr(
        "agents.plot_hole_agent.delete_plot_holes",
        lambda job_id: deleted_counts.append(2) or 2,
    )
    monkeypatch.setattr(
        "agents.plot_hole_agent.upsert_plot_hole",
        lambda **kwargs: persisted.append(kwargs),
    )
    monkeypatch.setattr(
        "agents.plot_hole_agent.update_job_status",
        lambda job_id, **kwargs: status_updates.append({"job_id": job_id, **kwargs}),
    )

    agent = PlotHoleAgent(
        openai_client=FakeOpenAIClient(lambda _: {"findings": []}),
        job_id="job-456",
    )

    result = await agent.run()

    assert result == "job-456"
    assert deleted_counts == [2]
    assert persisted == []
    assert status_updates[-1]["status"] == STATUS_PLOT_HOLE_COMPLETE


@pytest.mark.asyncio
async def test_plot_hole_retries_once_after_timeout_then_succeeds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PLOT_HOLE_MAX_RETRIES", "2")
    attempts = {"count": 0}
    agent = PlotHoleAgent(openai_client=object(), job_id="job-timeout")

    async def fake_request(
        story_state: dict[str, object],
        attempt: int,
    ) -> list[dict[str, object]]:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("Request timed out.")
        return [
            {
                "hole_type": "timeline_paradox",
                "severity": "medium",
                "description": "A supported chronology contradiction exists.",
                "chapters_involved": [1],
                "characters_involved": [],
                "events_involved": ["evt_001"],
                "confidence": 0.8,
            }
        ]

    monkeypatch.setattr(agent, "_request_plot_holes", fake_request)

    result = await agent._extract_plot_holes_with_retry(_story_state())

    assert attempts["count"] == 2
    assert result[0]["hole_type"] == "timeline_paradox"


@pytest.mark.asyncio
async def test_run_marks_job_failed_when_timeline_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    status_updates: list[dict[str, object]] = []
    state = _story_state()
    state["timeline"] = []

    monkeypatch.setattr(
        "agents.plot_hole_agent.get_full_job_state",
        lambda job_id: state,
    )
    monkeypatch.setattr(
        "agents.plot_hole_agent.update_job_status",
        lambda job_id, **kwargs: status_updates.append({"job_id": job_id, **kwargs}),
    )

    agent = PlotHoleAgent(openai_client=object(), job_id="job-missing")

    with pytest.raises(RuntimeError, match="No timeline events found"):
        await agent.run()

    assert status_updates[0]["status"] == STATUS_PLOT_HOLE_IN_PROGRESS
    assert status_updates[-1]["status"] == STATUS_FAILED
