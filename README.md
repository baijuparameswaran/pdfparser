# pdfparser

Parse standard or scanned PDFs into structured elements (headings, paragraphs, and images) using PyMuPDF for text/layout extraction, Tesseract OCR for scanned pages, and optional Vision LLM enrichment for better heading detection and section summaries.

## Features

- Extract text blocks with fonts, sizes, and positions using PyMuPDF.
- Heuristic heading detection (font size, boldness, spacing, numbering).
- Paragraph grouping by proximity and styles.
- Image extraction with bounding boxes and save-to-file option.
- Link extraction (URIs and intra-document links) with bounding boxes.
- OCR for scanned PDFs via Tesseract (pytesseract) with per-page configurable DPI.
- Optional Vision LLM enrichment (OpenAI) to refine headings, hierarchy, and create alt text for images.
- JSON output includes meta (title, authors, creator, producer, creation/mod dates, ToC) and per-page blocks, images, and links.
- Sections tree that nests content under chapters/sections: built from PDF ToC when available, falling back to heading heuristics.
- CLI and Python API.

## Install

Prerequisites:
- System: Tesseract OCR installed and accessible on PATH (for OCR features). On Linux:
  ```bash
  sudo apt-get update
  sudo apt-get install -y tesseract-ocr
  ```
- Python 3.9+

Then install dependencies (choose one):

- Using requirements files (recommended for venv installs):
  ```bash
  # Base runtime deps
  pip install -r requirements.txt

  # Optional vision deps
  # pip install -r requirements-vision.txt
  ```

- Or install the package in editable mode (includes deps via pyproject):
  ```bash
  pip install -e .
  # Optional vision extras
  # pip install -e .[vision]
  ```

Set `OPENAI_API_KEY` in your environment to enable vision features.

### Quickstart (local)

```bash
# Create and activate a virtualenv (recommended)
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Optional: Enable vision features
# pip install -r requirements-vision.txt
# export OPENAI_API_KEY=YOUR_KEY

# Run the CLI on a PDF
pdfparser input.pdf --out out.json --ocr-if-needed --images-dir images/

# Try the included smoke test (generates a sample PDF and parses it)
python scripts/smoke_test.py
```

## Usage

### CLI

```bash
pdfparser input.pdf --out out.json --images-dir images/ --ocr-if-needed
```

Options:
- `--out`: Path to write JSON result (default prints to stdout).
- `--images-dir`: Directory to save extracted images (optional).
- `--dpi`: DPI for OCR rendering (default 300).
- `--ocr`: Force OCR all pages.
- `--ocr-if-needed`: OCR only pages with low/no extractable text.
- `--vision`: Use Vision LLM to refine structure (requires OPENAI_API_KEY).
- `--model`: Vision model name (default `gpt-4o-mini` if openai installed).
- `--max-pages`: Limit pages processed.
- `--page-range`: e.g. `1-5,8,10-12`.
- `--verbose`: Debug logs.

### Python API

```python
from pdfparser.api import parse_pdf

result = parse_pdf(
    path="input.pdf",
    images_dir="images",
    ocr_mode="if-needed",  # "never" | "if-needed" | "always"
    ocr_dpi=300,
    use_vision=False,
    vision_model="gpt-4o-mini",
    max_pages=None,
    page_range=None,
)

# result is a dict you can dump to JSON

# Example: iterate sections (chapters) and print headings in each
def walk_sections(sections, depth=0):
  for s in sections:
    print("  " * depth + f"- [L{s['level']}] {s['title']} (pages {s['page_start']}–{s['page_end']})")
    # Show first 3 blocks' texts for preview
    for b in s.get("blocks", [])[:3]:
      blk = b["block"]
      if blk.get("type") == "heading":
        print("  " * (depth + 1) + f"• H{blk['level']}: {blk['text']}")
      elif blk.get("type") == "paragraph":
        print("  " * (depth + 1) + f"• P: {blk['text'][:80]}…")
    walk_sections(s.get("children", []), depth + 1)

walk_sections(result.get("sections", []))
```

## Output Schema

High-level JSON structure (simplified):

```json
{
  "meta": {
    "title": "...",
    "authors": ["..."],
    "creator": "...",
    "producer": "...",
    "creationDate": "...",
    "modDate": "...",
    "pages": 10,
    "toc": [{"level": 1, "title": "Chapter 1", "page": 2}]
  },
  "pages": [
    {
      "number": 1,
      "width": 595.2,
      "height": 841.8,
      "blocks": [
        {"type": "heading", "level": 1, "text": "Introduction", "bbox": [x1,y1,x2,y2]},
        {"type": "paragraph", "text": "...", "bbox": [x1,y1,x2,y2]}
      ],
      "images": [
        {"id": "img_0001", "bbox": [x1,y1,x2,y2], "path": "images/img_0001.png", "alt": "..."}
      ],
      "links": [
        {"bbox": [x1,y1,x2,y2], "uri": "https://...", "target_page": null, "text": null}
      ]
    }
  ]
  ,
  "sections": [
    {
      "title": "Chapter 1",
      "level": 1,
      "page_start": 2,
      "page_end": 10,
      "children": [
        {"title": "1.1 Background", "level": 2, "page_start": 3, "page_end": 5, "children": []}
      ],
      "blocks": [{"page": 2, "block": {"type": "heading", "level": 1, "text": "Chapter 1"}}],
      "images": [],
      "links": []
    }
  ]
}

### Advanced options

- OCR modes:
  - `never`: Do not OCR (fastest for born-digital PDFs).
  - `if-needed`: OCR only pages with little/no extractable text (default).
  - `always`: Force OCR for all pages (use for pure scans).
- Page selection: `--page-range "1-5,8,10-12"` and/or `--max-pages N`.
- Vision refinement: `--vision --model gpt-4o-mini` (requires `OPENAI_API_KEY`).
- Images directory: `--images-dir images/` saves embedded images to disk.

### Notes

- Link `text` is not guaranteed because links are defined by rectangles; mapping to overlapping text is heuristic and may be empty.
- Image bounding boxes come from PyMuPDF image info when available and can be approximate.
- Title/authors are pulled from PDF metadata; if missing, simple layout heuristics infer them from the first page.
```

## Limitations

- Heuristics may misclassify headings for highly stylized PDFs.
- OCR accuracy depends on the scan quality and Tesseract language models installed.
- Vision LLM enrichment requires Internet and may incur costs; results are probabilistic.

## Development

Run unit tests (if you add some):
```bash
pytest -q
```

## License

MIT
