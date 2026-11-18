"""Build the four-table Bioinformatics supplementary PDF."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
REGISTRY = ROOT / "registry"
OUT = ROOT / "manuscript" / "RATA_Bioinformatics_Supplementary_v1.pdf"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = load_module("rata_supp_base", ROOT / "scripts" / "73_build_supplementary_v2.py")
FIX = load_module("rata_supp_fix", ROOT / "scripts" / "74_fix_supplementary_v3.py")


def add_cover(pdf, page_counter):
    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.axis("off")
    ax.text(0.5, 0.80, "Supplementary Material", ha="center", va="center", fontsize=22, fontweight="bold")
    ax.text(
        0.5,
        0.67,
        "RATA: a role-aware three-gate framework and software\nfor auditing transportability of transcriptomic signatures",
        ha="center",
        va="center",
        fontsize=15,
    )
    ax.text(0.5, 0.54, "Jiakang Zhao", ha="center", va="center", fontsize=12)
    ax.text(0.5, 0.48, "Version 1 | 10 November 2026", ha="center", va="center", fontsize=10)
    contents = [
        "Supplementary Note 1 | Framework, simulation and software parameters",
        "Supplementary Table S1 | ACC evidence capacity, provenance and transport",
        "Supplementary Table S2 | ACC selection and role-aware analyses",
        "Supplementary Table S3 | Pituitary controls and known-truth simulation",
        "Supplementary Table S4 | Software API, tests, runtime and predictive validity",
    ]
    ax.text(0.24, 0.38, "Contents", fontsize=11, fontweight="bold", va="top")
    ax.text(0.24, 0.345, "\n".join(contents), fontsize=8.5, va="top", linespacing=1.75)
    page_counter[0] += 1
    BASE.footer(fig, page_counter[0])
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def main():
    BASE.OUT = OUT
    BASE.add_text_page = lambda pdf, title, text, page_counter, fontsize=7.4: FIX.patched_add_text_page(
        BASE, pdf, title, text, page_counter, fontsize
    )
    BASE.add_table_pages = (
        lambda pdf, title, frame, columns, page_counter, rows_per_page, max_colwidth=24, fontsize=6.2: FIX.patched_add_table_pages(
            BASE,
            pdf,
            title,
            frame,
            columns,
            page_counter,
            rows_per_page,
            max_colwidth,
            fontsize,
        )
    )

    page_counter = [0]
    with BASE.PdfPages(OUT) as pdf:
        add_cover(pdf, page_counter)
        BASE.add_text_page(
            pdf,
            "Supplementary Note 1. Framework, simulation and software parameters",
            """
            RATA separates an evidence audit into reusable records:
            (i) reuse-aware evidence capacity, (ii) selection robustness, (iii) endpoint-
            specific independent transport and (iv) role-aware interpretation.

            Provenance
            - GEO SuperSeries/SubSeries relations, shared arrays, patient identifiers where
              available and technical replicates were checked before clusters were counted.
            - GSE10927/GSE33371, GSE19750/GSE19776 and GSE49278/GSE49280 were collapsed
              into reuse families.
            - GSE76021 was retained as a paediatric event-free-survival cohort and was not
              merged with adult ACC overall survival.

            Evidence capacity
            - Claims were counted at the signature-cohort pair level.
            - Effective clusters used the inverse Herfindahl concentration.
            - Total events and independent-only events were reported separately.
            - Platform diversity was recorded rather than treated as an independent cohort.

            Gate 1
            - Fixed-formula nulls matched candidate-pool size, selected feature count,
              sample size and class balance.
            - Pure null contained no outcome signal.
            - Realistic null assigned standardized effect 0.20 to 5% of features.
            - Selection cross-validation repeated feature selection inside each training fold.
            - Pituitary positive control used 6,456 eligible genes; invasion used 18,827.

            Gate 2
            - Binary analyses used endpoint-specific AUC thresholds and a minimum-cohort rule.
            - Survival Gate 2 required at least two unseen adult clusters, at least 10 events
              per cohort, at least 20 total events, within-cohort score standardization,
              concordant cohort direction and a common HR with 95% CI excluding 1.
            - Per-cohort HR, Cochran's Q, I-squared and instability flags were returned.

            Gate 3
            - Applied only after a signature passed Gate 1 and had an independent pair.
            - Target, confounder, mediator and no-adjust axes were fixed before adjustment.
            - Mediation used 500 cohort-stratified percentile bootstrap replicates and was
              interpreted descriptively.

            Software
            - rata-tools 0.2.0 uses Python >=3.10, NumPy, SciPy, scikit-learn and statsmodels.
            - Thirteen tests cover capacity, C-index, censoring, selection-CV, binary and
              survival transport, heterogeneity, decision states and input validation.
            - The package exposes a Python API and `rata-tools` command-line interface.
            """,
            page_counter,
        )

        pairs = pd.read_csv(REGISTRY / "ACC_Provenance_Pairs_v3.csv")
        transport = pd.read_csv(RESULTS / "RATA_v3_pair_registry_and_transport.csv")
        BASE.add_table_pages(
            pdf,
            "Supplementary Table S1A. ACC pair-level provenance registry",
            pairs,
            [
                "signature_id",
                "source_pmid",
                "pair_role",
                "cohort",
                "platform",
                "expression_n",
                "survival_n",
                "events",
                "endpoint",
                "design_independence_grade",
                "rata_unseen_grade",
                "reuse_cluster_id",
            ],
            page_counter,
            rows_per_page=16,
            max_colwidth=22,
            fontsize=5.5,
        )
        BASE.add_table_pages(
            pdf,
            "Supplementary Table S1B. ACC transport and stratified Cox results",
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
                "common_cox_hr",
                "common_cox_ci_low",
                "common_cox_ci_high",
                "i2",
                "did_status",
            ],
            page_counter,
            rows_per_page=13,
            max_colwidth=22,
            fontsize=5.4,
        )

        gate1 = pd.read_csv(RESULTS / "RATA_v5_double_null_selection_gate.csv")
        axes = pd.read_csv(RESULTS / "RATA_v4_per_axis_r2_ci.csv")
        optimism = pd.read_csv(RESULTS / "RATA_v3_selection_optimism_signature_map.csv")
        role_adjust = pd.read_csv(RESULTS / "RATA_v5_ssgsea_role_aware_adjustment.csv")
        mediation = pd.read_csv(RESULTS / "RATA_v5_ssgsea_mediation_bootstrap.csv")
        BASE.add_table_pages(
            pdf,
            "Supplementary Table S2A. ACC pure and realistic selection nulls",
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
            fontsize=5.9,
        )
        BASE.add_table_pages(
            pdf,
            "Supplementary Table S2B. Per-axis R-squared and bootstrap intervals",
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
            fontsize=5.5,
        )
        BASE.add_table_pages(
            pdf,
            "Supplementary Table S2C. Selection-path optimism and ssGSEA role-aware models",
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
            ],
            page_counter,
            rows_per_page=6,
            max_colwidth=24,
            fontsize=6.0,
        )
        BASE.add_table_pages(
            pdf,
            "Supplementary Table S2D. ssGSEA Cox sensitivity models",
            role_adjust,
            list(role_adjust.columns),
            page_counter,
            rows_per_page=5,
            max_colwidth=24,
            fontsize=5.8,
        )
        BASE.add_table_pages(
            pdf,
            "Supplementary Table S2E. ssGSEA mediation bootstrap",
            mediation,
            list(mediation.columns),
            page_counter,
            rows_per_page=5,
            max_colwidth=27,
            fontsize=5.9,
        )

        marker = pd.read_csv(RESULTS / "RATA_v5_pituitary_marker_robustness.csv")
        proxy = pd.read_csv(RESULTS / "RATA_v5_pituitary_proxy_sensitivity_models.csv")
        invasion = pd.read_csv(RESULTS / "RATA_v5_pituitary_invasion_cohort_auc.csv")
        confound = pd.read_csv(RESULTS / "RATA_v5_GSE260487_invasion_lineage_confounding.csv")
        pituitary = json.loads(
            (RESULTS / "RATA_v5_pituitary_positive_control_provenance.json").read_text(encoding="utf-8")
        )
        BASE.add_text_page(
            pdf,
            "Supplementary Table S3A. Pituitary positive-control provenance",
            json.dumps(pituitary, indent=2, ensure_ascii=False),
            page_counter,
            fontsize=6.8,
        )
        BASE.add_table_pages(
            pdf,
            "Supplementary Table S3B. Seven-marker and principal-component robustness",
            marker,
            list(marker.columns),
            page_counter,
            rows_per_page=1,
            max_colwidth=28,
            fontsize=5.8,
        )
        BASE.add_table_pages(
            pdf,
            "Supplementary Table S3C. Pituitary principal-component sensitivity",
            proxy,
            list(proxy.columns),
            page_counter,
            rows_per_page=1,
            max_colwidth=26,
            fontsize=5.9,
        )
        BASE.add_table_pages(
            pdf,
            "Supplementary Table S3D. Pituitary invasion external AUCs",
            invasion,
            list(invasion.columns),
            page_counter,
            rows_per_page=3,
            max_colwidth=24,
            fontsize=6.5,
        )
        BASE.add_table_pages(
            pdf,
            "Supplementary Table S3E. Complete invasion-lineage confounding",
            confound,
            list(confound.columns),
            page_counter,
            rows_per_page=1,
            max_colwidth=24,
            fontsize=6.2,
        )

        component = pd.read_csv(RESULTS / "RATA_v5_known_truth_gate_simulation_summary.csv")
        joint = pd.read_csv(RESULTS / "RATA_v5_joint_gate_operating_characteristics_long.csv")
        BASE.add_table_pages(
            pdf,
            "Supplementary Table S3F. Known-truth simulation by scenario",
            component,
            list(component.columns),
            page_counter,
            rows_per_page=5,
            max_colwidth=22,
            fontsize=5.9,
        )
        BASE.add_table_pages(
            pdf,
            "Supplementary Table S3G. Component and joint operating characteristics",
            joint,
            list(joint.columns),
            page_counter,
            rows_per_page=15,
            max_colwidth=25,
            fontsize=5.7,
        )

        runtime = pd.read_csv(RESULTS / "Bioinformatics_RuntimeBenchmark.csv")
        predictive = json.loads(
            (RESULTS / "RATA_v5_predictive_validity_summary.json").read_text(encoding="utf-8")
        )
        benchmark = json.loads(
            (RESULTS / "Bioinformatics_RuntimeBenchmark.json").read_text(encoding="utf-8")
        )
        BASE.add_table_pages(
            pdf,
            "Supplementary Table S4A. rata-tools 0.2.0 runtime benchmark",
            runtime,
            list(runtime.columns),
            page_counter,
            rows_per_page=5,
            max_colwidth=38,
            fontsize=6.2,
        )
        BASE.add_text_page(
            pdf,
            "Supplementary Table S4B. Benchmark environment",
            json.dumps(
                {
                    key: benchmark[key]
                    for key in [
                        "software_version",
                        "python",
                        "platform",
                        "processor",
                        "numpy",
                        "scipy",
                        "scikit_learn",
                        "statsmodels",
                    ]
                },
                indent=2,
            ),
            page_counter,
            fontsize=7.0,
        )
        BASE.add_text_page(
            pdf,
            "Supplementary Table S4C. Frozen predictive-validity analysis",
            json.dumps(predictive, indent=2, ensure_ascii=False),
            page_counter,
            fontsize=6.8,
        )
        BASE.add_text_page(
            pdf,
            "Supplementary Table S4D. Minimal vignette and release checks",
            """
            Minimal API example

            import numpy as np
            from rata_tools import evidence_capacity, selection_null_decision
            from rata_tools import three_gate_decision

            capacity = evidence_capacity(
                ["ASU", "ASU", "Michigan", "ENSAT", "ENSAT"],
                events_per_cluster={"ASU": 17, "Michigan": 16, "ENSAT": 20},
                independent_clusters={"ASU", "Michigan"},
                platform_per_cluster={"ASU": "GPL570", "Michigan": "GPL570",
                                      "ENSAT": "GPL570"},
            )
            selection = selection_null_decision(
                0.91, np.random.default_rng(1).normal(0.75, 0.05, 500)
            )
            decision = three_gate_decision(
                selection.decision, "positive_control_binary_pass",
                "role_integrity_pass",
            )
            print(capacity)
            print(decision.to_dict())

            Release checks
            - Package version: 0.2.0.
            - Tests: 13/13 passed with unittest discovery.
            - Wheel: rata_tools-0.2.0-py3-none-any.whl.
            - CI: GitHub Actions matrix for Python 3.10, 3.11 and 3.12.
            - License: MIT.
            - CLI: rata-tools --version and rata-tools demo.
            """,
            page_counter,
            fontsize=6.7,
        )

    print(OUT)
    print(f"pages={page_counter[0]}")


if __name__ == "__main__":
    main()
