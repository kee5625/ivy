"""Ingestion agent for processing manuscript PDFs into chapters."""

from __future__ import annotations

import asyncio
import logging
import time
import uuid

from langgraph.func import entrypoint, task

from db.repository import ChapterRepository, JobRepository
from services.parse_service import parse_and_clean
from utils.client import ingestion_chat_completion
from utils.job import set_job_status
from utils.storage import download_pdf as fetch_pdf_bytes

logger = logging.getLogger(__name__)

_MAX_CONCURRENT_LLM_CALLS = 10
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 2.0


@task
def download_pdf(object_key: str) -> bytes:
    t0 = time.perf_counter()
    pdf_bytes = fetch_pdf_bytes(object_key)
    if not pdf_bytes:
        raise RuntimeError("PDF download returned empty bytes")
    logger.info(
        "[IngestionAgent] PDF downloaded key=%s size=%.1fKB in %.2fs",
        object_key, len(pdf_bytes) / 1024, time.perf_counter() - t0,
    )
    return pdf_bytes


@task
def parse_pdf(pdf_bytes: bytes) -> list[dict]:
    t0 = time.perf_counter()
    result = parse_and_clean(pdf_bytes)
    if "error" in result:
        raise RuntimeError(f"parse_service failed: {result['error']}")
    chapters = result.get("chapters", [])
    if not chapters:
        raise RuntimeError("parse_service returned no chapters")
    logger.info(
        "[IngestionAgent] PDF parsed → %d chapters in %.2fs",
        len(chapters), time.perf_counter() - t0,
    )
    return chapters


@task
async def extract_all_chapters(job_id: str, chapters: list[dict]) -> list[dict]:
    logger.info(
        "[IngestionAgent] job=%s extracting %d chapters (concurrency=%d)",
        job_id, len(chapters), _MAX_CONCURRENT_LLM_CALLS,
    )
    t0 = time.perf_counter()
    semaphore = asyncio.Semaphore(_MAX_CONCURRENT_LLM_CALLS)

    async def extract_one(chunk: dict) -> dict | Exception:
        try:
            async with semaphore:
                result = await _extract_with_retry(chunk)
            await _save_chapter(job_id, result)
            return result
        except Exception as exc:
            return exc

    results = await asyncio.gather(*[extract_one(ch) for ch in chapters])

    failures = [r for r in results if isinstance(r, Exception)]
    successes = [r for r in results if not isinstance(r, Exception)]

    if len(failures) == len(chapters):
        raise RuntimeError(f"All {len(chapters)} chapters failed LLM extraction")
    if failures:
        logger.warning(
            "[IngestionAgent] job=%s %d/%d chapters failed extraction",
            job_id, len(failures), len(chapters),
        )

    logger.info(
        "[IngestionAgent] job=%s extraction done: %d/%d succeeded in %.2fs",
        job_id, len(successes), len(chapters), time.perf_counter() - t0,
    )
    return successes


async def _extract_with_retry(chunk: dict) -> dict:
    last_exc: Exception | None = None
    chapter_num = chunk.get("chapter_num")
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            result = await asyncio.to_thread(ingestion_chat_completion, chunk)
            logger.info(
                "[IngestionAgent] chapter=%s extracted: %d summary bullets, %d events, %d chars",
                chapter_num,
                len(result.get("summary", [])),
                len(result.get("key_events", [])),
                len(result.get("characters", [])),
            )
            return result
        except Exception as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES:
                delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.warning(
                    "[IngestionAgent] chapter=%s attempt %d/%d failed (%r), retrying in %.1fs",
                    chapter_num, attempt, _MAX_RETRIES, exc, delay,
                )
                await asyncio.sleep(delay)

    raise RuntimeError(
        f"Chapter {chapter_num} failed after {_MAX_RETRIES} attempts: {repr(last_exc)}"
    ) from last_exc


async def _save_chapter(job_id: str, result: dict) -> None:
    await ChapterRepository.create(
        chapter_id=str(uuid.uuid4()),
        job_id=job_id,
        chapter_num=result["chapter_num"],
        title=result["chapter_title"],
        summary=result["summary"],
        key_events=result["key_events"],
        characters=result["characters"],
        temporal_markers=result["temporal_markers"],
        raw_text=result["raw_text"],
    )
    logger.info(
        "[IngestionAgent] job=%s chapter=%d '%s' saved to DB",
        job_id, result["chapter_num"], result["chapter_title"],
    )


@entrypoint()
async def ingestion_agent(inputs: dict) -> str:
    """Download → parse → extract → save."""
    job_id: str = inputs["job_id"]
    pdf_key: str = inputs["pdf_key"]

    logger.info("[IngestionAgent] job=%s starting (key=%s)", job_id, pdf_key)
    t0 = time.perf_counter()

    await _update_status(job_id, status="ingestion_in_progress", current_agent="ingestion_agent")

    try:
        pdf_bytes = await download_pdf(pdf_key)
        chapters = await parse_pdf(pdf_bytes)
        await extract_all_chapters(job_id, chapters)

        elapsed = time.perf_counter() - t0
        logger.info(
            "[IngestionAgent] job=%s COMPLETE: %d chapters ingested in %.2fs",
            job_id, len(chapters), elapsed,
        )

        await _update_status(
            job_id,
            status="ingestion_complete",
            current_agent="timeline_agent",
            completed_agents=["ingestion_agent"],
        )
        return job_id
    except Exception as exc:
        logger.exception(
            "[IngestionAgent] job=%s FAILED after %.2fs: %s",
            job_id, time.perf_counter() - t0, exc,
        )
        await _update_status(job_id, status="failed", error=str(exc))
        raise


async def _update_status(job_id: str, status: str, **kwargs) -> None:
    """Write status to both DB and Redis."""
    logger.debug("[IngestionAgent] job=%s status → %s", job_id, status)
    await JobRepository.update_status(job_id, status=status, **kwargs)
    await set_job_status(
        job_id,
        status=status,
        current_agent=kwargs.get("current_agent"),
        completed_agents=kwargs.get("completed_agents", []),
        error=kwargs.get("error"),
    )
