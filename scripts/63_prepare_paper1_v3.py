"""Prepare the submission-oriented v3 Markdown source from the audited v2 draft.

This script only creates new files under codex_output/. It does not alter the
existing v2 manuscript or any upstream result tables.
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "manuscript" / "RATA_Paper1_Manuscript_v2.md"
OUTPUT = ROOT / "manuscript" / "RATA_Paper1_Manuscript_v3.md"


ABSTRACT = """## Abstract

**Background:** External area under the receiver operating characteristic curve (AUC) can overstate the independence of transcriptomic signatures when cohorts overlap, feature selection uses the same samples, or scores reflect lineage and tissue composition. We developed Role-Aware Transportability Audit (RATA), a three-gate framework separating selection robustness, independent transport, and role-aware axis interpretation.

**Methods:** Gate 1 compared apparent performance with pure and realistic selection nulls and used selection cross-validation when reproducible. Gate 2 applied cohort-stratified survival models or endpoint-specific binary rules. Gate 3 adjusted prespecified confounders while separating targets and mediators. We audited 11 adrenocortical carcinoma (ACC) signatures, a pituitary GH/NFPA positive control, and a pituitary invasion negative case, with known-truth simulations and reusable software.

**Results:** Nine ACC signatures were TCGA-involved (eight confirmed and one inferred). Seven had verifiable external claims, corresponding to nine signature-cohort validation claims across three adult non-TCGA cohort clusters (effective number 2.67). Three of six scoreable signatures passed Gate 1. The 13-gene ssGSEA signature was the only signature with two unseen adult cohorts and passed Gate 2 (hazard ratio [HR] 1.49, 95% CI 1.07-2.08; I2=0); stromal and lineage adjustment gave HR 1.58 (1.11-2.24). Proliferation possibly mediated the association, but the mediated proportion was imprecise. The lineage control passed selection cross-validation (AUC 0.991; null q95 0.630) and external validation (AUC 1.000). An invasion signature had apparent AUC 0.933 but selection-CV AUC 0.587 and inconsistent external performance (0.531 and 0.953). Simulated joint pass rates were 0.33% for null, 94% for portable, 1.0% for confounded-only, and 0% for non-transport. A frozen preflight rule achieved AUROC 0.650 and sensitivity 0.530 (95% CI 0.490-0.569), below prespecified criteria.

**Conclusions:** ACC external evidence was limited, and several apparent performances were compatible with selection noise. One signature passed all gates with a modest, partly mediated effect. RATA is a descriptive evidence-audit framework, not a validated prediction tool.

"""


TABLE2 = """### Table 2. Joint operating characteristics of the three-gate framework

| Scenario | Gate 1, % (95% CI) | Gate 1+2, % (95% CI) | Gate 1+2+3, % (95% CI) |
|---|---:|---:|---:|
| Pure null | 0.7 (0.2-2.4) | 0.3 (0.1-1.9) | 0.3 (0.1-1.9) |
| Confounded only | 94.7 (91.5-96.7) | 94.7 (91.5-96.7) | 1.0 (0.3-2.9) |
| True non-transport | 91.3 (87.6-94.0) | 0.0 (0.0-1.3) | 0.0 (0.0-1.3) |
| True portable | 94.0 (90.7-96.2) | 94.0 (90.7-96.2) | 94.0 (90.7-96.2) |
| Attenuated true effect | 92.3 (88.8-94.8) | 89.0 (85.0-92.1) | 89.0 (85.0-92.1) |

Percentages are pass rates over 300 runs per scenario. CIs are Wilson 95% intervals. The confounded-only and true non-transport scenarios test whether later gates remove signals that pass selection alone; the true-portable scenario tests whether a real signal can pass all gates.

"""


FIGURES = """## Figure legends

