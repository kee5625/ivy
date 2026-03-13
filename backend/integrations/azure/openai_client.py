from __future__ import annotations

import os

from openai import AsyncOpenAI


def get_openai_client() -> AsyncOpenAI | None:
    """
    Temporarily switched to standard OpenAI API instead of Azure/Foundry.
    Requires OPENAI_API_KEY to be set in the environment (.env).
    """
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return None

    return AsyncOpenAI(api_key=api_key)
