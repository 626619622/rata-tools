"""Finalize the Bioinformatics source for Word/PDF rendering."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v4.md"
OUTPUT = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v5.md"


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    replacements = {
        "Cramer's V": "Cramér's V",
        """The effective number of clusters is the inverse Herfindahl concentration,

\\[
N_{\\mathrm{eff}} = 1 / \\sum_i p_i^2,
\\]

where \\(p_i\\) is the proportion of claims using cluster \\(i\\).
""": """The effective number of clusters is the inverse Herfindahl concentration,

**N_eff = 1 / Σ_i p_i²,**

where p_i is the proportion of claims using cluster i.
""",
    }
    for old, new in replacements.items():
        if old not in text:
            raise ValueError(f"Expected text not found: {old[:60]}")
        text = text.replace(old, new, count=1)
    OUTPUT.write_text(text, encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
