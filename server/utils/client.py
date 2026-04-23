import json
import os
from typing import Any

from groq import Groq

MODEL = "qwen/qwen3-32b"
MAX_CHAPTER_CHARS = 15_000
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0


def get_client() -> Groq:
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    return client


def ingestion_chat_completion(chapter_chunk: dict[str, Any]) -> dict[str, Any]:
    client = get_client()
    chapter_text = str(chapter_chunk.get("text", ""))[:MAX_CHAPTER_CHARS]

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
        f"Chapter: {chapter_chunk.get('chapter_title', '')}\n\n"
        f"Text:\n{chapter_text}"
    )

    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model=MODEL,
    )

    raw_content = response.choices[0].message.content or "{}"
    extracted = json.loads(raw_content)

    return {
        "chapter_num": chapter_chunk.get("chapter_num"),
        "chapter_title": chapter_chunk.get("chapter_title", ""),
        "summary": extracted.get("summary", []),
        "key_events": extracted.get("key_events", []),
        "characters": extracted.get("characters", []),
        "temporal_markers": extracted.get("temporal_markers", []),
        "raw_text": chapter_chunk.get("text", ""),
    }


def plot_holes_chat_completion(
    story_state: dict[str, Any],
    attempt: int,
    model_name: str | None = None,
) -> list[dict[str, Any]]:
    _ = attempt
    client = get_client()

    prompt = (
        "You are a conservative fiction continuity analyst.\n"
        "Review the structured story state and return only high-signal plot holes that are directly supported by the provided evidence.\n\n"
        "Allowed hole types:\n"
        "- timeline_paradox: chronology or causality contradicts itself.\n"
        "- location_conflict: the same person or event is placed in incompatible locations at the same time.\n"
        "- dead_character_speaks: a character appears active after a supported death/absence contradiction.\n"
        "- unresolved_setup: the story strongly sets up a concrete thread that remains unresolved by the end of the provided material.\n\n"
        "Rules:\n"
        "1) Be conservative. Return fewer findings rather than speculative ones.\n"
        "2) Return zero findings if the evidence is ambiguous.\n"
        "3) Use only the provided chapters, timeline events, and entities.\n"
        "4) Keep descriptions concise and evidence-based. Mention the contradiction or unresolved setup explicitly.\n"
        "5) `confidence` must reflect how explicit the support is, from 0.0 to 1.0.\n"
        "6) Only use event ids and chapter numbers that exist in the input.\n\n"
        f"Story state:\n{json.dumps(story_state, ensure_ascii=False)}"
    )

    response = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model=model_name or MODEL,
    )

    raw_content = response.choices[0].message.content or "{}"
    parsed = json.loads(raw_content)

    findings: Any
    if isinstance(parsed, dict):
        findings = parsed.get("findings", [])
    elif isinstance(parsed, list):
        findings = parsed
    else:
        findings = []

    if not isinstance(findings, list):
        return []

    return [item for item in findings if isinstance(item, dict)]
