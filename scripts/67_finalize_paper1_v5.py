"""Create the final Paper 1 source with a 250-300 word abstract."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manuscript" / "RATA_Paper1_Manuscript_v4.md"
OUTPUT = ROOT / "manuscript" / "RATA_Paper1_Manuscript_v5.md"


ABSTRACT = """## Abstract

**Background:** External area under the receiver operating characteristic curve (AUC) can overstate independence when cohorts overlap, feature selection and evaluation share samples, or scores reflect lineage and tissue composition. Role-Aware Transportability Audit (RATA) is a three-gate framework for selection robustness, independent transport, and role-aware axis interpretation.

**Methods:** Gate 1 compared apparent performance with pure and realistic selection nulls. Gate 2 used cohort-stratified survival or endpoint-specific binary rules. Gate 3 adjusted prespecified confounders while separating targets and mediators. We audited 11 adrenocortical carcinoma (ACC) signatures, one pituitary positive control, one invasion negative case, known-truth simulations, and software.

**Results:** Nine ACC signatures were TCGA-involved (eight confirmed and one inferred). Seven had verifiable external claims, with nine signature-cohort validation claims across three adult non-TCGA cohort clusters (effective number 2.67). Three of six scoreable signatures passed Gate 1. The 13-gene ssGSEA signature alone had two unseen adult cohorts and passed Gate 2 (hazard ratio [HR] 1.49, 95% CI 1.07-2.08; I2=0); stromal and lineage adjustment gave HR 1.58 (1.11-2.24). Proliferation possibly mediated the association, but the mediated proportion was imprecise. The lineage control passed selection cross-validation (AUC 0.991; null q95 0.630) and external validation (AUC 1.000). An invasion signature had apparent AUC 0.933 but selection-CV AUC 0.587 with inconsistent external performance (0.531 and 0.953). Joint simulation pass rates were 0.33% for null, 94% for portable, 1.0% for confounded-only, and 0% for non-transport. A frozen preflight rule achieved AUROC 0.650 and sensitivity 0.530 (95% CI 0.490-0.569), below prespecified criteria.

**Conclusions:** ACC external evidence was limited, and several apparent performances were compatible with selection noise. One signature passed all gates with a modest, partly mediated effect. RATA is a descriptive evidence-audit framework, not a validated prediction tool.

"""


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    pattern = re.compile(r"## Abstract.*?(?=\*\*Keywords:\*\*)", re.S)
    if pattern.search(text) is None:
        raise ValueError("Abstract section not found")
    text = pattern.sub(ABSTRACT, text, count=1)
    abstract = text.split("## Abstract", 1)[1].split("**Keywords:**", 1)[0]
    words = re.findall(r"\b[\w'-]+\b", abstract)
    if not 250 <= len(words) <= 300:
        raise ValueError(f"Abstract length outside 250-300 words: {len(words)}")
    OUTPUT.write_text(text, encoding="utf-8")
    print(OUTPUT)
    print(f"Abstract words: {len(words)}")


if __name__ == "__main__":
    main()
