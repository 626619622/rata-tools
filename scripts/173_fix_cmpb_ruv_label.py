"""Correct the remaining RUV-III label and rebuild CMPB manuscript v4."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = Path(r"C:\Users\赵佳康\Documents\deepseek-harness\default-workspace\rata_final")
IN_DIR = ROOT / "cmpb_submission_20261118"
SOURCE_MD = IN_DIR / "RATA_CMPB_Manuscript_v3.md"
OUT_MD = IN_DIR / "RATA_CMPB_Manuscript_v4.md"
OUT_DOCX = IN_DIR / "RATA_CMPB_Manuscript_v4.docx"
PYTHON = ROOT.parent / "pituitary-env" / "python311" / "python.exe"


def main() -> None:
    text = SOURCE_MD.read_text(encoding="utf-8")
    old = "| ComBat / SVA / RUV-III |"
    new = "| ComBat / SVA / RUV |"
    if old not in text:
        raise ValueError("Expected RUV-III Table 1 label not found")
    text = text.replace(old, new, 1)
    if "RUV-III" in text:
        raise ValueError("RUV-III remains in the corrected manuscript")
    OUT_MD.write_text(text, encoding="utf-8")
    subprocess.run(
        [str(PYTHON), str(SOURCE_DIR / "build_docx.py"), str(OUT_MD), str(OUT_DOCX)],
        check=True,
        cwd=str(IN_DIR),
    )
    print(OUT_MD)
    print(OUT_DOCX)


if __name__ == "__main__":
    main()
