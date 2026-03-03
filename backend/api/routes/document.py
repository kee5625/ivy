import logging

from fastapi import APIRouter, File, HTTPException, UploadFile

from integrations.azure.blob_repository import upload_pdf_bytes

logger = logging.getLogger(__name__)
router = APIRouter(tags=["documents"])

@router.post("/pdf/parse")
async def parse_pdf(file: UploadFile = File(...)) -> dict[str, object]:
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=415, detail="Only PDF uploads are supported")

    pdf_bytes = await file.read()
    if not pdf_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    try:
        uploaded = upload_pdf_bytes(pdf_bytes, filename=file.filename)
        logger.info("Upload result: %s", uploaded)
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("PDF parse failed")
        raise HTTPException(status_code=500, detail="Failed to parse PDF") from exc

    return {
        "status": "ok",
        "results": uploaded,
    }
