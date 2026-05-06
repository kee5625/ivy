"""Document job routes."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from db.redis import set_job_manifest
from db.repository import (
    ChapterRepository,
    JobRepository,
    PlotHoleRepository,
    TimelineRepository,
)
from utils.job import get_job_status, set_job_status

logger = logging.getLogger(__name__)
router = APIRouter(tags=["document"])

_STATUS_MAP: dict[str, str] = {
    "pending": "pending",
    "ingestion_in_progress": "ingestion_in_progress",
    "ingestion_complete": "ingestion_complete",
    "timeline_in_progress": "timeline_in_progress",
    "timeline_complete": "timeline_complete",
    "plot_hole_in_progress": "plot_hole_in_progress",
    "plot_hole_complete": "plot_hole_complete",
    "failed": "failed",
}


# =============================================================================
# Helpers
# =============================================================================

def _ensure_list(value: Any) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, ValueError):
            return []
    return []


def _serialize_chapter(chapter: dict[str, Any]) -> dict[str, Any]:
    return {
        "chapter_num": chapter["chapter_num"],
        "chapter_title": chapter.get("title") or "",
        "summary": _ensure_list(chapter.get("summary")),
        "key_events": _ensure_list(chapter.get("key_events")),
        "characters": list(chapter.get("characters") or []),
    }


def _serialize_event(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": event["event_id"],
        "description": event["description"],
        "chapter_num": event["chapter_num"],
        "chapter_title": event.get("chapter_title") or "",
        "order": event["event_order"],
        "characters_present": list(event.get("characters_present") or []),
        "location": event.get("location"),
        "causes": list(event.get("causes") or []),
        "caused_by": list(event.get("caused_by") or []),
        "time_reference": event.get("time_reference"),
        "inferred_date": event.get("inferred_date"),
        "inferred_year": event.get("inferred_year"),
        "relative_time_anchor": event.get("relative_time_anchor"),
        "confidence": event.get("confidence"),
    }


def _serialize_hole(hole: dict[str, Any]) -> dict[str, Any]:
    return {
        "hole_id": hole["hole_id"],
        "hole_type": hole.get("hole_type") or "",
        "severity": hole.get("severity") or "medium",
        "description": hole["description"],
        "chapters_involved": list(hole.get("chapters_involved") or []),
        "characters_involved": list(hole.get("characters_involved") or []),
        "events_involved": list(hole.get("events_involved") or []),
    }


# =============================================================================
# Pipeline runner (background task)
# =============================================================================

async def _run_pipeline(job_id: str, pdf_key: str) -> None:
    from agents.ingestion_agent import ingestion_agent
    from agents.timeline_agent import timeline_agent
    from agents.plot_hole_agent import plot_hole_agent

    try:
        logger.info("[Pipeline] job=%s starting ingestion", job_id)
        await ingestion_agent.ainvoke({"job_id": job_id, "pdf_key": pdf_key})
        logger.info("[Pipeline] job=%s starting timeline", job_id)
        await timeline_agent.ainvoke({"job_id": job_id})
        logger.info("[Pipeline] job=%s starting plot_hole", job_id)
        await plot_hole_agent.ainvoke({"job_id": job_id})
        logger.info("[Pipeline] job=%s complete", job_id)
    except Exception:
        logger.exception("[Pipeline] job=%s failed", job_id)


# =============================================================================
# Routes
# =============================================================================

class CreateJobRequest(BaseModel):
    filename: str
    object_key: str


@router.post("")
async def create_job(body: CreateJobRequest) -> dict:
    job_id = str(uuid.uuid4())
    await JobRepository.create(
        job_id,
        pdf_filename=body.filename,
        pdf_key=body.object_key,
    )
    await set_job_manifest(job_id, body.object_key)
    asyncio.create_task(_run_pipeline(job_id, body.object_key))
    logger.info("[API] created job=%s for file=%s", job_id, body.filename)
    return {"job_id": job_id}


@router.get("/{job_id}")
async def get_job(job_id: str) -> dict:
    redis_state = await get_job_status(job_id)
    db_job = await JobRepository.get(job_id)

    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    if redis_state:
        status = redis_state.get("status", db_job["status"])
        current_agent = redis_state.get("current_agent")
        completed_agents = redis_state.get("completed_agents") or []
        error = redis_state.get("error")
    else:
        status = db_job["status"]
        current_agent = db_job.get("current_agent")
        completed_agents = db_job.get("completed_agents") or []
        error = db_job.get("error")

    return {
        "job_id": job_id,
        "status": _STATUS_MAP.get(status, status),
        "current_agent": current_agent or None,
        "completed_agents": completed_agents,
        "error": error or None,
        "created_at": str(db_job["created_at"]),
        "updated_at": str(db_job["updated_at"]),
    }


@router.get("/{job_id}/chapters")
async def get_chapters(job_id: str) -> dict:
    db_job = await JobRepository.get(job_id)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    chapters = await ChapterRepository.get_by_job(job_id)
    return {"chapters": [_serialize_chapter(c) for c in chapters]}


@router.get("/{job_id}/timeline")
async def get_timeline(job_id: str) -> dict:
    db_job = await JobRepository.get(job_id)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    events = await TimelineRepository.get_by_job(job_id)
    return {"timeline_events": [_serialize_event(e) for e in events]}


@router.get("/{job_id}/plot-holes")
async def get_plot_holes(job_id: str) -> dict:
    db_job = await JobRepository.get(job_id)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    holes = await PlotHoleRepository.get_by_job(job_id)
    return {"plot_holes": [_serialize_hole(h) for h in holes]}


@router.post("/{job_id}/rerun-plot-holes")
async def rerun_plot_holes(job_id: str) -> dict:
    """Re-run only the plot hole agent against already-ingested data.

    Useful when the agent code/prompt changes but the book hasn't changed —
    skips the 10-minute ingestion + timeline pipeline.
    """
    from agents.plot_hole_agent import plot_hole_agent

    db_job = await JobRepository.get(job_id)
    if db_job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    # Verify prerequisite data exists
    chapters = await ChapterRepository.get_by_job(job_id)
    if not chapters:
        raise HTTPException(
            status_code=422,
            detail="No chapter data found — run the full pipeline first",
        )
    events = await TimelineRepository.get_by_job(job_id)
    if not events:
        raise HTTPException(
            status_code=422,
            detail="No timeline data found — run the full pipeline first",
        )

    # Clear stale plot holes
    deleted = await PlotHoleRepository.delete_by_job(job_id)
    logger.info("[API] rerun_plot_holes job=%s cleared %d stale holes", job_id, deleted)

    # Reset status so the agent can write new results
    await JobRepository.update_status(job_id, "timeline_complete")
    await set_job_status(
        job_id,
        status="timeline_complete",
        current_agent=None,
        completed_agents=["ingestion_agent", "timeline_agent"],
    )

    async def _run_plot_holes() -> None:
        try:
            await plot_hole_agent.ainvoke({"job_id": job_id})
        except Exception:
            logger.exception("[API] rerun_plot_holes job=%s failed", job_id)

    asyncio.create_task(_run_plot_holes())
    logger.info("[API] rerun_plot_holes job=%s dispatched", job_id)
    return {"job_id": job_id, "status": "plot_hole_in_progress"}
