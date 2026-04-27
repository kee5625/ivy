import os
import re
import uuid
from datetime import datetime, timezone

import boto3
from botocore.config import Config

_PRESIGN_EXPIRES_SECONDS = 300


def get_s3_client():
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


def get_bucket() -> str:
    bucket = os.environ.get("S3_BUCKET", "")
    if not bucket:
        raise RuntimeError("S3_BUCKET not configured")
    return bucket


def sanitize_filename(filename: str) -> str:
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9._-]", "", filename.strip().lower().replace(" ", "-")))


def make_object_key(filename: str) -> str:
    now = datetime.now(timezone.utc)
    safe = sanitize_filename(filename)
    return f"uploads/{now.year}/{now.month:02d}/{now.day:02d}/{uuid.uuid4()}-{safe}"


def presign_put(object_key: str, content_type: str = "application/pdf") -> str:
    """Generate presigned PUT URL for direct browser upload."""
    client = get_s3_client()
    return client.generate_presigned_url(
        "put_object",
        Params={"Bucket": get_bucket(), "Key": object_key, "ContentType": content_type},
        ExpiresIn=_PRESIGN_EXPIRES_SECONDS,
    )


def download_pdf(object_key: str) -> bytes:
    """Download PDF bytes from R2."""
    client = get_s3_client()
    response = client.get_object(Bucket=get_bucket(), Key=object_key)
    return response["Body"].read()
