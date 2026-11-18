"""Build the final table-paginated Bioinformatics DOCX from v10."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_SCRIPT = ROOT / "scripts" / "121_build_bioinformatics_docx_final.py"


def main() -> None:
    code = SOURCE_SCRIPT.read_text(encoding="utf-8")
    code = code.replace(
        'SOURCE = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v8.md"',
        'SOURCE = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v10.md"',
        1,
    ).replace(
        'OUTPUT = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v5.docx"',
        'OUTPUT = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v6.docx"',
        1,
    )
    namespace = {"__file__": str(SOURCE_SCRIPT), "__name__": "rata_docx_v10"}
    exec(compile(code, str(SOURCE_SCRIPT), "exec"), namespace)
    namespace["main"]()


if __name__ == "__main__":
    main()
