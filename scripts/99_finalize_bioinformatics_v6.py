"""Final cross-reference pass for the Bioinformatics manuscript."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v5.md"
OUTPUT = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v6.md"


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    replacements = [
        (
            "The complete pair-level ACC registry, confidence intervals and per-axis estimates are in Supplementary Tables S1 and S2.",
            "The complete pair-level ACC registry, transport results, confidence intervals and per-axis estimates are in Supplementary Tables S1 and S2.",
        ),
        (
            "The adjusted invasion AUC was not identifiable. The negative case shows how a strong apparent result can fail both selection and independent-transport checks.",
            "The adjusted invasion AUC was not identifiable. Full positive-control and invasion tables are provided in Supplementary Table S3. The negative case shows how a strong apparent result can fail both selection and independent-transport checks.",
        ),
        (
            "Wilson 95% confidence intervals for component and joint gate combinations are provided in the Supplementary Material.",
            "Wilson 95% confidence intervals for component and joint gate combinations are provided in Supplementary Table S3.",
        ),
        (
            "These timings describe software overhead on synthetic inputs and are not estimates of expression preprocessing or data download time.",
            "These timings describe software overhead on synthetic inputs and are not estimates of expression preprocessing or data download time. The benchmark environment, vignette and release checks are provided in Supplementary Table S4.",
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
