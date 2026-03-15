from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, Request, UploadFile

from agents.ingestion_agent import IngestionAgent
from agents.timeline_agent import TimelineAgent
from integrations.azure.blob_repository import upload_pdf_bytes
from integrations.cosmos.cosmos_repository import create_job

logger = logging.getLogger(__name__)
router = APIRouter(tags=["documents"])


async def _run_ingestion(openai_client, job_id: str, blob_name: str) -> None:
    try:
        ingestion_agent = IngestionAgent(openai_client=openai_client, job_id=job_id)
        await ingestion_agent.run(blob_name)

        timeline_agent = TimelineAgent(openai_client=openai_client, job_id=job_id)
        await timeline_agent.run()
    except Exception:
        import traceback, sys
        traceback.print_exc(file=sys.stderr)
        logger.exception("[_run_ingestion] background task failed for job=%s", job_id)


@router.post("/pdf/upload")
async def upload_pdf(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
) -> dict[str, object]:
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=415, detail="Only PDF uploads are supported")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    # 1. Upload PDF to Blob Storage
    try:
        uploaded = upload_pdf_bytes(pdf_bytes, filename=file.filename)
        logger.info("Uploaded blob: %s", uploaded["blob_name"])
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Blob upload failed")
        raise HTTPException(status_code=500, detail="Failed to upload PDF") from exc

    # 2. Create job in Cosmos -- returns job_id immediately
    try:
        job_id = create_job(blob_name=uploaded["blob_name"])
        logger.info("Created job: %s", job_id)
    except Exception as exc:
        logger.exception("Job creation failed")
        raise HTTPException(status_code=500, detail="Failed to create job") from exc

    # 3. Fire ingestion agent in the background -- route returns immediately
    openai_client = request.app.state.openai_client
    background_tasks.add_task(_run_ingestion, openai_client, job_id, uploaded["blob_name"])
    logger.info("Ingestion agent queued for job: %s", job_id)

    return {
        "status": "accepted",
        "job_id": job_id,
        "blob_name": uploaded["blob_name"],
        "blob_url": uploaded["blob_url"],
    }


@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str) -> dict[str, object]:
    from integrations.cosmos.cosmos_repository import get_job
    try:
        job = get_job(job_id)
    except Exception as exc:
        logger.exception("Failed to fetch job %s", job_id)
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found") from exc

    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "current_agent": job["current_agent"],
        "completed_agents": job["completed_agents"],
        "error": job.get("error"),
        "created_at": job["created_at"],
        "updated_at": job["updated_at"],
    }


@router.get("/jobs/{job_id}/chapters")
async def get_job_chapters(job_id: str) -> dict[str, object]:
    from integrations.cosmos.cosmos_repository import get_chapters
    try:
        chapters = get_chapters(job_id)
    except Exception as exc:
        logger.exception("Failed to fetch chapters for job %s", job_id)
        raise HTTPException(status_code=500, detail="Failed to fetch chapters") from exc

    return {
        "job_id": job_id,
        "chapter_count": len(chapters),
        "chapters": [
            {
                "chapter_num": ch["chapter_num"],
                "chapter_title": ch["chapter_title"],
                "summary": ch["summary"],
                "key_events": ch["key_events"],
                "characters": ch["characters"],
            }
            for ch in chapters
        ],
    }


@router.get("/jobs/{job_id}/timeline")
async def get_job_timeline(job_id: str) -> dict[str, object]:
    from integrations.cosmos.cosmos_repository import get_timeline_events
    try:
        timeline_events = get_timeline_events(job_id)
    except Exception as exc:
        logger.exception("Failed to fetch timeline for job %s", job_id)
        raise HTTPException(status_code=500, detail="Failed to fetch timeline events") from exc

    return {
        "job_id": job_id,
        "timeline_event_count": len(timeline_events),
        "timeline_events": [
            {
                "event_id": evt["event_id"],
                "description": evt["description"],
                "chapter_num": evt["chapter_num"],
                "chapter_title": evt.get("chapter_title", ""),
                "order": evt["order"],
                "characters_present": evt.get("characters_present", []),
                "location": evt.get("location"),
                "causes": evt.get("causes", []),
                "caused_by": evt.get("caused_by", []),
                "time_reference": evt.get("time_reference"),
                "inferred_date": evt.get("inferred_date"),
                "inferred_year": evt.get("inferred_year"),
                "relative_time_anchor": evt.get("relative_time_anchor"),
                "confidence": evt.get("confidence"),
            }
            for evt in timeline_events
        ],
    }
