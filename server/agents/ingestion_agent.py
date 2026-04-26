"""Ingestion agent for processing manuscript PDFs into chapters."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from typing import Any

from groq import Groq
from langgraph.func import entrypoint, task

from utils.storage import download_pdf as fetch_pdf_bytes
from services.parse_service import parse_and_clean
from db.repository import JobRepository, ChapterRepository

logger = logging.getLogger(__name__)

_MAX_CONCURRENT_LLM_CALLS = 10
_MAX_CHAPTER_CHARS = 15_000
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 2.0


@task
def download_pdf(object_key: str) -> bytes:
    """Download PDF bytes from S3/R2."""
    pdf_bytes = fetch_pdf_bytes(object_key)
    if not pdf_bytes:
        raise RuntimeError("Error downloading pdf.")
    return pdf_bytes


@task
def parse_pdf(pdf_bytes: bytes) -> list[dict]:
    """Parse PDF into chapters."""
    result = parse_and_clean(pdf_bytes)
    if "error" in result:
        raise RuntimeError(f"parse_service failed: {result['error']}")

    chapters = result.get("chapters", [])
    if not chapters:
        raise RuntimeError("parse_service returned no chapters")

    return chapters


@task
async def extract_all_chapters(job_id: str, chapters: list[dict]) -> list[dict]:
    """Extract all chapters with bounded concurrency and per-chapter retry."""
    semaphore = asyncio.Semaphore(_MAX_CONCURRENT_LLM_CALLS)

    async def extract_one(chunk: dict) -> dict | Exception:
        try:
            async with semaphore:
                result = await extract_chapter_data_with_retry(chunk)
            result_saved = await extract_and_save(job_id, result)
            return result_saved
        except Exception as e:
            return e

    tasks = [extract_one(ch) for ch in chapters]
    results = await asyncio.gather(*tasks)

    failures = 0
    for i, res in enumerate(results):
        if isinstance(res, Exception):
            failures += 1
            logger.error(
                "[IngestionAgent] job=%s chapter %d failed: %r",
                job_id,
                i + 1,
                res,
            )

    if failures == len(chapters):
        raise RuntimeError(f"All {failures} chapters failed during LLM extraction")
    if failures:
        logger.warning(
            "[IngestionAgent] job=%s %d/%d chapters had errors",
            job_id,
            failures,
            len(chapters),
        )

    return [r for r in results if not isinstance(r, Exception)]


async def extract_and_save(job_id: str, result: dict) -> dict:
    """Save extracted chapter data to database."""
    chapter_id = str(uuid.uuid4())
    await ChapterRepository.create(
        chapter_id=chapter_id,
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
        "[IngestionAgent] job=%s chapter=%d '%s' saved",
        job_id,
        result["chapter_num"],
        result["chapter_title"],
    )
    return result


async def extract_chapter_data_with_retry(chunk: dict) -> dict:
    """Call LLM with exponential-backoff retry."""
    last_exc: Exception | None = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            return await extract_chapter_data(chunk)
        except Exception as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES:
                delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.warning(
                    "[IngestionAgent] chapter=%d attempt %d/%d failed (%r), "
                    "retrying in %.1fs",
                    chunk["chapter_num"],
                    attempt,
                    _MAX_RETRIES,
                    exc,
                    delay,
                )
                await asyncio.sleep(delay)

    raise RuntimeError(
        f"Chapter {chunk['chapter_num']} failed after {_MAX_RETRIES} "
        f"attempts: {repr(last_exc)}"
    ) from last_exc


async def extract_chapter_data(chunk: dict) -> dict:
    """Extract structured data from chapter text using Groq LLM."""
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    chapter_text = chunk["text"][:_MAX_CHAPTER_CHARS]

    prompt = (
        "You are a literary analyst. Given the following chapter text, extract:\n"
        "1. A strict maximum of 3 short bullets for the summary.\n"
        "2. A strict maximum of 5 key events (each as a short sentence).\n"
        "3. Only the top 10 most important characters mentioned (names only).\n"
        "4. Up to 5 temporal markers (explicit or relative time expressions like years, dates, 'later that night', 'the next morning').\n\n"
        "Respond in JSON with exactly this shape:\n"
        "{\n"
        '  "summary": ["bullet 1", "bullet 2"],\n'
        '  "key_events": ["event 1", "event 2"],\n'
        '  "characters": ["Name1", "Name2"],\n'
        '  "temporal_markers": ["1998", "the next day"]\n'
        "}\n\n"
        f"Chapter: {chunk['chapter_title']}\n\n"
        f"Text:\n{chapter_text}"
    )

    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "qwen/qwen3-32b"),
        messages=[{"role": "user", "content": prompt},],
    )

    raw_content = response.choices[0].message.content or "{}"
    extracted = json.loads(raw_content)

    return {
        "chapter_num": chunk["chapter_num"],
        "chapter_title": chunk["chapter_title"],
        "summary": extracted.get("summary", []),
        "key_events": extracted.get("key_events", []),
        "characters": extracted.get("characters", []),
        "temporal_markers": extracted.get("temporal_markers", []),
        "raw_text": chunk["text"],
    }


@entrypoint()
async def ingestion_agent(job_id: str, pdf_key: str) -> str:
    """Main ingestion workflow: download → parse → extract → save."""
    await JobRepository.update_status(
        job_id,
        status="ingesting",
        current_agent="ingestion_agent",
    )

    try:
        pdf_bytes = download_pdf(pdf_key)
        chapters = parse_pdf(pdf_bytes)
        logger.info(
            "[IngestionAgent] job=%s parsed %d chapters",
            job_id,
            len(chapters),
        )
        await extract_all_chapters(job_id, chapters)
        await JobRepository.update_status(
            job_id,
            status="timeline",
            current_agent="timeline_agent",
            completed_agents=["ingestion_agent"],
        )
        return job_id
    except Exception as e:
        logger.exception("[IngestionAgent] job=%s ingestion failed", job_id)
        await JobRepository.update_status(
            job_id,
            status="failed",
            error=str(e),
        )
        raise
