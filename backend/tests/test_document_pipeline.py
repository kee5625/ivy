from __future__ import annotations

import pytest

from api.routes.document import _run_ingestion


@pytest.mark.asyncio
async def test_run_ingestion_executes_agents_in_order(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str | None]] = []

    class FakeIngestionAgent:
        def __init__(self, openai_client, job_id: str):
            assert openai_client == "client"
            assert job_id == "job-1"

        async def run(self, blob_name: str) -> str:
            calls.append(("ingestion", blob_name))
            return "job-1"

    class FakeTimelineAgent:
        def __init__(self, openai_client, job_id: str):
            assert openai_client == "client"
            assert job_id == "job-1"

        async def run(self) -> str:
            calls.append(("timeline", None))
            return "job-1"

    monkeypatch.setattr("api.routes.document.IngestionAgent", FakeIngestionAgent)
    monkeypatch.setattr("api.routes.document.TimelineAgent", FakeTimelineAgent)

    await _run_ingestion("client", "job-1", "story.pdf")

    assert calls == [("ingestion", "story.pdf"), ("timeline", None)]


@pytest.mark.asyncio
async def test_run_ingestion_stops_after_ingestion_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, str | None]] = []

    class FakeIngestionAgent:
        def __init__(self, openai_client, job_id: str):
            pass

        async def run(self, blob_name: str) -> str:
            calls.append(("ingestion", blob_name))
            raise RuntimeError("boom")

    class FakeTimelineAgent:
        def __init__(self, openai_client, job_id: str):
            pass

        async def run(self) -> str:
            calls.append(("timeline", None))
            return "job-1"

    monkeypatch.setattr("api.routes.document.IngestionAgent", FakeIngestionAgent)
    monkeypatch.setattr("api.routes.document.TimelineAgent", FakeTimelineAgent)

    await _run_ingestion("client", "job-1", "story.pdf")

    assert calls == [("ingestion", "story.pdf")]

