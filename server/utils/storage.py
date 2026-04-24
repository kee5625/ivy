import os

import boto3
from botocore.config import Config


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


def download_pdf(object_key: str) -> bytes:
    """Download PDF bytes from R2 by object key."""
    bucket = os.environ.get("S3_BUCKET", "")
    if not bucket:
        raise RuntimeError("S3_BUCKET not configured")

    client = _get_s3_client()
    response = client.get_object(Bucket=bucket, Key=object_key)
    return response["Body"].read()
