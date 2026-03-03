from __future__ import annotations

import json
import logging
from uuid import uuid4

from integrations.azure.blob_repository import download_blob_bytes
from services.parse_service import parse_and_clean

logger = logging.getLogger(__name__)

class IngestionAgent:
    def __init__(self, openai_client, cosmos_client):
        self.openai = openai_client
        self.cosmos = cosmos_client
    
    def run(self, blob_name: str, job_id: str | None = None) -> str:
        