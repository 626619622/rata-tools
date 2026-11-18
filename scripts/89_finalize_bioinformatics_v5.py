"""Finalize equation rendering and typography for the Bioinformatics source."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v4.md"
OUTPUT = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v5.md"


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    old_formula = (
        "\\[\n"
        "N_{\\mathrm{eff}} = 1 / \\sum_i p_i^2,\n"
        "\\]\n\n"
        "where \\(p_i\\) is the proportion of claims using cluster \\(i\\)."
    )
    new_formula = (
        "**N_eff = 1 / Σ_i p_i²**, where p_i is the proportion of claims "
        "using cluster i."
    )
    if old_formula not in text:
        raise ValueError("Expected equation block not found")
    text = text.replace(old_formula, new_formula, 1)
    text = text.replace("Cramer's V", "Cramér's V")
    OUTPUT.write_text(text, encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
