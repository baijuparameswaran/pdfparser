from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple
import json
import os

from .extract import extract_pages
from .ocr import ocr_pages_if_needed
from .structure import build_structure
from .vision import refine_with_vision


@dataclass
class ParseOptions:
    images_dir: Optional[str] = None
    ocr_mode: str = "if-needed"  # "never" | "if-needed" | "always"
    ocr_dpi: int = 300
    use_vision: bool = False
    vision_model: str = "gpt-4o-mini"
    max_pages: Optional[int] = None
    page_range: Optional[str] = None
    verbose: bool = False


def parse_pdf(
    path: str,
    images_dir: Optional[str] = None,
    ocr_mode: str = "if-needed",
    ocr_dpi: int = 300,
    use_vision: bool = False,
    vision_model: str = "gpt-4o-mini",
    max_pages: Optional[int] = None,
    page_range: Optional[str] = None,
    verbose: bool = False,
) -> Dict[str, Any]:
    """Parse a PDF into structured content.

    Returns a dict with keys: meta, pages (each page has blocks and images).
    """
    options = ParseOptions(
        images_dir=images_dir,
        ocr_mode=ocr_mode,
        ocr_dpi=ocr_dpi,
        use_vision=use_vision,
        vision_model=vision_model,
        max_pages=max_pages,
        page_range=page_range,
        verbose=verbose,
    )

    if images_dir:
        os.makedirs(images_dir, exist_ok=True)

    pages, meta = extract_pages(path, images_dir=images_dir, max_pages=max_pages, page_range=page_range, verbose=verbose)

    if ocr_mode in {"if-needed", "always"}:
        pages = ocr_pages_if_needed(path, pages, mode=ocr_mode, dpi=ocr_dpi, verbose=verbose)

    structured = build_structure(pages, verbose=verbose, meta=meta)

    if use_vision:
        try:
            structured = refine_with_vision(structured, model=vision_model, verbose=verbose)
        except Exception as e:
            if verbose:
                print(f"Vision refinement failed: {e}")

    return structured
