from __future__ import annotations

import asyncio
import json
import logging
import os

from integrations.azure.blob_repository import download_blob_bytes
from integrations.cosmos.cosmos_repository import (
    update_job_status,
    upsert_chapter,
)
from pipeline_status import (
    STATUS_FAILED,
    STATUS_INGESTION_COMPLETE,
    STATUS_INGESTION_IN_PROGRESS,
)
from services.parse_service import parse_and_clean

logger = logging.getLogger(__name__)

# Max concurrent OpenAI calls to avoid rate-limit/connection pool errors
# Increased to 5 now that CosmosDB connection leaks are fixed.
_MAX_CONCURRENT_LLM_CALLS = 10

# Max characters of chapter text to send to the LLM per call.
# Reduced to 15,000 to drastically speed up processing and stay well within
# fast latency boundaries while getting the gist of the chapter.
_MAX_CHAPTER_CHARS = 15_000

# Retry configuration
_MAX_RETRIES = 3
_RETRY_BASE_DELAY = 2.0  # seconds, doubles each retry


class IngestionAgent:

    def __init__(self, openai_client, job_id: str):
        self.openai = openai_client
        self.job_id = job_id
        self._semaphore = asyncio.Semaphore(_MAX_CONCURRENT_LLM_CALLS)

    # ── Public entry point ────────────────────────────────────────────────

    async def run(self, blob_name: str) -> str:
        if self.openai is None:
            raise RuntimeError(
                "OpenAI client is not configured. "
                "Set OPENAI_API_KEY in your .env file."
            )
        update_job_status(
            self.job_id,
            status=STATUS_INGESTION_IN_PROGRESS,
            current_agent="ingestion_agent",
        )

        try:
            pdf_bytes = self._download_pdf(blob_name)
            chapters = self._parse_pdf(pdf_bytes)
            logger.info(
                "[IngestionAgent] job=%s  parsed %d chapters",
                self.job_id,
                len(chapters),
            )
            await self._extract_all_chapters(chapters)
            update_job_status(
                self.job_id,
                status=STATUS_INGESTION_COMPLETE,
                current_agent="timeline_agent",
                completed_agents=["ingestion_agent"],
            )
        except Exception as e:
            logger.exception(
                "[IngestionAgent] job=%s  ingestion failed", self.job_id
            )
            update_job_status(self.job_id, status=STATUS_FAILED, error=str(e))
            raise

        return self.job_id

    # ── Download ──────────────────────────────────────────────────────────

    def _download_pdf(self, blob_name: str) -> bytes:
        pdf_bytes = download_blob_bytes(blob_name)
        if not pdf_bytes:
            raise RuntimeError(f"Blob '{blob_name}' was found but is empty")
        return pdf_bytes

    # ── Parse ─────────────────────────────────────────────────────────────

    def _parse_pdf(self, pdf_bytes: bytes) -> list[dict]:
        """
        Returns a list of chapter dicts, each with keys:
            chapter_num, chapter_title, text, start_page, end_page
        """
        result = parse_and_clean(pdf_bytes)
        if "error" in result:
            raise RuntimeError(f"parse_service failed: {result['error']}")

        chapters = result.get("chapters", [])
        if not chapters:
            raise RuntimeError("parse_service returned no chapters")

        return chapters

    # ── LLM extraction (with concurrency control + retry) ─────────────────

    async def _extract_all_chapters(self, chapters: list[dict]) -> list[dict]:
        """Process all chapters with bounded concurrency."""
        tasks = [self._extract_and_save(ch) for ch in chapters]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Log any per-chapter failures but don't abort the whole job
        failures = 0
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                failures += 1
                logger.error(
                    "[IngestionAgent] job=%s  chapter %d failed: %r",
                    self.job_id,
                    i + 1,
                    res,
                )

        if failures == len(chapters):
            raise RuntimeError(
                f"All {failures} chapters failed during LLM extraction"
            )
        if failures:
            logger.warning(
                "[IngestionAgent] job=%s  %d/%d chapters had errors",
                self.job_id,
                failures,
                len(chapters),
            )

        return [r for r in results if not isinstance(r, Exception)]

    async def _extract_and_save(self, chunk: dict) -> dict:
        async with self._semaphore:
            result = await self._extract_chapter_data_with_retry(chunk)

        upsert_chapter(
            job_id=self.job_id,
            chapter_num=result["chapter_num"],
            chapter_title=result["chapter_title"],
            summary=result["summary"],
            key_events=result["key_events"],
            characters=result["characters"],
            raw_text=result["raw_text"],
            temporal_markers=result["temporal_markers"],
        )
        logger.info(
            "[IngestionAgent] job=%s  chapter=%d '%s' saved",
            self.job_id,
            result["chapter_num"],
            result["chapter_title"],
        )
        return result

    async def _extract_chapter_data_with_retry(self, chunk: dict) -> dict:
        """Call the LLM with exponential-backoff retry."""
        last_exc: Exception | None = None
        for attempt in range(1, _MAX_RETRIES + 1):
            try:
                return await self._extract_chapter_data(chunk)
            except Exception as exc:
                last_exc = exc
                if attempt < _MAX_RETRIES:
                    delay = _RETRY_BASE_DELAY * (2 ** (attempt - 1))
                    logger.warning(
                        "[IngestionAgent] job=%s  chapter=%d  attempt %d/%d "
                        "failed (%r), retrying in %.1fs",
                        self.job_id,
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

    async def _extract_chapter_data(self, chunk: dict) -> dict:
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

        response = await self.openai.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            timeout=60.0,
        )

        raw_content = response.choices[0].message.content
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
