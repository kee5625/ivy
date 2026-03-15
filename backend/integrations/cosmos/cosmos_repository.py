from __future__ import annotations

from datetime import datetime, timezone
from typing import TypedDict
from uuid import uuid4

from integrations.cosmos.cosmos_client import (
    create_cosmos_client,
    ensure_container_exists,
    get_container_client,
)


# ── Document Shapes ───────────────────────────────────────────────────────────

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
    temporal_markers: list[str]
    raw_text: str


class EntityDocument(TypedDict):
    id: str
    job_id: str
    type: str                    # always "entity"
    entity_id: str               # slugified name e.g. "harry_potter"
    name: str                    # display name e.g. "Harry Potter"
    entity_type: str             # "character" | "location" | "object"
    appears_in_chapters: list[int]
    traits: list[str]
    aliases: list[str]           # e.g. ["Mr Potter", "The Boy Who Lived"]
    role: str                    # "protagonist" | "antagonist" | "minor"


class TimelineEventDocument(TypedDict):
    id: str
    job_id: str
    type: str                    # always "timeline_event"
    event_id: str                # e.g. "evt_001"
    description: str
    chapter_num: int
    chapter_title: str
    order: int                   # global chronological order across all chapters
    characters_present: list[str]  # entity_ids
    location: str | None         # entity_id of location
    causes: list[str]            # event_ids this event directly causes
    caused_by: list[str]         # event_ids that caused this event
    time_reference: str | None   # e.g. "three days later", "that evening"
    inferred_date: str | None    # e.g. "1998-06-12" when confidently inferable
    inferred_year: int | None
    relative_time_anchor: str | None  # e.g. "after evt_003"
    confidence: float | None


class PlotHoleDocument(TypedDict):
    id: str
    job_id: str
    type: str                    # always "plot_hole"
    hole_id: str
    hole_type: str               # "dead_character_speaks" | "location_conflict" |
                                 # "timeline_paradox" | "unresolved_setup"
    severity: str                # "high" | "medium" | "low"
    description: str
    chapters_involved: list[int]
    characters_involved: list[str]  # entity_ids
    events_involved: list[str]      # event_ids


# ── Helpers ───────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_container():
    client = create_cosmos_client()
    if client is None:
        raise RuntimeError("Cosmos DB is not configured — check COSMOS_ACCOUNT_URL")
    container = get_container_client(client)
    ensure_container_exists(container)
    return container


# ── Job operations ────────────────────────────────────────────────────────────

def create_job(blob_name: str) -> str:
    """Create a new job document. Returns the job_id."""
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
    """Patch a job document with new status and agent progress."""
    container = _get_container()
    patch_ops = [
        {"op": "replace", "path": "/status", "value": status},
        {"op": "replace", "path": "/updated_at", "value": _now()},
    ]
    if current_agent is not None:
        patch_ops.append({"op": "replace", "path": "/current_agent", "value": current_agent})
    if completed_agents is not None:
        patch_ops.append({"op": "replace", "path": "/completed_agents", "value": completed_agents})
    if error is not None:
        patch_ops.append({"op": "replace", "path": "/error", "value": error})

    container.patch_item(item=job_id, partition_key=job_id, patch_operations=patch_ops)


def get_job(job_id: str) -> JobDocument:
    """Fetch a job document by job_id."""
    container = _get_container()
    return container.read_item(item=job_id, partition_key=job_id)


# ── Chapter operations ────────────────────────────────────────────────────────

def upsert_chapter(
    job_id: str,
    chapter_num: int,
    chapter_title: str,
    summary: list[str],
    key_events: list[str],
    characters: list[str],
    raw_text: str,
    temporal_markers: list[str] | None = None,
) -> None:
    """Write a single chapter's extracted data. Called as each chapter finishes."""
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
        "temporal_markers": temporal_markers or [],
        "raw_text": raw_text,
    })


def get_chapters(job_id: str) -> list[ChapterDocument]:
    """Fetch all chapters for a job, ordered by chapter number."""
    container = _get_container()
    query = (
        "SELECT * FROM c "
        "WHERE c.job_id = @job_id AND c.type = 'chapter' "
        "ORDER BY c.chapter_num"
    )
    items = container.query_items(
        query=query,
        parameters=[{"name": "@job_id", "value": job_id}],
        partition_key=job_id,
    )
    return list(items)


def get_chapter(job_id: str, chapter_num: int) -> ChapterDocument:
    """Fetch a single chapter by number."""
    container = _get_container()
    return container.read_item(
        item=f"{job_id}_ch{chapter_num}",
        partition_key=job_id,
    )


# ── Entity operations ─────────────────────────────────────────────────────────

def upsert_entity(
    job_id: str,
    entity_id: str,
    name: str,
    entity_type: str,
    appears_in_chapters: list[int],
    traits: list[str],
    aliases: list[str] | None = None,
    role: str = "minor",
) -> None:
    """Write a character, location, or object found by the entity agent."""
    container = _get_container()
    container.upsert_item({
        "id": f"{job_id}_entity_{entity_id}",
        "job_id": job_id,
        "type": "entity",
        "entity_id": entity_id,
        "name": name,
        "entity_type": entity_type,
        "appears_in_chapters": appears_in_chapters,
        "traits": traits,
        "aliases": aliases or [],
        "role": role,
    })


