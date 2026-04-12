from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

import app as app_module
from integrations.azure import openai_client as openai_client_module


class FakeOpenAIClient:
    def __init__(self) -> None:
        self.closed = False

    async def close(self) -> None:
        self.closed = True


@pytest.mark.asyncio
async def test_get_openai_client_returns_none_without_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PROJECT_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_ENDPOINT", "https://example.openai.azure.com")
    await openai_client_module.close_openai_client()

    client = await openai_client_module.get_openai_client()

    assert client is None


@pytest.mark.asyncio
async def test_get_openai_client_uses_foundry_api_key_and_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PROJECT_KEY", "project-key-123")
    monkeypatch.setenv("OPENAI_ENDPOINT", "https://example.openai.azure.com")
    monkeypatch.setenv("OPENAI_TIMEOUT_SECONDS", "60")
    monkeypatch.setenv("TIMELINE_MERGE_TIMEOUT_SECONDS", "45")
    monkeypatch.setenv("PLOT_HOLE_TIMEOUT_SECONDS", "30")
    await openai_client_module.close_openai_client()

    created: dict[str, object] = {}

    def fake_async_openai_factory(**kwargs: object) -> FakeOpenAIClient:
        created["kwargs"] = kwargs
        client = FakeOpenAIClient()
        created["client"] = client
        return client

    monkeypatch.setattr(openai_client_module, "AsyncOpenAI", fake_async_openai_factory)

    client = await openai_client_module.get_openai_client()

    assert client is created["client"]
    kwargs = created["kwargs"]
    assert kwargs["api_key"] == "project-key-123"
    assert kwargs["base_url"] == "https://example.openai.azure.com/openai/v1"
    assert kwargs["max_retries"] == 0
    timeout = kwargs["timeout"]
    assert isinstance(timeout, httpx.Timeout)
    assert timeout.connect == 10.0
    assert timeout.read == 60.0
    assert timeout.write == 20.0
    assert timeout.pool == 10.0


@pytest.mark.asyncio
async def test_get_openai_client_derives_base_url_from_project_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PROJECT_KEY", "project-key-123")
    monkeypatch.setenv(
        "PROJECT_ENDPOINT",
        "https://example.services.ai.azure.com/api/projects/ivy",
    )
    monkeypatch.delenv("OPENAI_ENDPOINT", raising=False)
    await openai_client_module.close_openai_client()

    created: dict[str, object] = {}

    def fake_async_openai_factory(**kwargs: object) -> FakeOpenAIClient:
        created["kwargs"] = kwargs
        client = FakeOpenAIClient()
        created["client"] = client
        return client

    monkeypatch.setattr(openai_client_module, "AsyncOpenAI", fake_async_openai_factory)

    await openai_client_module.get_openai_client()

    kwargs = created["kwargs"]
    assert kwargs["base_url"] == "https://example.services.ai.azure.com/openai/v1"


@pytest.mark.asyncio
async def test_close_openai_client_closes_openai_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PROJECT_KEY", "project-key-123")
    monkeypatch.setenv("OPENAI_ENDPOINT", "https://example.openai.azure.com")
    await openai_client_module.close_openai_client()

    created: dict[str, object] = {}

    def fake_async_openai_factory(**kwargs: object) -> FakeOpenAIClient:
        client = FakeOpenAIClient()
        created["client"] = client
        return client

    monkeypatch.setattr(openai_client_module, "AsyncOpenAI", fake_async_openai_factory)

    await openai_client_module.get_openai_client()
    await openai_client_module.close_openai_client()

    client = created["client"]
    assert client.closed is True


def test_app_startup_accepts_foundry_client(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_client = object()
    closed = {"value": False}

    async def fake_get_openai_client() -> object:
        return fake_client

    async def fake_close_openai_client() -> None:
        closed["value"] = True

    monkeypatch.setattr(app_module, "get_openai_client", fake_get_openai_client)
    monkeypatch.setattr(app_module, "close_openai_client", fake_close_openai_client)

    with TestClient(app_module.create_app()) as client:
        assert client.app.state.openai_client is fake_client
        response = client.get("/api/health")

    assert response.status_code == 200
    assert closed["value"] is True


def test_app_startup_handles_foundry_init_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    closed = {"value": False}

    async def fake_get_openai_client() -> object:
        raise RuntimeError("credential unavailable")

    async def fake_close_openai_client() -> None:
        closed["value"] = True

    monkeypatch.setattr(app_module, "get_openai_client", fake_get_openai_client)
    monkeypatch.setattr(app_module, "close_openai_client", fake_close_openai_client)

    with TestClient(app_module.create_app()) as client:
        assert client.app.state.openai_client is None
        response = client.get("/api/health")

    assert response.status_code == 200
    assert closed["value"] is True
