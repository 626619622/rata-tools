"""Build Bioinformatics manuscript DOCX from v7."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "64_build_submission_docx_v3.py"


def main() -> None:
    spec = importlib.util.spec_from_file_location("rata_docx_builder", BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load DOCX builder")
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    builder.add_markdown_docx(
        ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v7.md",
        ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v3.docx",
        manuscript=True,
    )


if __name__ == "__main__":
    main()
