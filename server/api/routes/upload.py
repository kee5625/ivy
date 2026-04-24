import os
import re
import uuid
from datetime import datetime, timezone

import boto3
from botocore.config import Config
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

_PRESIGN_EXPIRES_SECONDS = 300


def _get_s3_client():
    endpoint = os.environ.get("S3_ENDPOINT", "")
    access_key = os.environ.get("S3_ACCESS_KEY", "")
    secret_key = os.environ.get("S3_SECRET_KEY", "")
    region = os.environ.get("S3_REGION", "auto")

    if not endpoint or not access_key or not secret_key:
        raise RuntimeError("S3_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY must be set")

    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
        config=Config(signature_version="s3v4"),
    )


def _sanitize_filename(filename: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9._-]", "", filename.strip().lower().replace(" ", "-")))


def _make_object_key(filename: str) -> str:
    now = datetime.now(timezone.utc)
    safe = _sanitize_filename(filename)
    return f"uploads/{now.year}/{now.month:02d}/{now.day:02d}/{uuid.uuid4()}-{safe}"


class PresignRequest(BaseModel):
    filename: str
    content_type: str = "application/pdf"
    size: int


class PresignResponse(BaseModel):
    presigned_url: str
    object_key: str


@router.post("/presign", response_model=PresignResponse)
def presign_upload(body: PresignRequest) -> PresignResponse:
    bucket = os.environ.get("S3_BUCKET", "")
    if not bucket:
        raise HTTPException(status_code=500, detail="S3_BUCKET not configured")

    try:
        client = _get_s3_client()
        object_key = _make_object_key(body.filename)
        presigned_url = client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": bucket,
                "Key": object_key,
                "ContentType": body.content_type,
            },
            ExpiresIn=_PRESIGN_EXPIRES_SECONDS,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return PresignResponse(presigned_url=presigned_url, object_key=object_key)
