from __future__ import annotations

from typing import Any, Dict, List, Optional
import math


def median(nums: List[float]) -> float:
    s = sorted(nums)
    n = len(s)
    if n == 0:
        return 0.0
    if n % 2 == 1:
        return float(s[n//2])
    return float((s[n//2 - 1] + s[n//2]) / 2)


def guess_heading_level(size: float, size_median: float) -> Optional[int]:
    # Simple heuristic: larger than median -> heading; scale to levels
    if size >= size_median * 1.6:
        return 1
    if size >= size_median * 1.35:
        return 2
    if size >= size_median * 1.2:
        return 3
    return None


def build_structure(pages: List[Dict], verbose: bool = False, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    structured_pages = []
    for page in pages:
        blocks = []
        sizes = []
        for rb in page.get("raw_blocks", []):
            if rb.get("type") != "text":
                continue
            spans = rb.get("spans", [])
            sizes.extend([s.get("size") for s in spans if s.get("size")])
        size_median = median([s for s in sizes if isinstance(s, (int, float))]) or 10.0

        for rb in page.get("raw_blocks", []):
            if rb.get("type") != "text":
                continue
            text = " ".join(rb.get("text", "").split())
            if not text:
                continue
            level = None
            # derive a representative size
            span_sizes = [s.get("size") for s in rb.get("spans", []) if s.get("size")]
            rep_size = median([s for s in span_sizes if isinstance(s, (int, float))]) or size_median
            level = guess_heading_level(rep_size, size_median)

            if level is not None:
                blocks.append({
                    "type": "heading",
                    "level": level,
                    "text": text,
                    "bbox": rb.get("bbox"),
                })
            else:
                blocks.append({
                    "type": "paragraph",
                    "text": text,
                    "bbox": rb.get("bbox"),
                })
        structured_pages.append({
            "number": page["number"],
            "width": page["width"],
            "height": page["height"],
            "blocks": blocks,
            "images": page.get("images", []),
            "links": page.get("links", []),
        })

    out_meta = {
        "title": None,
        "pages": len(structured_pages),
    }
    if isinstance(meta, dict):
        out_meta.update(meta)

    # Build sections tree
    def new_node(title: str, level: int, page_start: int) -> Dict[str, Any]:
        return {
            "title": title,
            "level": level,
            "page_start": page_start,
            "page_end": None,
            "children": [],
            "blocks": [],
            "images": [],
            "links": [],
        }

    sections: List[Dict[str, Any]] = []
    stack: List[Dict[str, Any]] = []

    toc = (out_meta or {}).get("toc") or []
    if toc:
        # Use ToC for hierarchy; attach content by page ranges later
        for item in toc:
            title = item.get("title") or ""
            level = int(item.get("level") or 1)
            page = int(item.get("page") or 1)
            node = new_node(title, level, page)
            # place in hierarchy
            while stack and stack[-1]["level"] >= level:
                stack.pop()
            if stack:
                stack[-1]["children"].append(node)
            else:
                sections.append(node)
            stack.append(node)

        # Fill page_end by next section start - 1
        flat: List[Dict[str, Any]] = []
        def walk(n: Dict[str, Any]):
            flat.append(n)
            for c in n["children"]:
                walk(c)
        for root in sections:
            walk(root)
        flat_sorted = sorted(flat, key=lambda n: (n["page_start"], n["level"]))
        for i, n in enumerate(flat_sorted):
            # find next node with same or higher level
            end_page = structured_pages[-1]["number"] if structured_pages else n["page_start"]
            for m in flat_sorted[i+1:]:
                if m["level"] <= n["level"]:
                    end_page = m["page_start"] - 1
                    break
            n["page_end"] = max(n["page_start"], end_page)

    else:
        # Infer sections from headings
        for page in structured_pages:
            for blk in page.get("blocks", []):
                if blk.get("type") == "heading":
                    level = int(blk.get("level") or 1)
                    node = new_node(blk.get("text", ""), level, page["number"])
                    while stack and stack[-1]["level"] >= level:
                        stack.pop()
                    if stack:
                        stack[-1]["children"].append(node)
                    else:
                        sections.append(node)
                    stack.append(node)

        # Assign page_end similarly
        flat: List[Dict[str, Any]] = []
        def walk2(n: Dict[str, Any]):
            flat.append(n)
            for c in n["children"]:
                walk2(c)
        for root in sections:
            walk2(root)
        flat_sorted = sorted(flat, key=lambda n: (n["page_start"], n["level"]))
        for i, n in enumerate(flat_sorted):
            end_page = structured_pages[-1]["number"] if structured_pages else n["page_start"]
            for m in flat_sorted[i+1:]:
                if m["level"] <= n["level"]:
                    end_page = m["page_start"] - 1
                    break
            n["page_end"] = max(n["page_start"], end_page)

    # Attach content to sections by page range
    def assign_content():
        if not sections:
            return
        # Utility to add block/image/link to the deepest matching section containing this page
        def place(page_num: int, kind: str, item: Dict[str, Any]):
            def place_in(nodes: List[Dict[str, Any]]):
                for node in nodes[::-1]:
                    if node["page_start"] <= page_num <= (node["page_end"] or page_num):
                        if node["children"]:
                            placed = place_in(node["children"])
                            if placed:
                                return True
                        if kind == "block":
                            node["blocks"].append(item)
                        elif kind == "image":
                            node["images"].append(item)
                        elif kind == "link":
                            node["links"].append(item)
                        return True
                return False
            place_in(sections)

        for page in structured_pages:
            for blk in page.get("blocks", []):
                place(page["number"], "block", {"page": page["number"], "block": blk})
            for img in page.get("images", []):
                place(page["number"], "image", img)
            for lnk in page.get("links", []):
                place(page["number"], "link", lnk)

    assign_content()

    return {"meta": out_meta, "pages": structured_pages, "sections": sections}
