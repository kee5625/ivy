"""Document upload and processing routes."""

from fastapi import APIRouter

router = APIRouter(tags=["document"])


@router.post("/upload")
async def upload_document():
    """Upload a PDF manuscript."""
    return {"message": "Upload endpoint - not implemented"}


@router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    """Get job status and results."""
    return {"job_id": job_id, "status": "not_implemented"}
