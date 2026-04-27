from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from utils.storage import get_s3_client, get_bucket, make_object_key, presign_put

router = APIRouter()


class PresignRequest(BaseModel):
    filename: str
    content_type: str = "application/pdf"
    size: int


class PresignResponse(BaseModel):
    presigned_url: str
    object_key: str


@router.post("/presign", response_model=PresignResponse)
def presign_upload(body: PresignRequest) -> PresignResponse:
    try:
        object_key = make_object_key(body.filename)
        presigned_url = presign_put(object_key, body.content_type)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return PresignResponse(presigned_url=presigned_url, object_key=object_key)
