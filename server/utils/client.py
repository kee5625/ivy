import json
import logging
import os
import re
import time
from typing import Any

from openai import OpenAI

logger = logging.getLogger(__name__)

MODEL = "gpt-4o-mini"
PLOT_HOLE_MODEL = "gpt-4o"   # plot hole detection needs deeper reasoning
MAX_CHAPTER_CHARS = 15_000

_JSON_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)
_JSON_RESPONSE_FORMAT = {"type": "json_object"}


def get_client() -> OpenAI:
    return OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def _parse_json(raw: str | None) -> Any:
    text = (raw or "").strip()
    if not text:
        return {}
    match = _JSON_FENCE.search(text)
    if match:
        text = match.group(1).strip()
    return json.loads(text)


def _log_llm_call(fn: str, model: str, prompt_len: int, t0: float, usage: Any) -> None:
    elapsed = time.perf_counter() - t0
    if usage:
        logger.info(
            "[LLM] %s model=%s prompt_chars=%d tokens(in=%d out=%d) %.2fs",
            fn, model, prompt_len,
            usage.prompt_tokens, usage.completion_tokens, elapsed,
        )
    else:
        logger.info("[LLM] %s model=%s prompt_chars=%d %.2fs", fn, model, prompt_len, elapsed)


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

    t0 = time.perf_counter()
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=MODEL,
        response_format=_JSON_RESPONSE_FORMAT,
    )
    _log_llm_call("ingestion", MODEL, len(prompt), t0, response.usage)

    extracted = _parse_json(response.choices[0].message.content)

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
        "You are a meticulous fiction continuity analyst. Your job is to find ALL types of "
        "inconsistencies, plot holes, logic gaps, and continuity errors in the story data below.\n\n"
        "HOLE TYPES — use these exact strings:\n"
        "- timeline_paradox        : dates, timing, or causality contradicts itself\n"
        "- location_conflict       : same person/event in incompatible locations at same time\n"
        "- dead_character_speaks   : character active after established death or disappearance\n"
        "- unresolved_setup        : explicit setup (foreshadowing, promise, chekhov gun) never resolved\n"
        "- factual_error           : real-world fact is wrong (biology, physics, math, prices, anatomy)\n"
        "- character_inconsistency : character acts against their established knowledge, memory, or traits\n"
        "- logic_gap               : story logic breaks — easy solution ignored, motivation absent, stakes don't add up\n"
        "- world_inconsistency     : established world rule or lore violated without explanation\n\n"
        "INSTRUCTIONS:\n"
        "1. Be THOROUGH. Flag everything suspicious. It is better to over-report than under-report.\n"
        "2. Do NOT refuse to flag something because it might have an in-universe explanation — "
        "flag it and use a lower confidence score instead.\n"
        "3. Cross-reference chapters explicitly: if a fact in chapter 3 contradicts chapter 7, flag it.\n"
        "4. Pay close attention to `raw_text_excerpt` fields — these contain actual quoted text with "
        "specific details (prices, physical descriptions, dates, dialogue) that reveal factual errors.\n"
        "5. `confidence` range: 0.5 = plausible issue, 0.75 = likely issue, 0.9+ = clear contradiction.\n"
        "6. `chapters_involved` and `events_involved` must only contain values present in the input.\n\n"
        'Respond in JSON: {"findings": [{"hole_type": ..., "severity": ..., "description": ..., '
        '"chapters_involved": [...], "characters_involved": [...], "events_involved": [...], "confidence": ...}]}\n\n'
        f"Story state:\n{json.dumps(story_state, ensure_ascii=False)}"
    )

    t0 = time.perf_counter()
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=model_name or PLOT_HOLE_MODEL,
        response_format=_JSON_RESPONSE_FORMAT,
    )
    _log_llm_call("plot_holes", model_name or PLOT_HOLE_MODEL, len(prompt), t0, response.usage)

    parsed = _parse_json(response.choices[0].message.content)

    if isinstance(parsed, dict):
        findings = parsed.get("findings", [])
    elif isinstance(parsed, list):
        findings = parsed
    else:
        findings = []

    if not isinstance(findings, list):
        return []

    return [item for item in findings if isinstance(item, dict)]


