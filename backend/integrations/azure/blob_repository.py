from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from azure.storage.blob import ContentSettings

from integrations.azure.blob_client import (
    create_blob_service_client,
    ensure_container_exists,
    get_blob_container_name,
    get_container_client,
)


def build_pdf_blob_name(filename: str | None = None) -> str:
    suffix = Path(filename or "document.pdf").suffix or ".pdf"
    return f"uploads/{datetime.now(timezone.utc).strftime('%Y/%m/%d')}/{uuid4().hex}{suffix}"


def upload_pdf_bytes(
    pdf_bytes: bytes,
    filename: str | None = None,
    metadata: dict[str, str] | None = None,
) -> dict[str, object]:
    if not isinstance(pdf_bytes, bytes):
        raise TypeError("pdf_bytes must be bytes")
    if not pdf_bytes:
        raise ValueError("pdf_bytes cannot be empty")

    blob_service_client = create_blob_service_client()
    if blob_service_client is None:
        raise RuntimeError("Azure Blob Storage is not configured")

    container_client = get_container_client(blob_service_client)
    ensure_container_exists(container_client)

    blob_name = build_pdf_blob_name(filename)
    blob_client = container_client.get_blob_client(blob_name)

    normalized_metadata = {k: str(v) for k, v in (metadata or {}).items()}
    blob_client.upload_blob(
        pdf_bytes,
        overwrite=True,
        metadata=normalized_metadata,
        content_settings=ContentSettings(content_type="application/pdf"),
    )

    return {
        "container": get_blob_container_name(),
        "blob_name": blob_name,
        "blob_url": blob_client.url,
        "size_bytes": len(pdf_bytes),
    }


def download_blob_bytes(blob_name: str) -> bytes:
    blob_service_client = create_blob_service_client()
    if blob_service_client is None:
        raise RuntimeError("Azure Blob Storage is not configured")

    container_client = get_container_client(blob_service_client)
    blob_client = container_client.get_blob_client(blob_name)
    return blob_client.download_blob().readall()


def delete_blob(blob_name: str) -> None:
    blob_service_client = create_blob_service_client()
    if blob_service_client is None:
        raise RuntimeError("Azure Blob Storage is not configured")

    container_client = get_container_client(blob_service_client)
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.delete_blob(delete_snapshots="include")
