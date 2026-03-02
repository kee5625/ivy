from __future__ import annotations

import io
from typing import TypedDict

import pdfplumber
from pdfplumber.utils import resolve
from integrations.azure.blob_repository import download_blob_bytes



def send_chunks(blob_name: str) -> dict[str, object]:
    pdf_bytes = download_blob_bytes(blob_name)
    return parse_and_clean(pdf_bytes)


def parse_and_clean(pdf_bytes: bytes) -> dict[str, object]:
    toc = extract_toc(pdf_bytes)
    
    return {
    }

def extract_toc(pdf_bytes: bytes):
    with pdfplumber.open(pdf_bytes) as pdf:
        page_id_to_num = {page.page_obj.objid: i for i, page in enumerate(pdf.pages)}
        
        try:
            outlines = pdf.doc.get_outlines()
        except Exception:
            print("No outlines/bookmars found in this PDF.")
            return
            
        print("Table of Contents:\n")
        
        for outline in outline:
            level, title, dest, action, se = outline
            indent = " " + (level - 1)
            
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
                            
            print(f"{indent}- {title}")
            print(f"{indent}  -> Jumps to Page: {page_num} (Y-Coord: {y_coordinate})")

def _normalize_text(text: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"-\n(?=[a-z])", "", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()

