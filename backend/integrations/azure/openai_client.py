from __future__ import annotations

import os

from openai import AsyncAzureOpenAI


PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT", "")
OPENAI_ENDPOINT = os.getenv("OPENAI_ENDPOINT", "")
PROJECT_KEY = os.getenv("PROJECT_KEY", "")


def get_openai_client() -> AsyncAzureOpenAI | None:
    """
    Build an async OpenAI client using whichever credentials are present.

    Priority:
      1. OPENAI_ENDPOINT + PROJECT_KEY  — direct Azure OpenAI, works locally
         with no managed identity or Foundry project required.
      2. PROJECT_ENDPOINT (Foundry AIProjectClient) — used in deployed envs
         where a managed identity is attached.
      3. Neither set → return None (callers must handle this gracefully).
    """
    if OPENAI_ENDPOINT and PROJECT_KEY:
        return AsyncAzureOpenAI(
            azure_endpoint=OPENAI_ENDPOINT,
            api_key=PROJECT_KEY,
            api_version="2024-12-01-preview",
        )

    if PROJECT_ENDPOINT:
        try:
            from azure.identity import DefaultAzureCredential
            from azure.ai.projects import AIProjectClient

            project_client = AIProjectClient(
                endpoint=PROJECT_ENDPOINT,
                credential=DefaultAzureCredential(),
            )
            return project_client.inference.get_azure_openai_client(
                api_version="2024-12-01-preview"
            )
        except Exception:
            return None

    return None
