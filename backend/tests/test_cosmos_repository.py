from __future__ import annotations

from integrations.cosmos import cosmos_repository


class FakeContainer:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.deleted: list[tuple[str, str]] = []
        self.items_to_return: list[dict[str, object]] = []

    def query_items(self, **kwargs: object) -> list[dict[str, object]]:
        self.calls.append(kwargs)
        return self.items_to_return

    def delete_item(self, item: str, partition_key: str) -> None:
        self.deleted.append((item, partition_key))


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


def test_get_plot_holes_orders_by_hole_id(monkeypatch) -> None:
    container = FakeContainer()
    monkeypatch.setattr(cosmos_repository, "_get_container", lambda: container)

    result = cosmos_repository.get_plot_holes("job-123")

    assert result == []
    assert "ORDER BY c.hole_id" in str(container.calls[0]["query"])


def test_delete_plot_holes_deletes_each_item(monkeypatch) -> None:
    container = FakeContainer()
    container.items_to_return = [
        {"id": "job-123_hole_hole_001"},
        {"id": "job-123_hole_hole_002"},
    ]
    monkeypatch.setattr(cosmos_repository, "_get_container", lambda: container)

    deleted_count = cosmos_repository.delete_plot_holes("job-123")

    assert deleted_count == 2
    assert container.deleted == [
        ("job-123_hole_hole_001", "job-123"),
        ("job-123_hole_hole_002", "job-123"),
    ]
