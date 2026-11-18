"""Build the Bioinformatics manuscript DOCX from the final Markdown source."""

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
        manuscript / "RATA_Paper_Bioinformatics_v5.md",
        manuscript / "RATA_Paper_Bioinformatics_v1.docx",
        manuscript=True,
    )


if __name__ == "__main__":
    main()
