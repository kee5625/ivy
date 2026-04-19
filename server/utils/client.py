import os
import typing

from groq import Groq

MODEL="qwen/qwen3-32b"
MAX_CHAPTER_CHARS = 15_000
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2.0

def get_client() -> Groq:
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    return client
    
def ingestion_chat_completion(chapter_chunk: dict) -> dict:
    client = get_client()
    chapter_text = chunk["text"][:MAX_CHAPTER_CHARS]
    
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
    
    response = client.chat.completitions.create(
        messages[
            {
                "role":"user",
                "content": prompt,
            }
        ],
        model = MODEL,
    )
    
    raw_content = response.choices[0].messages.content
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
