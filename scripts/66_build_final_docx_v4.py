"""Build final submission DOCX files from the v4 Markdown sources."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "64_build_submission_docx_v3.py"


def load_builder():
    spec = importlib.util.spec_from_file_location("rata_docx_builder", BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load DOCX builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> None:
    builder = load_builder()
    manuscript = ROOT / "manuscript"
    builder.add_markdown_docx(
        manuscript / "RATA_Paper1_Manuscript_v4.md",
        manuscript / "RATA_Paper1_Manuscript_v4.docx",
        manuscript=True,
    )
    builder.add_markdown_docx(
        manuscript / "RATA_Paper1_CoverLetter_v1.md",
        manuscript / "RATA_Paper1_CoverLetter_v2.docx",
        manuscript=False,
    )
    builder.add_markdown_docx(
        manuscript / "RATA_Paper1_TitlePage_v1.md",
        manuscript / "RATA_Paper1_TitlePage_v2.docx",
        manuscript=False,
    )


if __name__ == "__main__":
    main()
