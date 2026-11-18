"""Finalize the Bioinformatics manuscript abstract and source."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v1.md"
OUTPUT = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v2.md"


ABSTRACT = """## Abstract

**Motivation:** External performance is often treated as evidence that a transcriptomic signature transports across cohorts. Validation accessions may reuse arrays or patients, selection can inflate apparent performance, and scores may mainly capture lineage, proliferation or tissue composition. Existing tools adjust expression or fit robust models but do not audit a published transportability claim.

**Results:** We present Role-Aware Transportability Audit (RATA), implemented in `rata-tools` 0.2.0. Gate 1 combines selection-aware cross-validation with matched nulls; Gate 2 applies endpoint-specific binary or cohort-stratified survival rules; Gate 3 separates target, confounder and mediator axes. Evidence capacity and gate-specific outcomes are returned as structured records. Computational validation included ACC and pituitary controls, five known-truth scenarios, tool comparison and runtime benchmarks. ACC evidence collapsed to three adult clusters; one 13-gene signature passed all gates with a modest effect (HR 1.49, 95% CI 1.07-2.08; I2=0). A lineage control passed, whereas an invasion signature with apparent AUC 0.933 failed selection and transport. Simulation separated portable, confounded and non-transport signals. A 500-sample, 1,000-feature selection benchmark ran in 0.040 s.

**Availability and implementation:** The package provides a Python API, command-line interface, examples, tests and continuous integration. Data accessions and reproducibility materials are supplied with the manuscript.

**Contact:** 213231036@seu.edu.cn

"""


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    pattern = re.compile(r"## Abstract.*?(?=\*\*Keywords:\*\*)", re.S)
    if pattern.search(text) is None:
        raise ValueError("Abstract section not found")
    text = pattern.sub(ABSTRACT, text, count=1)
    abstract = text.split("## Abstract", 1)[1].split("**Keywords:**", 1)[0]
    word_count = len(re.findall(r"\b[\w]+\b", abstract))
    if not 240 <= word_count <= 270:
        raise ValueError(f"Unexpected abstract length: {word_count}")
    OUTPUT.write_text(text, encoding="utf-8")
    print(OUTPUT)
    print(f"Abstract words: {word_count}")


if __name__ == "__main__":
    main()
