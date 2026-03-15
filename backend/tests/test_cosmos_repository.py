from __future__ import annotations

from integrations.cosmos import cosmos_repository


class FakeContainer:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def query_items(self, **kwargs: object) -> list[dict[str, object]]:
        self.calls.append(kwargs)
        return []


def test_get_timeline_events_orders_by_bracketed_order(monkeypatch) -> None:
    container = FakeContainer()
    monkeypatch.setattr(cosmos_repository, "_get_container", lambda: container)

    result = cosmos_repository.get_timeline_events("job-123")

    assert result == []
    assert 'ORDER BY c["order"]' in str(container.calls[0]["query"])


def test_get_timeline_events_for_chapter_orders_by_bracketed_order(monkeypatch) -> None:
    container = FakeContainer()
    monkeypatch.setattr(cosmos_repository, "_get_container", lambda: container)

    result = cosmos_repository.get_timeline_events_for_chapter("job-123", 3)

    assert result == []
    assert 'ORDER BY c["order"]' in str(container.calls[0]["query"])
