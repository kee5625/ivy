from __future__ import annotations
from uuid import uui4

from datetime import datetime, timezone
from typing import TypedDict
from uuid import uuid4

from integrations.cosmos.cosmos_client import (
    create_cosmos_client,
    ensure_container_exists,
    get_container_client,
)

# ---Document Shapes---


class JobDocument(TypedDict):
    id: str
    job_id: str
    type: str
    status: str
    current_agent: str
    blob_name: str
    completed_agents: list[str]
    error: str | None
    created_at: str
    updated_at: str

class ChapterDocument(TypedDict):
    id: str
    job_id: str
    type: str
    chapter_num: int
    chapter_title: str
    summary: list[str]
    key_events: list[str]
    characters: list[str]
    raw_text: str

# Helpers

def _now() -> str:
    return datetime.now(timezone.utc).isformat()

def _get_container():
    client = create_cosmos_client()
    if client is None:
        raise RuntimeError("Cosmos DB is not configured — check COSMOS_ACCOUNT_URL")
    container = get_container_client(client)
    ensure_container_exists(container)
    return container
    
# job related

def create_job(blob_name: str) -> str:
    job_id = uuid4().hex
    container = _get_container()
    container.upsert_item({
        "id": job_id,
        "job_id": job_id,
        "type": "job",
        "status": "pending",
        "current_agent": "ingestion_agent",
        "blob_name": blob_name,
        "completed_agents": [],
        "error": None,
        "created_at": _now(),
        "updated_at": _now(),
    })
    return job_id
    
    
def update_job_status(
    job_id: str,
    status: str,
    current_agent: str | None = None,
    completed_agents: list[str] | None = None,
    error: str | None = None,
) -> None:

def get_job(job_id: str) -> JobDocument:
    container = _get_container()
    return container.read_item(item=job_id, partition_key=job_id)
    
# Chapter related

def upsert_chapter(
    job_id: str,
    chapter_num: int,
    chapter_title: str,
    summary: list[str],
    key_events: list[str],
    characters: list[str],
    raw_text: str,
) -> None:
    container = _get_container()
    container.upsert_item({
        "id": f"{job_id}_ch{chapter_num}",
        "job_id": job_id,
        "type": "chapter",
        "chapter_num": chapter_num,
        "chapter_title": chapter_title,
        "summary": summary,
        "key_events": key_events,
        "characters": characters,
        "raw_text": raw_text,
    })
    
def get_chapters(job_id: str) -> list[ChapterDocument]:
    container = _get_container()
    query = "SELECT * FROM c WHERE c.job_id = @job_id AND c.type = 'chapter' ORDER BY c.chapter_num"
    items = container.query_items(
        query=query,
        parameters=[{"name":"@job_id", "value": job_id}],
        partition_key=job_id,
    )
    return list(items)