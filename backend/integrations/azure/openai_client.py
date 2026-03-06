from __future__ import annotations

import os

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient


PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT", "")


def create_project_client() -> AIProjectClient | None:
    if not PROJECT_ENDPOINT:
        return None

    return AIProjectClient(
        endpoint=PROJECT_ENDPOINT,
        credential=DefaultAzureCredential(),
    )


def get_inference_client(project_client: AIProjectClient):
    return project_client.inference.get_azure_openai_client(api_version="2024-12-01-preview")
