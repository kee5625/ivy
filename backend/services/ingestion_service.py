from __future__ import annotations

from agents.ingestion_agent import IngestionAgent

def start_ingestion_job(blob_name: str, openai_client, cosmos_client) -> str:
    agent = IngestionAgent(openai_client, cosmos_client)
    job_id = str(uuid4())
    logger.info(f"Starting ingestion job {job_id} for blob {blob_name}")
    result = agent.run(blob_name, job_id)
    logger.info(f"Ingestion job {job_id} completed with result: {result}")
    return result