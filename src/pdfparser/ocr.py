from __future__ import annotations

from typing import Any, Dict, List
import io
import fitz  # PyMuPDF
from PIL import Image
import pytesseract


def has_meaningful_text(page: Dict) -> bool:
    for b in page.get("raw_blocks", []):
        if b.get("type") == "text" and b.get("text", "").strip():
            return True
    return False


def ocr_pages_if_needed(pdf_path: str, pages: List[Dict], mode: str = "if-needed", dpi: int = 300, verbose: bool = False) -> List[Dict]:
    doc = fitz.open(pdf_path)
    new_pages = []
    for page in pages:
        need_ocr = mode == "always" or (mode == "if-needed" and not has_meaningful_text(page))
        if not need_ocr:
            new_pages.append(page)
            continue
        i = page["number"] - 1
        p = doc.load_page(i)
        mat = fitz.Matrix(dpi/72, dpi/72)
        pix = p.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text = pytesseract.image_to_string(img)
        if verbose:
            print(f"OCR page {page['number']}: {len(text.strip())} chars")
        # Add as a single block; structure builder will reflow
        page = {**page, "raw_blocks": page.get("raw_blocks", []) + [{
            "type": "text",
            "text": text,
            "bbox": [0, 0, page["width"], page["height"]],
            "spans": [{"text": text, "size": 10, "font": "OCR", "flags": 0, "bbox": [0,0,page["width"], page["height"]]}]
        }]} 
        new_pages.append(page)
    return new_pages
