from __future__ import annotations


def _chunk_text(
    text: str, chunk_size: int = 800, chunk_overlap: int = 100
) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")

    if not text:
        return []

    step = chunk_size - chunk_overlap
    chunks: list[str] = []
    for start in range(0, len(text), step):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
    return chunks


def parse_pdf_bytes(pdf_bytes: bytes, filename: str | None = None) -> dict[str, object]:
    if not isinstance(pdf_bytes, bytes):
        raise TypeError("pdf_bytes must be bytes")
    if not pdf_bytes:
        raise ValueError("Uploaded PDF is empty")

    # Placeholder extraction logic until a real PDF parser is integrated.
    extracted_text = f"Placeholder extracted content from {filename or 'uploaded.pdf'}"
    chunks = _chunk_text(extracted_text)

    return {
        "filename": filename or "uploaded.pdf",
        "byte_size": len(pdf_bytes),
        "page_count": None,
        "chunks": chunks,
        "metadata": {
            "parser": "placeholder",
            "chunk_size": 800,
            "chunk_overlap": 100,
        },
    }
