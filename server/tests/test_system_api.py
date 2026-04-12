from __future__ import annotations

from fastapi.testclient import TestClient

import app as app_module


def test_health_endpoints_expose_liveness_and_readiness(monkeypatch) -> None:
    async def fake_get_openai_client() -> object:
        return object()

    async def fake_close_openai_client() -> None:
        return None

    monkeypatch.setattr(app_module, "get_openai_client", fake_get_openai_client)
    monkeypatch.setattr(app_module, "close_openai_client", fake_close_openai_client)
    async def fake_openai_probe(request) -> dict[str, object]:
        return {"required": True, "status": "ready", "detail": "ok"}

    async def fake_blob_probe() -> dict[str, object]:
        return {"required": True, "status": "ready", "detail": "ok"}

    async def fake_cosmos_probe() -> dict[str, object]:
        return {"required": True, "status": "ready", "detail": "ok"}

    async def fake_gremlin_probe(request) -> dict[str, object]:
        return {"required": False, "status": "skipped", "detail": "optional"}

    monkeypatch.setattr("api.routes.system._probe_openai_dependency", fake_openai_probe)
    monkeypatch.setattr("api.routes.system._probe_blob_dependency", fake_blob_probe)
    monkeypatch.setattr("api.routes.system._probe_cosmos_dependency", fake_cosmos_probe)
    monkeypatch.setattr("api.routes.system._probe_gremlin_dependency", fake_gremlin_probe)

    with TestClient(app_module.create_app()) as client:
        health_response = client.get("/api/health")
        live_response = client.get("/api/health/live")
        ready_response = client.get("/api/health/ready")

    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok", "service": "ivy-backend"}
    assert live_response.status_code == 200
    assert live_response.json() == {"status": "live", "service": "ivy-backend"}
    assert ready_response.status_code == 200
    assert ready_response.json() == {
        "status": "ready",
        "service": "ivy-backend",
        "checks": {
            "openai": {"required": True, "status": "ready", "detail": "ok"},
            "blob": {"required": True, "status": "ready", "detail": "ok"},
            "cosmos": {"required": True, "status": "ready", "detail": "ok"},
            "gremlin": {"required": False, "status": "skipped", "detail": "optional"},
        },
    }


def test_readiness_returns_503_when_required_dependency_is_not_ready(monkeypatch) -> None:
    async def fake_get_openai_client() -> object:
        return object()

    async def fake_close_openai_client() -> None:
        return None

    monkeypatch.setattr(app_module, "get_openai_client", fake_get_openai_client)
    monkeypatch.setattr(app_module, "close_openai_client", fake_close_openai_client)
    async def fake_openai_probe(request) -> dict[str, object]:
        return {"required": True, "status": "ready", "detail": "ok"}

    async def fake_blob_probe() -> dict[str, object]:
        return {"required": True, "status": "not_ready", "detail": "missing"}

    async def fake_cosmos_probe() -> dict[str, object]:
        return {"required": True, "status": "ready", "detail": "ok"}

    async def fake_gremlin_probe(request) -> dict[str, object]:
        return {"required": False, "status": "skipped", "detail": "optional"}

    monkeypatch.setattr("api.routes.system._probe_openai_dependency", fake_openai_probe)
    monkeypatch.setattr("api.routes.system._probe_blob_dependency", fake_blob_probe)
    monkeypatch.setattr("api.routes.system._probe_cosmos_dependency", fake_cosmos_probe)
    monkeypatch.setattr("api.routes.system._probe_gremlin_dependency", fake_gremlin_probe)

    with TestClient(app_module.create_app()) as client:
        response = client.get("/api/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "service": "ivy-backend",
        "checks": {
            "openai": {"required": True, "status": "ready", "detail": "ok"},
            "blob": {"required": True, "status": "not_ready", "detail": "missing"},
            "cosmos": {"required": True, "status": "ready", "detail": "ok"},
            "gremlin": {"required": False, "status": "skipped", "detail": "optional"},
        },
        "blocking_checks": ["blob"],
    }
