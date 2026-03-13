from __future__ import annotations

import logging
from uuid import uuid4

from agents.ingestion_agent import IngestionAgent

logger = logging.getLogger(__name__)


async def start_ingestion_job(blob_name: str, openai_client) -> str:
    job_id = uuid4().hex
    agent = IngestionAgent(openai_client=openai_client, job_id=job_id)
    logger.info(f"Starting ingestion job {job_id} for blob {blob_name}")
    result = await agent.run(blob_name)
    logger.info(f"Ingestion job {job_id} completed with result: {result}")
    return result
