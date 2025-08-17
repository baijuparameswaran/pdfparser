# Examples

## Basic parse

```bash
pdfparser sample.pdf --out out.json
```

## With OCR if needed

```bash
pdfparser scanned.pdf --ocr-if-needed --dpi 300 --out out.json
```

## Save images while parsing

```bash
pdfparser report.pdf --images-dir images/ --out out.json
```

## Vision refinement

```bash
export OPENAI_API_KEY=sk-...
pdfparser paper.pdf --vision --model gpt-4o-mini --out refined.json
```
