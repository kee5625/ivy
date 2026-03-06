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
from services.parse_service import Bookmark, parse_and_clean

logger = logging.getLogger(__name__)



class IngestionAgent:

    def __init__(self, openai_client, job_id: str):
        self.openai = openai_client
        self.job_id = job_id

    async def run(self, blob_name: str) -> str:
        if self.openai is None:
            raise RuntimeError(
                "OpenAI client is not configured. "
                "Set OPENAI_ENDPOINT + PROJECT_KEY in your .env file."
            )
        update_job_status(self.job_id, status="in_progress", current_agent="ingestion_agent")

        try:
            pdf_bytes = self._download_pdf(blob_name)
            raw_text, toc = self._parse_pdf(pdf_bytes)
            chunks = self._chunk_by_chapter(raw_text, toc)
            await self._extract_all_chapters(chunks)
            update_job_status(
                self.job_id,
                status="ingestion_complete",
                current_agent="entity_agent",
                completed_agents=["ingestion_agent"],
            )
        except Exception as e:
            update_job_status(self.job_id, status="failed", error=str(e))
            raise

        return self.job_id

    def _download_pdf(self, blob_name: str) -> bytes:
        pdf_bytes = download_blob_bytes(blob_name)
        if not pdf_bytes:
            raise RuntimeError(f"Blob '{blob_name}' was found but is empty")
        return pdf_bytes

    def _parse_pdf(self, pdf_bytes: bytes) -> tuple[str, list[Bookmark]]:
        result = parse_and_clean(pdf_bytes)
        if "error" in result:
            raise RuntimeError(f"parse_service failed: {result['error']}")
        return result["text"], result["full_toc"]

    def _chunk_by_chapter(self, raw_text: str, toc: list[Bookmark]) -> list[dict]:
        chunks = []

        chapter_toc = [t for t in toc if isinstance(t["page_num"], int)]

        for i, entry in enumerate(chapter_toc):
            title = entry["title"]
            start_idx = raw_text.find(title)
            if start_idx == -1:
                continue

            end_idx = len(raw_text)
            if i + 1 < len(chapter_toc):
                next_title = chapter_toc[i + 1]["title"]
                next_idx = raw_text.find(next_title, start_idx + len(title))
                if next_idx != -1:
                    end_idx = next_idx

            chunks.append({
                "chapter_num": i + 1,
                "chapter_title": title,
                "text": raw_text[start_idx:end_idx].strip(),
            })

        if not chunks:
            chunks = [{"chapter_num": 1, "chapter_title": "Full Text", "text": raw_text}]

        return chunks

    async def _extract_all_chapters(self, chunks: list[dict]) -> list[dict]:
        tasks = [self._extract_and_save(chunk) for chunk in chunks]
        return await asyncio.gather(*tasks)

    async def _extract_and_save(self, chunk: dict) -> dict:
        result = await self._extract_chapter_data(chunk)
        upsert_chapter(
            job_id=self.job_id,
            chapter_num=result["chapter_num"],
            chapter_title=result["chapter_title"],
            summary=result["summary"],
            key_events=result["key_events"],
            characters=result["characters"],
            raw_text=result["raw_text"],
        )
        logger.info(
            "[IngestionAgent] job=%s chapter=%d saved",
            self.job_id,
            result["chapter_num"],
        )
        return result

    async def _extract_chapter_data(self, chunk: dict) -> dict:
        prompt = f"""You are a literary analyst. Given the following chapter text, extract:
        1. A 3-5 bullet summary of the chapter
        2. A list of key events (each as a short sentence)
        3. Every character mentioned (names only)

        Respond in JSON with exactly this shape:
        {{
        "summary": ["bullet 1", "bullet 2"],
        "key_events": ["event 1", "event 2"],
        "characters": ["Name1", "Name2"]
        }}

        Chapter: {chunk['chapter_title']}

        Text:
        {chunk['text'][:8000]}"""

        response = await self.openai.chat.completions.create(
            model=os.getenv("OPENAI_DEPLOYMENT", "gpt-4o-mini"),
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )

        extracted = json.loads(response.choices[0].message.content)

        return {
            "chapter_num": chunk["chapter_num"],
            "chapter_title": chunk["chapter_title"],
            "summary": extracted.get("summary", []),
            "key_events": extracted.get("key_events", []),
            "characters": extracted.get("characters", []),
            "raw_text": chunk["text"],
        }