**Figure 1. Evidence capacity and provenance of ACC transcriptomic signatures.** Horizontal bars show the number of published signatures using each external expression cohort cluster after collapsing shared arrays and GEO SuperSeries/SubSeries. Seven signatures had verifiable external-expression claims, corresponding to nine signature-cohort validation claims across the displayed clusters. Platforms are shown at the end of each bar. The Herfindahl effective number was 2.67 across the eight adult non-TCGA claims and 3.24 across all reported claims.

**Figure 2. Gate 1 selection robustness.** Points show the observed apparent AUC percentile under a realistic top-k selection null for six ACC signatures with recoverable scores. The dashed line marks the prespecified 95th-percentile gate. Candidate-pool size and selected feature count were matched to each publication. Higher values indicate performance less compatible with selection noise; pure-null results are provided in the Supplementary Material.

**Figure 3. Independent transport and role-aware adjustment.** Per-cohort AUC/C-index and forest plots for survival and binary endpoints. The ssGSEA model is shown before and after role-aware confounder adjustment, with target over-adjustment and mediator adjustment displayed as separate sensitivity analyses.

**Figure 4. Pituitary lineage positive control.** External GH/CNFPA separation, seven-marker score, 200-versus-186-gene score correlation, inferred-sex residual AUC, and PC1/PC2-PC5 sensitivity analysis.

**Figure 5. Pituitary invasion negative case and three-gate operating characteristics.** Top left: apparent AUC, reproducible selection cross-validation AUC and the 1,000-run selection-null 95th percentile for the pituitary invasion signature. Top right: external AUCs with bootstrap 95% confidence intervals in GSE136781 and GSE260487; the inset reports the complete invasion-lineage confounding in GSE260487. Bottom: joint pass rates for Gate 1, Gates 1+2, and Gates 1+2+3 across five known-truth scenarios, with 300 runs per scenario.

"""


def replace_section(text: str, start: str, end: str, replacement: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?(?=" + re.escape(end) + ")", re.S)
    if pattern.search(text) is None:
        raise ValueError(f"Section not found: {start}")
    return pattern.sub(replacement, text, count=1)


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    text = replace_section(text, "## Abstract", "**Keywords:**", ABSTRACT)

    text = text.replace(
        "Before adjustment, each signature was assigned a target domain, confounders, mediators, and axes that should not be adjusted.",
        "Gate 3 was applied only to signatures that passed Gate 1 and had at least one independent pair. Before adjustment, each signature was assigned a target domain, confounders, mediators, and axes that should not be adjusted.",
        1,
    )

    text = text.replace(
        "The pituitary invasion negative case used GSE169498 for discovery and GSE136781 and GSE260487 as external cohorts.",
        "The pituitary invasion negative case used GSE169498 for discovery and GSE136781 and GSE260487 as external cohorts. The discovery candidate pool contained 18,827 genes before expression filtering and signature reconstruction.",
        1,
    )

    text = text.replace(
        "The invasion discovery cohort contained 73 tumours (49 invasive and 24 non-invasive). The reconstructed signature used 11 invasive-positive and 15 invasive-negative genes.",
        "The invasion discovery cohort contained 73 tumours (49 invasive and 24 non-invasive) and began with a candidate pool of 18,827 genes. The reconstructed signature used 11 invasive-positive and 15 invasive-negative genes.",
        1,
    )

    text = replace_section(text, "### Table 2.", "## Figure legends", TABLE2)
    text = replace_section(text, "## Figure legends", "## Data and code availability", FIGURES)

    if "permanent repository DOI" in text or "should be inserted before submission" in text:
        raise ValueError("Unresolved repository placeholder remains")

    OUTPUT.write_text(text, encoding="utf-8")

    abstract = text.split("## Abstract", 1)[1].split("**Keywords:**", 1)[0]
    words = re.findall(r"\b[\w'-]+\b", abstract)
    print(f"{OUTPUT}")
    print(f"Abstract words: {len(words)}")


if __name__ == "__main__":
    main()
