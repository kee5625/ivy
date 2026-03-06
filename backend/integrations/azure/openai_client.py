from __future__ import annotations

import os

from openai import AsyncAzureOpenAI


def get_openai_client() -> AsyncAzureOpenAI | None:
    """
    Read env vars here (not at module level) so that load_dotenv() in
    config.py is guaranteed to have run before these are checked.

    Priority:
      1. OPENAI_ENDPOINT + PROJECT_KEY  -- direct Azure OpenAI, works locally.
      2. PROJECT_ENDPOINT (Foundry)     -- managed identity in deployed envs.
      3. Neither set                    -> None.
    """
    openai_endpoint = os.getenv("OPENAI_ENDPOINT", "")
    project_key     = os.getenv("PROJECT_KEY", "")
    project_endpoint = os.getenv("PROJECT_ENDPOINT", "")

    if openai_endpoint and project_key:
        return AsyncAzureOpenAI(
            azure_endpoint=openai_endpoint,
            api_key=project_key,
            api_version="2025-01-01-preview",
        )

    if project_endpoint:
        try:
            from azure.identity import DefaultAzureCredential
            from azure.ai.projects import AIProjectClient

            project_client = AIProjectClient(
                endpoint=project_endpoint,
                credential=DefaultAzureCredential(),
            )
            return project_client.inference.get_azure_openai_client(
                api_version="2024-01-01-preview"
            )
        except Exception:
            return None

    return None
