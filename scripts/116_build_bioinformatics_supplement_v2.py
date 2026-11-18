"""Build supplement v2 with the 20,000-feature benchmark."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "93_build_bioinformatics_supplement.py"


def main() -> None:
    code = SOURCE.read_text(encoding="utf-8")
    replacements = {
        'OUT = ROOT / "manuscript" / "RATA_Bioinformatics_Supplementary_v1.pdf"': (
            'OUT = ROOT / "manuscript" / "RATA_Bioinformatics_Supplementary_v2.pdf"'
        ),
        "Version 1 | 10 November 2026": "Version 2 | 10 November 2026",
        'RESULTS / "Bioinformatics_RuntimeBenchmark.csv"': (
            'RESULTS / "Bioinformatics_RuntimeBenchmark_v2.csv"'
        ),
        'RESULTS / "Bioinformatics_RuntimeBenchmark.json"': (
            'RESULTS / "Bioinformatics_RuntimeBenchmark_v2.json"'
        ),
    }
    for old, new in replacements.items():
        if old not in code:
            raise ValueError(f"Expected text not found: {old}")
        code = code.replace(old, new, 1)
    namespace = {"__file__": str(SOURCE), "__name__": "rata_bioinformatics_supp_v2"}
    exec(compile(code, str(SOURCE), "exec"), namespace)
    namespace["main"]()


if __name__ == "__main__":
    main()
