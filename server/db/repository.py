from typing import Any
from db.connection import fetch, fetchrow, execute, fetchval


class JobRepository:
    """Repository for job operations."""

    @staticmethod
    async def create(job_id: str, pdf_filename: str, pdf_key: str) -> dict[str, Any]:
        """Create a new job."""
        await execute(
            """
            INSERT INTO jobs (job_id, status, pdf_filename, pdf_key)
            VALUES ($1, 'pending', $2, $3)
            """,
            job_id,
            pdf_filename,
            pdf_key,
        )
        return await JobRepository.get(job_id)

    @staticmethod
    async def get(job_id: str) -> dict[str, Any] | None:
        """Get job by ID."""
        row = await fetchrow("SELECT * FROM jobs WHERE job_id = $1", job_id)
        return dict(row) if row else None

    @staticmethod
    async def update_status(job_id: str, status: str, **kwargs) -> None:
        """Update job status and optional fields."""
        fields = ["status = $2"]
        values = [job_id, status]
        param_idx = 3

        for key, value in kwargs.items():
            fields.append(f"{key} = ${param_idx}")
            values.append(value)
            param_idx += 1

        query = (
            f"UPDATE jobs SET {', '.join(fields)}, updated_at = NOW() WHERE job_id = $1"
        )
        await execute(query, *values)

    @staticmethod
    async def list(limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        """List jobs with pagination."""
        rows = await fetch(
            "SELECT * FROM jobs ORDER BY created_at DESC LIMIT $1 OFFSET $2",
            limit,
            offset,
        )
        return [dict(row) for row in rows]


class ChapterRepository:
    """Repository for chapter operations."""

    @staticmethod
    async def create(
        chapter_id: str,
        job_id: str,
        chapter_num: int,
        title: str | None = None,
        summary: list | None = None,
        key_events: list | None = None,
        characters: list | None = None,
        temporal_markers: list | None = None,
        raw_text: str | None = None,
    ) -> None:
        """Create a new chapter."""
        await execute(
            """
            INSERT INTO chapters (
                chapter_id, job_id, chapter_num, title,
                summary, key_events, characters, temporal_markers, raw_text
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            chapter_id,
            job_id,
            chapter_num,
            title,
            summary or [],
            key_events or [],
            characters or [],
            temporal_markers or [],
            raw_text,
        )

    @staticmethod
    async def get_by_job(job_id: str) -> list[dict[str, Any]]:
        """Get all chapters for a job."""
        rows = await fetch(
            "SELECT * FROM chapters WHERE job_id = $1 ORDER BY chapter_num", job_id
        )
        return [dict(row) for row in rows]


class TimelineRepository:
    """Repository for timeline event operations."""

    @staticmethod
    async def create(
        event_id: str,
        job_id: str,
        description: str,
        chapter_num: int,
        event_order: int,
        **kwargs,
    ) -> None:
        """Create a timeline event."""
        await execute(
            """
            INSERT INTO timeline_events (
                event_id, job_id, description, chapter_num, event_order,
                chapter_title, characters_present, location, causes, caused_by,
                time_reference, inferred_date, inferred_year, relative_time_anchor, confidence
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
            """,
            event_id,
            job_id,
            description,
            chapter_num,
            event_order,
            kwargs.get("chapter_title"),
            kwargs.get("characters_present", []),
            kwargs.get("location"),
            kwargs.get("causes", []),
            kwargs.get("caused_by", []),
            kwargs.get("time_reference"),
            kwargs.get("inferred_date"),
            kwargs.get("inferred_year"),
            kwargs.get("relative_time_anchor"),
            kwargs.get("confidence"),
        )

    @staticmethod
    async def get_by_job(job_id: str) -> list[dict[str, Any]]:
        """Get all timeline events for a job."""
        rows = await fetch(
            "SELECT * FROM timeline_events WHERE job_id = $1 ORDER BY event_order",
            job_id,
        )
        return [dict(row) for row in rows]


class EntityRepository:
    """Repository for entity operations."""

    @staticmethod
    async def get_by_job(job_id: str) -> list[dict[str, Any]]:
        """Get all entities for a job."""
        rows = await fetch(
            "SELECT * FROM entities WHERE job_id = $1 ORDER BY name",
            job_id,
        )
        return [dict(row) for row in rows]


class PlotHoleRepository:
    """Repository for plot hole operations."""

    @staticmethod
    async def delete_by_job(job_id: str) -> int:
        """Delete all plot holes for a job. Returns count deleted."""
        status = await execute("DELETE FROM plot_holes WHERE job_id = $1", job_id)
        try:
            return int(status.split()[-1])
        except (ValueError, IndexError):
            return 0

    @staticmethod
    async def create(
        hole_id: str,
        job_id: str,
        hole_type: str,
        severity: str,
        description: str,
        chapters_involved: list[int],
        characters_involved: list[str],
        events_involved: list[str],
        confidence: float | None,
    ) -> None:
        """Insert a plot hole record."""
        await execute(
            """
            INSERT INTO plot_holes (
                hole_id, job_id, hole_type, severity, description,
                chapters_involved, characters_involved, events_involved, confidence
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """,
            hole_id,
            job_id,
            hole_type,
            severity,
            description,
            chapters_involved,
            characters_involved,
            events_involved,
            confidence,
        )
