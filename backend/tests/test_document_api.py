from __future__ import annotations

from fastapi.testclient import TestClient

from app import create_app


def test_get_job_status_returns_current_status(monkeypatch) -> None:
    monkeypatch.setattr(
        "integrations.cosmos.cosmos_repository.get_job",
        lambda job_id: {
            "job_id": job_id,
            "status": "plot_hole_complete",
            "current_agent": None,
            "completed_agents": [
                "ingestion_agent",
                "timeline_agent",
                "plot_hole_agent",
            ],
            "error": None,
            "created_at": "2026-03-16T00:00:00+00:00",
            "updated_at": "2026-03-16T00:05:00+00:00",
        },
    )

    with TestClient(create_app()) as client:
        response = client.get("/jobs/job-123")

    assert response.status_code == 200
    assert response.json()["status"] == "plot_hole_complete"


def test_get_chapters_keeps_existing_client_shape(monkeypatch) -> None:
    monkeypatch.setattr(
        "integrations.cosmos.cosmos_repository.get_chapters",
        lambda job_id: [
            {
                "chapter_num": 1,
                "chapter_title": "The Boy Who Lived",
                "summary": ["A boy survives."],
                "key_events": ["A wizard visits."],
                "characters": ["Harry"],
            }
        ],
    )

    with TestClient(create_app()) as client:
        response = client.get("/jobs/job-123/chapters")

    assert response.status_code == 200
    body = response.json()
    assert body["chapter_count"] == 1
    assert body["chapters"][0]["chapter_title"] == "The Boy Who Lived"


def test_get_timeline_returns_ordered_events(monkeypatch) -> None:
    monkeypatch.setattr(
        "integrations.cosmos.cosmos_repository.get_timeline_events",
        lambda job_id: [
            {
                "event_id": "evt_001",
                "description": "Hagrid arrives.",
                "chapter_num": 1,
                "chapter_title": "The Hut on the Rock",
                "order": 1,
                "characters_present": ["hagrid", "harry"],
                "location": "hut",
                "causes": ["evt_002"],
                "caused_by": [],
                "time_reference": "that night",
                "inferred_date": None,
                "inferred_year": None,
                "relative_time_anchor": None,
                "confidence": 0.92,
            }
        ],
    )

    with TestClient(create_app()) as client:
        response = client.get("/jobs/job-123/timeline")

    assert response.status_code == 200
    body = response.json()
    assert body["timeline_event_count"] == 1
    assert body["timeline_events"][0]["event_id"] == "evt_001"


def test_get_plot_holes_returns_empty_list_when_none_exist(monkeypatch) -> None:
    monkeypatch.setattr(
        "integrations.cosmos.cosmos_repository.get_plot_holes",
        lambda job_id: [],
    )

    with TestClient(create_app()) as client:
        response = client.get("/jobs/job-123/plot-holes")

    assert response.status_code == 200
    assert response.json() == {
        "job_id": "job-123",
        "plot_hole_count": 0,
        "plot_holes": [],
    }


def test_get_plot_holes_returns_stored_findings(monkeypatch) -> None:
    monkeypatch.setattr(
        "integrations.cosmos.cosmos_repository.get_plot_holes",
        lambda job_id: [
            {
                "hole_id": "hole_001",
                "hole_type": "location_conflict",
                "severity": "high",
                "description": "Jon is placed in the archive and the harbor during the same morning scene.",
                "chapters_involved": [4, 5],
                "characters_involved": ["Jon"],
                "events_involved": ["evt_011", "evt_012"],
            }
        ],
    )

    with TestClient(create_app()) as client:
        response = client.get("/jobs/job-123/plot-holes")

    assert response.status_code == 200
    assert response.json() == {
        "job_id": "job-123",
        "plot_hole_count": 1,
        "plot_holes": [
            {
                "hole_id": "hole_001",
                "hole_type": "location_conflict",
                "severity": "high",
                "description": "Jon is placed in the archive and the harbor during the same morning scene.",
                "chapters_involved": [4, 5],
                "characters_involved": ["Jon"],
                "events_involved": ["evt_011", "evt_012"],
            }
        ],
    }

