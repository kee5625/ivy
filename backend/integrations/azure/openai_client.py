from __future__ import annotations

import os

import httpx
from openai import AsyncOpenAI


def get_openai_client() -> AsyncOpenAI | None:
    """
    Temporarily switched to standard OpenAI API instead of Azure/Foundry.
    Requires OPENAI_API_KEY to be set in the environment (.env).
    """
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
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

    return AsyncOpenAI(
        api_key=api_key,
        max_retries=0,
        timeout=httpx.Timeout(
            timeout=timeout_seconds,
            connect=min(timeout_seconds, 10.0),
            read=timeout_seconds,
            write=min(timeout_seconds, 20.0),
            pool=min(timeout_seconds, 10.0),
        ),
    )