def get_entities(
    job_id: str,
    entity_type: str | None = None,
) -> list[EntityDocument]:
    """
    Fetch all entities for a job.
    Optionally filter by entity_type: 'character' | 'location' | 'object'
    """
    container = _get_container()
    if entity_type:
        query = (
            "SELECT * FROM c "
            "WHERE c.job_id = @job_id AND c.type = 'entity' AND c.entity_type = @entity_type "
            "ORDER BY c.name"
        )
        params = [
            {"name": "@job_id", "value": job_id},
            {"name": "@entity_type", "value": entity_type},
        ]
    else:
        query = (
            "SELECT * FROM c "
            "WHERE c.job_id = @job_id AND c.type = 'entity' "
            "ORDER BY c.name"
        )
        params = [{"name": "@job_id", "value": job_id}]

    items = container.query_items(
        query=query,
        parameters=params,
        partition_key=job_id,
    )
    return list(items)


# ── Timeline operations ───────────────────────────────────────────────────────

def upsert_timeline_event(
    job_id: str,
    event_id: str,
    description: str,
    chapter_num: int,
    order: int,
    characters_present: list[str],
    causes: list[str] | None = None,
    caused_by: list[str] | None = None,
    location: str | None = None,
    time_reference: str | None = None,
    chapter_title: str | None = None,
    inferred_date: str | None = None,
    inferred_year: int | None = None,
    relative_time_anchor: str | None = None,
    confidence: float | None = None,
) -> None:
    """Write a single timeline event found by the timeline agent."""
    container = _get_container()
    container.upsert_item({
        "id": f"{job_id}_evt_{event_id}",
        "job_id": job_id,
        "type": "timeline_event",
        "event_id": event_id,
        "description": description,
        "chapter_num": chapter_num,
        "chapter_title": chapter_title or "",
        "order": order,
        "characters_present": characters_present,
        "location": location,
        "causes": causes or [],
        "caused_by": caused_by or [],
        "time_reference": time_reference,
        "inferred_date": inferred_date,
        "inferred_year": inferred_year,
        "relative_time_anchor": relative_time_anchor,
        "confidence": confidence,
    })


def get_timeline_events(job_id: str) -> list[TimelineEventDocument]:
    """Fetch all timeline events for a job, in chronological order."""
    container = _get_container()
    query = (
        "SELECT * FROM c "
        "WHERE c.job_id = @job_id AND c.type = 'timeline_event' "
        "ORDER BY c[\"order\"]"
    )
    items = container.query_items(
        query=query,
        parameters=[{"name": "@job_id", "value": job_id}],
        partition_key=job_id,
    )
    return list(items)


def get_timeline_events_for_chapter(
    job_id: str,
    chapter_num: int,
) -> list[TimelineEventDocument]:
    """Fetch all timeline events for a specific chapter."""
    container = _get_container()
    query = (
        "SELECT * FROM c "
        "WHERE c.job_id = @job_id AND c.type = 'timeline_event' AND c.chapter_num = @chapter_num "
        "ORDER BY c[\"order\"]"
    )
    items = container.query_items(
        query=query,
        parameters=[
            {"name": "@job_id", "value": job_id},
            {"name": "@chapter_num", "value": chapter_num},
        ],
        partition_key=job_id,
    )
    return list(items)


# ── Plot hole operations ──────────────────────────────────────────────────────

def upsert_plot_hole(
    job_id: str,
    hole_type: str,
    severity: str,
    description: str,
    chapters_involved: list[int],
    characters_involved: list[str] | None = None,
    events_involved: list[str] | None = None,
) -> None:
    """Write a single plot hole found by the plot hole agent."""
    hole_id = uuid4().hex[:8]
    container = _get_container()
    container.upsert_item({
        "id": f"{job_id}_hole_{hole_id}",
        "job_id": job_id,
        "type": "plot_hole",
        "hole_id": hole_id,
        "hole_type": hole_type,
        "severity": severity,
        "description": description,
        "chapters_involved": chapters_involved,
        "characters_involved": characters_involved or [],
        "events_involved": events_involved or [],
    })


def get_plot_holes(
    job_id: str,
    severity: str | None = None,
) -> list[PlotHoleDocument]:
    """
    Fetch all plot holes for a job.
    Optionally filter by severity: 'high' | 'medium' | 'low'
    """
    container = _get_container()
    if severity:
        query = (
            "SELECT * FROM c "
            "WHERE c.job_id = @job_id AND c.type = 'plot_hole' AND c.severity = @severity"
        )
        params = [
            {"name": "@job_id", "value": job_id},
            {"name": "@severity", "value": severity},
        ]
    else:
        query = (
            "SELECT * FROM c "
            "WHERE c.job_id = @job_id AND c.type = 'plot_hole'"
        )
        params = [{"name": "@job_id", "value": job_id}]

    items = container.query_items(
        query=query,
        parameters=params,
        partition_key=job_id,
    )
    return list(items)


# ── Cross-cutting queries ─────────────────────────────────────────────────────

def get_full_job_state(job_id: str) -> dict:
    """
    Fetch everything for a job in one call.
    Used by agents to load full pipeline state, and by the frontend for the final result.
    """
    return {
        "job": get_job(job_id),
        "chapters": get_chapters(job_id),
        "entities": get_entities(job_id),
        "timeline": get_timeline_events(job_id),
        "plot_holes": get_plot_holes(job_id),
    }
