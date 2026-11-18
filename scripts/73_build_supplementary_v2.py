"""Build a readable, paginated RATA Paper 1 supplementary PDF.

All output is created under codex_output/. Upstream manuscripts and results are
read-only inputs.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
REGISTRY = ROOT / "registry"
OUT = ROOT / "manuscript" / "RATA_Paper1_Supplementary_v2.pdf"


def footer(fig, page_number: int) -> None:
    fig.text(0.5, 0.02, f"RATA Paper 1 | Supplementary Material | {page_number}", ha="center", fontsize=7)


def add_text_page(pdf: PdfPages, title: str, text: str, page_counter: list[int], fontsize: float = 7.4) -> None:
    wrapped_lines: list[str] = []
    for paragraph in textwrap.dedent(text).strip().splitlines():
        if not paragraph:
            wrapped_lines.append("")
            continue
        wrapped_lines.extend(
            textwrap.wrap(
                paragraph,
                width=150,
                replace_whitespace=False,
                drop_whitespace=True,
            )
            or [""]
        )

    lines_per_page = 72
    chunks = [wrapped_lines[i : i + lines_per_page] for i in range(0, len(wrapped_lines), lines_per_page)]
    if not chunks:
        chunks = [[""]]

    for chunk_index, chunk in enumerate(chunks):
        fig, ax = plt.subplots(figsize=(11, 8.5))
        ax.axis("off")
        suffix = f" (continued {chunk_index + 1})" if len(chunks) > 1 else ""
        ax.text(0.045, 0.955, title + suffix, fontsize=13, fontweight="bold", va="top")
        ax.text(
            0.045,
            0.905,
            "\n".join(chunk),
            fontsize=fontsize,
            va="top",
            family="DejaVu Sans Mono",
            linespacing=1.28,
        )
        page_counter[0] += 1
        footer(fig, page_counter[0])
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)


def add_table_pages(
    pdf: PdfPages,
    title: str,
    frame: pd.DataFrame,
    columns: list[str],
    page_counter: list[int],
    rows_per_page: int,
    max_colwidth: int = 24,
    fontsize: float = 6.2,
) -> None:
    subset = frame.loc[:, columns].copy()
    chunks = [subset.iloc[i : i + rows_per_page] for i in range(0, len(subset), rows_per_page)]
    if not chunks:
        chunks = [subset]

    for chunk_index, chunk in enumerate(chunks):
        fig, ax = plt.subplots(figsize=(11, 8.5))
        ax.axis("off")
        suffix = f" (continued {chunk_index + 1})" if len(chunks) > 1 else ""
        ax.text(0.035, 0.955, title + suffix, fontsize=12.5, fontweight="bold", va="top")
        table_text = chunk.to_string(index=False, max_colwidth=max_colwidth)
        ax.text(
            0.035,
            0.905,
            table_text,
            fontsize=fontsize,
            va="top",
            family="DejaVu Sans Mono",
            linespacing=1.18,
        )
        page_counter[0] += 1
        footer(fig, page_counter[0])
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)


def add_cover(pdf: PdfPages, page_counter: list[int]) -> None:
    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.axis("off")
    ax.text(0.5, 0.80, "Supplementary Material", ha="center", va="center", fontsize=22, fontweight="bold")
    ax.text(
        0.5,
        0.69,
        "A three-gate framework for transportability of transcriptomic signatures:\nan audit of adrenocortical carcinoma",
        ha="center",
        va="center",
        fontsize=15,
    )
    ax.text(0.5, 0.55, "Jiakang Zhao", ha="center", va="center", fontsize=12)
    ax.text(0.5, 0.49, "Version 2 | 10 November 2026", ha="center", va="center", fontsize=10)
    contents = [
        "Supplementary Methods 1 | Simulation and analysis parameters",
        "Supplementary Table 1 | ACC pair-level provenance registry",
        "Supplementary Table 2 | Gate 1 pure and realistic selection nulls",
        "Supplementary Table 3 | Independent transport and stratified Cox models",
        "Supplementary Table 4 | Per-axis R-squared with bootstrap intervals",
        "Supplementary Table 5 | Selection-path optimism sensitivity",
        "Supplementary Table 6 | Pituitary positive-control robustness",
        "Supplementary Table 7 | Pituitary invasion negative case",
        "Supplementary Table 8 | ssGSEA role-aware adjustment and mediation",
        "Supplementary Table 9 | Known-truth component and joint operating characteristics",
        "Supplementary Table 10 | Frozen preflight predictive-validity analysis",
        "Supplementary Software | rata-tools 0.1.2",
    ]
    ax.text(0.20, 0.39, "Contents", fontsize=11, fontweight="bold", va="top")
    ax.text(0.20, 0.355, "\n".join(contents), fontsize=8.2, va="top", linespacing=1.65)
    page_counter[0] += 1
    footer(fig, page_counter[0])
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    page_counter = [0]
    with PdfPages(OUT) as pdf:
        add_cover(pdf, page_counter)

        add_text_page(
            pdf,
            "Supplementary Methods 1. Simulation and analysis parameters",
            """
            Data provenance
            - GEO SuperSeries/SubSeries, shared arrays, patient identifiers where available,
              and technical replicates were checked before cohorts were counted as independent.
            - GSE10927/GSE33371, GSE19750/GSE19776, and GSE49278/GSE49280 were collapsed into
              array families for evidence-capacity calculations.
            - GSE76021 was treated as a paediatric event-free-survival cohort and was not merged
              with adult ACC overall survival.

            Selection nulls and selection cross-validation
            - Fixed-formula ACC nulls matched the observed candidate-pool size, selected feature
              count, sample size, and class balance.
            - Pure null contained no feature-outcome signal. The realistic mixture null assigned
              a standardized effect of 0.20 to 5% of candidate features.
            - Decision threshold for each realistic null was its 95th percentile.
            - Selection cross-validation used five stratified folds. Selection was repeated within
              each training fold and performance was evaluated in the held-out fold.
            - Pituitary positive control used 6,456 eligible genes. Pituitary invasion used a
              discovery candidate pool of 18,827 genes.

            Gate 2
            - Survival: within-cohort score standardization; cohort-stratified one-degree-of-freedom
              Cox model; at least two RATA-unseen adult cohorts; at least 10 events per cohort and
              20 total events; common HR above 1 with 95% CI excluding 1; concordant cohort direction.
            - Binary: endpoint-specific external AUC threshold. Multi-cohort binary analyses used
              the minimum-AUC rule.
            - The survival and binary rules were not interchanged.

            Gate 3
            - Applied only to signatures passing Gate 1 with an independent pair.
            - Target, confounder, mediator, and no-adjust axes were fixed before analysis.
            - Target over-adjustment and mediator adjustment were reported separately.
            - Direct and mediated associations were descriptive because mediation assumptions
              cannot be verified in these observational cohorts.

            Resampling
            - AUC confidence intervals used patient-level percentile bootstrap.
            - The ssGSEA mediation analysis used 500 cohort-stratified percentile bootstrap
              replicates; the valid number is reported in Supplementary Table 8.
            - Known-truth simulation used 300 runs per scenario and Wilson 95% CIs.
            """,
            page_counter,
        )

        pairs = pd.read_csv(REGISTRY / "ACC_Provenance_Pairs_v3.csv")
        add_table_pages(
            pdf,
            "Supplementary Table 1A. ACC pair-level provenance registry: identity and grades",
            pairs,
            [
                "signature_id",
                "source_pmid",
                "pair_role",
                "cohort",
                "cohort_family",
                "platform",
                "design_independence_grade",
                "rata_unseen_grade",
                "reuse_cluster_id",
            ],
            page_counter,
            rows_per_page=16,
            max_colwidth=19,
            fontsize=5.8,
        )
        add_table_pages(
            pdf,
            "Supplementary Table 1B. ACC pair-level registry: samples, endpoints, and notes",
            pairs,
            [
                "signature_id",
                "cohort",
                "expression_n",
                "survival_n",
                "events",
                "endpoint",
                "evidence_note",
            ],
            page_counter,
            rows_per_page=16,
            max_colwidth=38,
            fontsize=5.8,
        )

        gate1 = pd.read_csv(RESULTS / "RATA_v5_double_null_selection_gate.csv")
        add_table_pages(
            pdf,
            "Supplementary Table 2. Gate 1 pure and realistic selection nulls",
            gate1,
            [
                "signature",
                "candidate_pool",
                "selected_k",
                "observed_apparent_auc",
                "pure_null_q95",
                "pure_null_percentile",
                "realistic_null_q95",
                "realistic_null_percentile",
                "realistic_null_p",
                "selection_gate_decision",
                "simulations_per_null",
            ],
            page_counter,
            rows_per_page=6,
            max_colwidth=22,
            fontsize=6.0,
        )

        transport = pd.read_csv(RESULTS / "RATA_v3_pair_registry_and_transport.csv")
        add_table_pages(
            pdf,
            "Supplementary Table 3A. Independent transport: C-index difference-in-differences",
            transport,
            [
                "signature",
                "external_cohort",
                "events",
                "signature_reference_cindex",
                "signature_external_cindex",
                "cindex_did",
                "cindex_did_ci_low",
                "cindex_did_ci_high",
                "did_status",
            ],
            page_counter,
            rows_per_page=13,
            max_colwidth=24,
            fontsize=5.9,
        )
        add_table_pages(
            pdf,
            "Supplementary Table 3B. Independent transport: stratified Cox and heterogeneity",
            transport,
            [
                "signature",
                "external_cohort",
                "common_cox_hr",
                "common_cox_ci_low",
                "common_cox_ci_high",
                "common_cox_p",
                "q",
                "q_p",
                "i2",
            ],
            page_counter,
            rows_per_page=13,
            max_colwidth=24,
            fontsize=6.0,
        )

        axes = pd.read_csv(RESULTS / "RATA_v4_per_axis_r2_ci.csv")
        add_table_pages(
            pdf,
            "Supplementary Table 4. Per-axis R-squared and bootstrap CIs",
            axes,
            [
                "signature",
                "cohort",
                "cohort_role",
                "axis",
                "single_axis_r2",
                "single_axis_r2_ci_low",
                "single_axis_r2_ci_high",
                "partial_r2",
                "partial_r2_ci_low",
                "partial_r2_ci_high",
                "stable_partial_axis",
            ],
            page_counter,
            rows_per_page=24,
            max_colwidth=20,
            fontsize=5.6,
        )

        optimism = pd.read_csv(RESULTS / "RATA_v3_selection_optimism_signature_map.csv")
        add_table_pages(
            pdf,
            "Supplementary Table 5. Selection-path optimism sensitivity",
            optimism,
            [
                "signature",
                "reported_candidate_pool",
                "simulated_pool",
                "selected_k",
                "optimism_median",
                "optimism_ci_low",
                "optimism_ci_high",
                "optimism_q95",
                "interpretation",
            ],
            page_counter,
            rows_per_page=6,
            max_colwidth=30,
            fontsize=5.9,
        )

        pituitary = json.loads(
            (RESULTS / "RATA_v5_pituitary_positive_control_provenance.json").read_text(encoding="utf-8")
        )
        marker = pd.read_csv(RESULTS / "RATA_v5_pituitary_marker_robustness.csv")
        proxy_models = pd.read_csv(RESULTS / "RATA_v5_pituitary_proxy_sensitivity_models.csv")
        proxy_controls = pd.read_csv(RESULTS / "RATA_v5_pituitary_expression_proxy_negative_controls.csv")
        add_text_page(
            pdf,
            "Supplementary Table 6A. Pituitary positive-control provenance",
            "Official group counts:\n"
            + json.dumps(pituitary, indent=2, ensure_ascii=False),
            page_counter,
            fontsize=6.8,
        )
        add_table_pages(
            pdf,
            "Supplementary Table 6B. Seven-marker and gene-coverage robustness",
            marker,
            list(marker.columns),
            page_counter,
            rows_per_page=1,
            max_colwidth=28,
            fontsize=6.0,
        )
        add_table_pages(
            pdf,
            "Supplementary Table 6C. Sex and principal-component sensitivity models",
            proxy_models,
            list(proxy_models.columns),
            page_counter,
            rows_per_page=1,
            max_colwidth=28,
            fontsize=6.0,
        )
        add_table_pages(
            pdf,
            "Supplementary Table 6D. Expression-based negative-control proxies",
            proxy_controls,
            list(proxy_controls.columns),
            page_counter,
            rows_per_page=6,
            max_colwidth=28,
            fontsize=6.5,
        )

        invasion = pd.read_csv(RESULTS / "RATA_v5_pituitary_invasion_cohort_auc.csv")
        invasion_json = json.loads(
            (RESULTS / "RATA_v5_pituitary_invasion_transport.json").read_text(encoding="utf-8")
        )
        confound = pd.read_csv(RESULTS / "RATA_v5_GSE260487_invasion_lineage_confounding.csv")
        add_table_pages(
            pdf,
            "Supplementary Table 7A. Pituitary invasion external AUCs",
            invasion,
            list(invasion.columns),
            page_counter,
            rows_per_page=3,
            max_colwidth=24,
            fontsize=6.8,
        )
        add_table_pages(
            pdf,
            "Supplementary Table 7B. Complete invasion-lineage confounding in GSE260487",
            confound,
            list(confound.columns),
            page_counter,
            rows_per_page=1,
            max_colwidth=24,
            fontsize=6.6,
        )
        add_text_page(
            pdf,
            "Supplementary Table 7C. Invasion selection and transport decision record",
            json.dumps(invasion_json, indent=2, ensure_ascii=False),
            page_counter,
            fontsize=6.8,
        )

        role_adjust = pd.read_csv(RESULTS / "RATA_v5_ssgsea_role_aware_adjustment.csv")
        mediation = pd.read_csv(RESULTS / "RATA_v5_ssgsea_mediation_bootstrap.csv")
        add_table_pages(
            pdf,
            "Supplementary Table 8A. ssGSEA role-aware Cox models",
            role_adjust,
            list(role_adjust.columns),
            page_counter,
            rows_per_page=5,
            max_colwidth=25,
            fontsize=5.9,
        )
        add_table_pages(
            pdf,
            "Supplementary Table 8B. ssGSEA mediation bootstrap",
            mediation,
            list(mediation.columns),
            page_counter,
            rows_per_page=5,
            max_colwidth=28,
            fontsize=6.0,
        )
        add_text_page(
            pdf,
            "Supplementary Table 8C. Interpretation of mediation intervals",
            """
            Percentile bootstrap intervals for mediated proportions can include values below zero
            when direct and indirect effects have opposite signs. Such intervals are reported
            descriptively and are not interpreted as negative mediation proportions. With 44
            samples and 33 events across two same-platform cohorts, the ssGSEA result is a modest
            cross-cohort prognostic association rather than a validated clinical biomarker.
            """,
            page_counter,
        )

        component = pd.read_csv(RESULTS / "RATA_v5_known_truth_gate_simulation_summary.csv")
        joint = pd.read_csv(RESULTS / "RATA_v5_joint_gate_operating_characteristics_long.csv")
        add_table_pages(
            pdf,
            "Supplementary Table 9A. Known-truth simulation by scenario",
            component,
            list(component.columns),
            page_counter,
            rows_per_page=5,
            max_colwidth=22,
            fontsize=6.0,
        )
        add_table_pages(
            pdf,
            "Supplementary Table 9B. Component and joint operating characteristics",
            joint,
            list(joint.columns),
            page_counter,
            rows_per_page=15,
            max_colwidth=26,
            fontsize=5.8,
        )

        predictive = json.loads(
            (RESULTS / "RATA_v5_predictive_validity_summary.json").read_text(encoding="utf-8")
        )
        add_text_page(
            pdf,
            "Supplementary Table 10. Frozen preflight predictive-validity analysis",
            json.dumps(predictive, indent=2, ensure_ascii=False),
            page_counter,
            fontsize=7.0,
        )

        readme = (ROOT / "rata_package" / "README.md").read_text(encoding="utf-8")
        add_text_page(
            pdf,
            "Supplementary Software. rata-tools 0.1.2",
            readme,
            page_counter,
            fontsize=7.0,
        )

    print(OUT)
    print(f"pages={page_counter[0]}")


if __name__ == "__main__":
    main()
