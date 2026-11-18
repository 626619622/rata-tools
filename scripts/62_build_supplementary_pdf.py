from pathlib import Path
import json
import textwrap

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
OUT = ROOT / "manuscript" / "RATA_Paper1_Supplementary_v1.pdf"


def add_text_page(pdf, title, text):
    fig, ax = plt.subplots(figsize=(11, 8.5))
    ax.axis("off")
    ax.text(0.02, 0.98, title, fontsize=13, fontweight="bold", va="top")
    ax.text(
        0.02,
        0.92,
        text,
        fontsize=7.2,
        va="top",
        family="DejaVu Sans Mono",
        linespacing=1.25,
    )
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def table_text(frame, max_rows=45):
    return frame.head(max_rows).to_string(index=False, max_colwidth=28)


def main():
    with PdfPages(OUT) as pdf:
        add_text_page(
            pdf,
            "Supplementary Methods 1. Simulation and analysis parameters",
            textwrap.dedent(
                """
                RATA Paper 1 supplementary material
                Date: 2026-11-10

                Selection null:
                - sample size 79; 28 events for ACC fixed-formula simulations
                - pure null: no feature-outcome signal
                - realistic null: 5% weak features, standardized effect 0.20
                - 500-1000 simulations depending on analysis
                - apparent AUC compared with same pool/k null

                Selection cross-validation:
                - five stratified folds
                - selection repeated within each training fold
                - held-out AUC averaged across folds

                Gate 2:
                - survival: within-cohort standardization; cohort-stratified 1-df Cox;
                  >=2 unseen cohorts; >=10 events/cohort; >=20 total events
                - binary: endpoint-specific threshold; multi-cohort minimum AUC rule

                Gate 3:
                - target, confounder and mediator roles fixed before adjustment
                - target over-adjustment and mediator adjustment reported separately

                Bootstrap:
                - percentile confidence intervals
                - mediation: 500 cohort-stratified replicates
                - AUC: 1500-2000 patient-level replicates

                Known-truth simulation:
                - 300 runs per scenario
                - pure null, true portable, confounded only, attenuated true effect,
                  true non-transport
                """
            ).strip(),
        )

        pairs = pd.read_csv(ROOT / "registry" / "ACC_Provenance_Pairs_v3.csv")
        add_text_page(
            pdf,
            "Supplementary Table 1. ACC pair-level provenance registry",
            table_text(
                pairs[
                    [
                        "signature_id",
                        "pair_role",
                        "cohort",
                        "expression_n",
                        "survival_n",
                        "events",
                        "endpoint",
                        "design_independence_grade",
                        "rata_unseen_grade",
                        "reuse_cluster_id",
                    ]
                ]
            ),
        )

        gate1 = pd.read_csv(RESULTS / "RATA_v5_double_null_selection_gate.csv")
        add_text_page(
            pdf,
            "Supplementary Table 2. Gate 1 pure and realistic selection nulls",
            table_text(
                gate1[
                    [
                        "signature",
                        "candidate_pool",
                        "selected_k",
                        "observed_apparent_auc",
                        "pure_null_q95",
                        "pure_null_percentile",
                        "pure_null_p",
                        "realistic_null_q95",
                        "realistic_null_percentile",
                        "realistic_null_p",
                        "selection_gate_decision",
                    ]
                ]
            ),
        )

        transport = pd.read_csv(
            RESULTS / "RATA_v3_pair_registry_and_transport.csv"
        )
        add_text_page(
            pdf,
            "Supplementary Table 3. Transportability and stratified Cox results",
            table_text(
                transport[
                    [
                        "signature",
                        "reference_cohorts",
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
                    ]
                ]
            ),
        )

        axes = pd.read_csv(RESULTS / "RATA_v4_per_axis_r2_ci.csv")
        add_text_page(
            pdf,
            "Supplementary Table 4. Per-axis R2 and bootstrap intervals",
            table_text(
                axes[
                    [
                        "signature",
                        "cohort",
                        "cohort_role",
                        "axis",
                        "single_axis_r2",
                        "partial_r2",
                        "partial_r2_ci_low",
                        "partial_r2_ci_high",
                        "stable_partial_axis",
                    ]
                ],
                max_rows=50,
            ),
        )

        optimism = pd.read_csv(
            RESULTS / "RATA_v3_selection_optimism_signature_map.csv"
        )
        add_text_page(
            pdf,
            "Supplementary Table 5. Selection-path optimism sensitivity",
            table_text(
                optimism[
                    [
                        "signature",
                        "reported_candidate_pool",
                        "simulated_pool",
                        "selected_k",
                        "optimism_median",
                        "optimism_ci_low",
                        "optimism_ci_high",
                        "optimism_q95",
                    ]
                ]
            ),
        )

        pituitary = json.loads(
            (RESULTS / "RATA_v5_pituitary_positive_control_provenance.json").read_text(
                encoding="utf-8"
            )
        )
        proxy = pd.read_csv(
            RESULTS / "RATA_v5_pituitary_proxy_sensitivity_models.csv"
        )
        add_text_page(
            pdf,
            "Supplementary Table 6. Pituitary positive-control robustness",
            "Official GSE147786 group counts: " + json.dumps(
                pituitary["tumor_group_counts"]
            ) + "\n\n" + table_text(proxy),
        )

        invasion = pd.read_csv(
            RESULTS / "RATA_v5_pituitary_invasion_cohort_auc.csv"
        )
        confound = pd.read_csv(
            RESULTS / "RATA_v5_GSE260487_invasion_lineage_confounding.csv"
        )
        add_text_page(
            pdf,
            "Supplementary Table 7. Pituitary invasion negative case",
            table_text(invasion) + "\n\n" + table_text(confound),
        )

        predictive = json.loads(
            (RESULTS / "RATA_v5_predictive_validity_summary.json").read_text(
                encoding="utf-8"
            )
        )
        add_text_page(
            pdf,
            "Supplementary Table 8. Frozen preflight predictive-validity result",
            json.dumps(predictive, indent=2),
        )

        readme = (
            ROOT
            / "rata_package"
            / "README.md"
        ).read_text(encoding="utf-8")
        add_text_page(
            pdf,
            "Supplementary Software. rata-tools 0.1.2",
            readme,
        )

    print(OUT)


if __name__ == "__main__":
    main()
