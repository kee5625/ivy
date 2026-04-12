from __future__ import annotations

import os
from urllib.parse import urlparse

import httpx
from openai import AsyncOpenAI

_openai_client: AsyncOpenAI | None = None


async def get_openai_client() -> AsyncOpenAI | None:
    global _openai_client

    if _openai_client is not None:
        return _openai_client

    api_key = os.getenv("PROJECT_KEY") or os.getenv("OPENAI_API_KEY")
    base_url = _get_openai_base_url()
    if not api_key or not base_url:
        return None

    base_timeout_seconds = float(os.getenv("OPENAI_TIMEOUT_SECONDS", "60"))
    merge_timeout_seconds = float(os.getenv("TIMELINE_MERGE_TIMEOUT_SECONDS", "45"))
    plot_hole_timeout_seconds = float(
        os.getenv("PLOT_HOLE_TIMEOUT_SECONDS", "45")
    )
    timeout_seconds = max(
        base_timeout_seconds,
        merge_timeout_seconds,
        plot_hole_timeout_seconds,
    )

    _openai_client = AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
        max_retries=0,
        timeout=httpx.Timeout(
            timeout=timeout_seconds,
            connect=min(timeout_seconds, 10.0),
            read=timeout_seconds,
            write=min(timeout_seconds, 20.0),
            pool=min(timeout_seconds, 10.0),
        ),
    )
    return _openai_client


async def close_openai_client() -> None:
    global _openai_client

    if _openai_client is not None:
        await _openai_client.close()
        _openai_client = None


def _get_openai_base_url() -> str | None:
    openai_endpoint = os.getenv("OPENAI_ENDPOINT", "").strip()
    if openai_endpoint:
        return _normalize_openai_base_url(openai_endpoint)

    project_endpoint = os.getenv("PROJECT_ENDPOINT", "").strip()
    if not project_endpoint:
        return None

    parsed = urlparse(project_endpoint)
    if not parsed.scheme or not parsed.netloc:
        return None

    return _normalize_openai_base_url(f"{parsed.scheme}://{parsed.netloc}")


def _normalize_openai_base_url(endpoint: str) -> str:
    return endpoint.rstrip("/") + "/openai/v1"
