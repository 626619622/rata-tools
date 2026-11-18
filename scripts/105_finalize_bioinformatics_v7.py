"""Create the final Bioinformatics Markdown source with complete cross-references."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v6.md"
OUTPUT = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v7.md"


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    replacements = [
        (
            "Cochran's Q, I-squared, confidence-interval width and instability flags.",
            "Cochran's Q [21], I-squared, confidence-interval width and instability flags.",
        ),
        (
            "The test suite covers evidence capacity, Harrell's C-index, censoring, selection-aware AUC, binary and multi-cohort transport, stratified Cox behavior, direction reversal, unstable cohorts, decision vocabulary and input validation.",
            "The test suite covers evidence capacity, Harrell's C-index [22], censoring, selection-aware AUC, binary and multi-cohort transport, stratified Cox behavior, direction reversal, unstable cohorts, decision vocabulary and input validation.",
        ),
        (
            "With 500 cohort-stratified bootstrap replicates, the proliferation-mediated proportion",
            "With 500 cohort-stratified bootstrap replicates [20], the proliferation-mediated proportion",
        ),
        (
            "The complete pair-level ACC registry, transport results, confidence intervals and per-axis estimates are in Supplementary Tables S1 and S2.",
            "The complete pair-level ACC registry and transport results are in Supplementary Table S1; selection and role-aware estimates are in Supplementary Table S2.",
        ),
    ]
    for old, new in replacements:
        if old not in text:
            raise ValueError(f"Expected text not found: {old[:80]}")
        text = text.replace(old, new, 1)
    OUTPUT.write_text(text, encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
