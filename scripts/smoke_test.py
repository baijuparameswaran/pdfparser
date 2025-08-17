import json
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER
from pdfparser.api import parse_pdf

# Generate a small PDF for testing
p = Path(__file__).parent
sample = p / "sample.pdf"

c = canvas.Canvas(str(sample), pagesize=LETTER)
width, height = LETTER
c.setFont("Helvetica-Bold", 20)
c.drawString(72, height-72, "Sample Document")

c.setFont("Helvetica", 12)
textobject = c.beginText(72, height-120)
textobject.textLine("This is a test paragraph. It should be detected as a paragraph.")
textobject.textLine("Another line continues the paragraph.")
c.drawText(textobject)

c.showPage()
c.save()

res = parse_pdf(str(sample), images_dir=str(p / "images"), ocr_mode="never", verbose=True)
print(json.dumps(res, indent=2))
