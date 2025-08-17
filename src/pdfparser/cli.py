from __future__ import annotations

import argparse
import json
from .api import parse_pdf


def main():
    p = argparse.ArgumentParser(description="Parse a PDF into structured content (headings, paragraphs, images)")
    p.add_argument("input", help="Path to input PDF")
    p.add_argument("--out", help="Write output JSON to file; default stdout")
    p.add_argument("--images-dir", help="Directory to save extracted images")
    p.add_argument("--dpi", type=int, default=300, help="DPI for OCR rendering")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--ocr", action="store_true", help="Force OCR all pages")
    g.add_argument("--ocr-if-needed", action="store_true", help="OCR only pages with low/no text")
    p.add_argument("--vision", action="store_true", help="Use Vision LLM to refine structure")
    p.add_argument("--model", default="gpt-4o-mini", help="Vision model name")
    p.add_argument("--max-pages", type=int)
    p.add_argument("--page-range", help="e.g. 1-5,8,10-12")
    p.add_argument("--verbose", action="store_true")

    args = p.parse_args()

    ocr_mode = "never"
    if args.ocr:
        ocr_mode = "always"
    elif args.ocr_if_needed:
        ocr_mode = "if-needed"

    result = parse_pdf(
        path=args.input,
        images_dir=args.images_dir,
        ocr_mode=ocr_mode,
        ocr_dpi=args.dpi,
        use_vision=args.vision,
        vision_model=args.model,
        max_pages=args.max_pages,
        page_range=args.page_range,
        verbose=args.verbose,
    )

    js = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(js)
    else:
        print(js)


if __name__ == "__main__":
    main()
