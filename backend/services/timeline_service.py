from __future__ import annotations

import logging

from agents.timeline_agent import TimelineAgent

logger = logging.getLogger(__name__)


async def start_timeline_job(job_id: str, openai_client) -> str:
    """
    Run timeline generation for an existing ingestion job.

    Parameters
    ----------
    job_id:
        Existing job identifier whose chapters are already stored.
    openai_client:
        Initialized async OpenAI client from app state.

    Returns
    -------
    str
        The same job_id after timeline generation completes.
    """
    agent = TimelineAgent(openai_client=openai_client, job_id=job_id)
    logger.info("Starting timeline job %s", job_id)
    result = await agent.run()
    logger.info("Timeline job %s completed with result: %s", job_id, result)
    return result
