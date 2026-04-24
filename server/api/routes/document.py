"""Document upload and processing routes."""

from fastapi import APIRouter
from utils.job import get_job_status

router = APIRouter(tags=["document"])


@router.post("/upload")
async def upload_document():
    """Upload a PDF manuscript."""
    return {"message": "Upload endpoint - not implemented"}


@router.get("/jobs/{job_id}/status")
async def get_job(job_id: str):
    """Get job status and results."""
    job_status = await get_job_status(job_id)
    
    if job_status is None:
        raise HTTPException(status_code=404, detail="Job not Found")
        
    return job_status
