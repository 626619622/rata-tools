from pathlib import Path
from docx import Document
from docx.shared import Pt

root = Path(__file__).resolve().parents[1] / "manuscript"

for stem in ["RATA_Paper1_TitlePage_v1", "RATA_Paper1_CoverLetter_v1"]:
    source = root / f"{stem}.md"
    output = root / f"{stem}.docx"
    doc = Document()
    doc.styles["Normal"].font.name = "Times New Roman"
    doc.styles["Normal"].font.size = Pt(11)
    for line in source.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text:
            doc.add_paragraph()
        elif text.startswith("# "):
            doc.add_heading(text[2:], level=1)
        elif text.startswith("**") and text.endswith("**"):
            doc.add_paragraph(text.strip("*"))
        else:
            doc.add_paragraph(text.replace("  ", "\n"))
    doc.save(output)
    print(output)
