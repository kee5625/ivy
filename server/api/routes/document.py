"""Document upload and processing routes."""

from fastapi import APIRouter, HTTPException

from db.repository import JobRepository
from utils.job import get_job_status

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