def timeline_chat_completion(payload: dict[str, Any]) -> list[dict[str, Any]]:
    client = get_client()

    prompt = (
        "You are a narrative analyst working on one chapter only.\n"
        "Using only the provided chapter data, produce a small ordered list of the most important events in this chapter.\n\n"
        "Requirements:\n"
        "1) Return at most 4 events.\n"
        "2) Keep each event short, concrete, and chapter-local.\n"
        "3) Preserve order within the chapter only.\n"
        "4) Do not invent events unsupported by the chapter data.\n"
        "5) `characters_present` should contain names/slugs only.\n"
        "6) `time_reference` should be null unless the chapter data provides one.\n"
        "7) `confidence` must be between 0.0 and 1.0.\n\n"
        'Respond in JSON: {"events": [{"description": ..., "characters_present": [...], "location": ..., "time_reference": ..., "confidence": ...}]}\n\n'
        f"Chapter data:\n{json.dumps(payload, ensure_ascii=False)}"
    )

    t0 = time.perf_counter()
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=MODEL,
        response_format=_JSON_RESPONSE_FORMAT,
    )
    _log_llm_call("timeline", MODEL, len(prompt), t0, response.usage)

    parsed = _parse_json(response.choices[0].message.content)
    raw_events = parsed.get("events", [])

    if not isinstance(raw_events, list):
        raise RuntimeError("Timeline output invalid: 'events' is not a list")

    return raw_events


def merge_timeline_chat_completion(payload: list[dict[str, Any]]) -> list[dict[str, Any]]:
    client = get_client()

    prompt = (
        "You are a narrative timeline analyst.\n"
        "Merge this batch of chapter-local events into one ordered story sub-timeline.\n\n"
        "Requirements:\n"
        "1) Every `source_event_id` from the input must appear exactly once in the output.\n"
        "2) Order only the events provided in this batch.\n"
        "3) Preserve narrative causality when setting `causes` and `caused_by`.\n"
        "4) Use `source_event_id` values from the input when referencing related events.\n"
        "5) `relative_time_anchor_event_id` must be null or one input `source_event_id`.\n"
        "6) Keep events concise and do not invent unsupported specifics.\n"
        "7) `confidence` must stay between 0.0 and 1.0.\n\n"
        'Respond in JSON: {"events": [{"source_event_id": ..., "description": ..., '
        '"chapter_num": ..., "chapter_title": ..., "order": ..., '
        '"characters_present": [...], "location": ..., "causes": [...], '
        '"caused_by": [...], "time_reference": ..., "inferred_date": ..., '
        '"inferred_year": ..., "relative_time_anchor_event_id": ..., "confidence": ...}]}\n\n'
        f"Input local events:\n{json.dumps(payload, ensure_ascii=False)}"
    )

    t0 = time.perf_counter()
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=MODEL,
        response_format=_JSON_RESPONSE_FORMAT,
    )
    _log_llm_call("merge_timeline", MODEL, len(prompt), t0, response.usage)

    parsed = _parse_json(response.choices[0].message.content)
    raw_events = parsed.get("events", [])

    if not isinstance(raw_events, list):
        raise RuntimeError("Merge output invalid: 'events' is not a list")

    return raw_events


def final_order_chat_completion(payload: list[dict[str, Any]]) -> list[str]:
    client = get_client()

    prompt = (
        "You are a narrative chronology analyst.\n"
        "Return the globally ordered list of source event ids for the provided events.\n\n"
        "Requirements:\n"
        "1) Every `source_event_id` must appear exactly once.\n"
        "2) Preserve the most plausible global chronology across batches.\n"
        "3) Return only the ordered ids, do not rewrite event content.\n\n"
        'Respond in JSON: {"ordered_source_event_ids": ["id1", "id2", ...]}\n\n'
        f"Input events:\n{json.dumps(payload, ensure_ascii=False)}"
    )

    t0 = time.perf_counter()
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model=MODEL,
        response_format=_JSON_RESPONSE_FORMAT,
    )
    _log_llm_call("final_order", MODEL, len(prompt), t0, response.usage)

    parsed = _parse_json(response.choices[0].message.content)
    ordered_ids = parsed.get("ordered_source_event_ids", [])

    if not isinstance(ordered_ids, list):
        raise RuntimeError("Final order output invalid: 'ordered_source_event_ids' is not a list")

    return [str(i) for i in ordered_ids if isinstance(i, str)]
