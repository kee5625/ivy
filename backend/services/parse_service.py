from __future__ import annotations

import io
import re
from typing import TypedDict, Any

import pdfplumber
from pdfplumber.utils import resolve
from integrations.azure.blob_repository import download_blob_bytes

class Bookmark(TypedDict):
    level: int
    title: str
    page_num: int | str
    y_coordinate: float | str


def send_chunks(blob_name: str) -> dict[str, object]:
    pdf_bytes = download_blob_bytes(blob_name)
    return parse_and_clean(pdf_bytes)


def parse_and_clean(pdf_bytes: bytes) -> dict[str, object]:
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        toc = extract_toc(pdf)
        
        if not toc:
            return {"error": "No table of contents found in the PDF."}
        
        start_page = toc[0]["page_num"]
        
        if isinstance(start_page, int):
            text_chunks = []
            for i in range(start_page, len(pdf.pages)):
                page_text = pdf.pages[i].extract_text()
                if page_text:
                    text_chunks.append(page_text)
            
            full_text = "\n".join(text_chunks)
        else:
            full_text = ""

        return {
            "title": "Full Book (Starting at Chapter 1)",
            "text": _normalize_text(full_text),
            "full_toc": toc
        }


def extract_section_text(pdf: pdfplumber.pdf.PDF, toc: list[Bookmark], index: int) -> str:
    """Helper to extract text from a specific TOC section until the next section begins."""
    start_page = toc[index]["page_num"]
    
    # If the page number is unresolved, we can't extract the text
    if not isinstance(start_page, int):
        return ""
        
    end_page = len(pdf.pages)
    
    # If this isn't the last chapter, end the extraction where the next chapter begins
    if index + 1 < len(toc):
        next_page = toc[index + 1]["page_num"]
        if isinstance(next_page, int):
            end_page = next_page

    text_chunks = []
    # Use max() just in case the current and next chapter start on the exact same page
    for i in range(start_page, max(start_page + 1, end_page)):
        if i < len(pdf.pages):
            page_text = pdf.pages[i].extract_text()
            if page_text:
                text_chunks.append(page_text)
                
    return "\n".join(text_chunks)


def extract_toc(pdf: pdfplumber.pdf.PDF) -> list[Bookmark]:
    page_id_to_num = {page.page_obj.objid: i for i, page in enumerate(pdf.pages)}
    
    try:
        outlines = pdf.doc.get_outlines()
    except Exception:
        print("No outlines/bookmarks found in this PDF.")
        return []
        
    bookmarks: list[Bookmark] = []
    
    # Fixed loop variable name
    for outline in outlines:
        level, title, dest, action, se = outline
        
        page_num = "Unknown"
        y_coordinate = "Unknown"
        
        if dest:
            resolved_dest = resolve(dest)
            
            if isinstance(resolved_dest, list) and len(resolved_dest) > 0:
                page_ref = resolved_dest[0]
                
                if hasattr(page_ref, 'objid'):
                    page_num = page_id_to_num.get(page_ref.objid, "Unknown")
                
                if len(resolved_dest) >= 4 and resolved_dest[1].name == 'XYZ':
                    y_coordinate = resolved_dest[3]
        elif action:
            resolved_action = resolve(action)
            if isinstance(resolved_action, dict) and b'D' in resolved_action:
                action_dest = resolve(resolved_action[b'D'])
                if isinstance(action_dest, list) and len(action_dest) > 0:
                    page_ref = action_dest[0]
                    if hasattr(page_ref, 'objid'):
                        page_num = page_id_to_num.get(page_ref.objid, "Unknown")
                        
        bookmarks.append({
            "level": level,
            "title": title,
            "page_num": page_num,
            "y_coordinate": y_coordinate
        })

    return bookmarks


def _normalize_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"-\n(?=[a-z])", "", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()
