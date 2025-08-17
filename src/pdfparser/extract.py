from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import fitz  # PyMuPDF
from PIL import Image
import io
import os


def parse_page_range(page_range: Optional[str], page_count: int) -> List[int]:
    if not page_range:
        return list(range(page_count))
    pages = set()
    for part in page_range.split(','):
        part = part.strip()
        if '-' in part:
            start, end = part.split('-', 1)
            s = int(start) - 1
            e = int(end) - 1
            for p in range(max(0, s), min(page_count - 1, e) + 1):
                pages.add(p)
        else:
            p = int(part) - 1
            if 0 <= p < page_count:
                pages.add(p)
    return sorted(pages)


def extract_pages(path: str, images_dir: Optional[str] = None, max_pages: Optional[int] = None, page_range: Optional[str] = None, verbose: bool = False):
    doc = fitz.open(path)
    idxs = parse_page_range(page_range, doc.page_count)
    if not idxs:
        idxs = list(range(doc.page_count))
    if max_pages is not None:
        idxs = idxs[:max_pages]

    pages = []
    for i in idxs:
        page = doc.load_page(i)
        width, height = page.rect.width, page.rect.height
        textpage = page.get_text("dict")
        blocks: List[Dict[str, Any]] = []
        for b in textpage.get("blocks", []):
            if b.get("type", 0) == 0:  # text
                bbox = b.get("bbox")
                text = "\n".join([line.get("spans", [{}])[0].get("text", "") for line in b.get("lines", [])])
                # Collect style info from spans
                spans: List[Dict[str, Any]] = []
                for line in b.get("lines", []):
                    for sp in line.get("spans", []):
                        spans.append({
                            "text": sp.get("text", ""),
                            "size": sp.get("size"),
                            "font": sp.get("font"),
                            "flags": sp.get("flags"),
                            "bbox": sp.get("bbox"),
                        })
                blocks.append({
                    "type": "text",
                    "text": text,
                    "bbox": bbox,
                    "spans": spans,
                })

        images: List[Dict[str, Any]] = []
        for img in page.get_images(full=True):
            xref = img[0]
            pix = fitz.Pixmap(doc, xref)
            if pix.n - pix.alpha >= 4:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            img_bytes = pix.tobytes("png")
            bbox = None  # PyMuPDF doesn't directly provide bbox per image from get_images
            # Optional: derive rough bbox from page.get_image_info (PyMuPDF 1.24+)
            try:
                infos = page.get_image_info(xrefs=[xref])
                if infos:
                    bbox = infos[0].get("bbox")
            except Exception:
                pass
            img_rec = {
                "xref": xref,
                "bbox": bbox,
            }
            if images_dir:
                img_id = f"img_{i+1:04d}_{xref}"
                out_path = os.path.join(images_dir, f"{img_id}.png")
                with open(out_path, "wb") as f:
                    f.write(img_bytes)
                img_rec["path"] = out_path
            images.append(img_rec)

        # Links (URIs and intra-doc links)
        links: List[Dict[str, Any]] = []
        try:
            for lnk in page.get_links():
                uri = lnk.get("uri")
                target = lnk.get("page")
                rect = lnk.get("from")  # Rect
                bbox = [rect.x0, rect.y0, rect.x1, rect.y1] if rect else None
                links.append({
                    "bbox": bbox,
                    "uri": uri,
                    "target_page": (target + 1) if target is not None else None,
                    "text": None,  # could be filled by overlapping text later
                })
        except Exception:
            pass

        pages.append({
            "number": i + 1,
            "width": width,
            "height": height,
            "raw_blocks": blocks,
            "images": images,
            "links": links,
        })
    # Document-level metadata
    md = doc.metadata or {}
    # Table of Contents
    toc = []
    try:
        # PyMuPDF returns toc as list of [level, title, page]
        for level, title, pg, *_ in doc.get_toc(simple=True):
            toc.append({"level": int(level), "title": title, "page": int(pg)})
    except Exception:
        pass

    # Heuristic: detect document title/authors from first page if metadata missing
    detected_title = None
    detected_authors: List[str] = []
    if pages:
        first = pages[0]
        # highest font size block on first page as title candidate
        max_size = -1.0
        best_text = None
        for b in first.get("raw_blocks", []):
            if b.get("type") == "text":
                sizes = [s.get("size") for s in b.get("spans", []) if s.get("size")]
                if sizes:
                    s = max(sizes)
                    t = " ".join(b.get("text", "").split())
                    if s > max_size and len(t) <= 200 and len(t) >= 3:
                        max_size = s
                        best_text = t
        if best_text:
            detected_title = best_text
        # author heuristic: smaller line(s) below title with commas or typical name pattern
        if detected_title:
            # collect blocks just below title bbox
            title_bbox = None
            for b in first.get("raw_blocks", []):
                if " ".join(b.get("text", "").split()) == detected_title:
                    title_bbox = b.get("bbox")
                    break
            if title_bbox:
                y_top = title_bbox[3]
                candidate_lines = []
                for b in first.get("raw_blocks", []):
                    if b.get("type") == "text" and b.get("bbox")[1] >= y_top and b.get("bbox")[1] <= y_top + 120:
                        t = " ".join(b.get("text", "").split())
                        if 2 <= len(t) <= 200:
                            candidate_lines.append(t)
                if candidate_lines:
                    # very simple split by commas/and
                    import re
                    c = candidate_lines[0]
                    names = re.split(r"\s*(?:,| and )\s*", c)
                    detected_authors = [n for n in names if 2 <= len(n) <= 80]

    meta = {
        "title": md.get("title") or detected_title,
        "authors": [a for a in (md.get("author") or "").split(";") if a] or detected_authors,
        "creator": md.get("creator"),
        "producer": md.get("producer"),
        "creationDate": md.get("creationDate"),
        "modDate": md.get("modDate"),
        "pages": len(pages),
        "toc": toc,
    }
    return pages, meta
