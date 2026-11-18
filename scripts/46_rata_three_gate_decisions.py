"""Assemble final three-gate decisions for ACC signatures."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def main() -> None:
    selection = pd.read_csv(
        RESULTS / "RATA_v5_double_null_selection_gate.csv"
    ).set_index("signature")
    transport = pd.read_csv(
        RESULTS / "RATA_v3_pair_registry_and_transport.csv"
    )
    independent_pairs = transport[
        transport["external_cohort"].isin(["TCGA", "GSE33371", "GSE19750"])
    ]
    independent_counts = (
        independent_pairs.groupby("signature").size().to_dict()
    )
    independent_cox = transport[
        transport["external_cohort"].eq(
            "INDEPENDENT_ONLY_STRATIFIED_COX"
        )
    ].set_index("signature")
    role_aware = json.loads(
        (RESULTS / "RATA_v5_ssgsea_role_aware_adjustment.json").read_text(
            encoding="utf-8"
        )
    )
    capacity = json.loads(
        (RESULTS / "RATA_v5_evidence_capacity_metrics.json").read_text(
            encoding="utf-8"
        )
    )

    rows = []
    for signature, selection_row in selection.iterrows():
        pair_count = int(independent_counts.get(signature, 0))
        gate1 = selection_row["selection_gate_decision"] == "pass"

        gate2 = False
        gate2_status = "untestable_no_independent_pair"
        if pair_count == 1:
            gate2_status = "provisional_single_independent_pair"
        elif pair_count >= 2:
            if (
                signature in independent_cox.index
                and independent_cox.loc[signature, "common_cox_ci_low"] > 1
                and independent_cox.loc[signature, "common_cox_hr"] > 1
            ):
                gate2 = True
                gate2_status = "pass_independent_pooled_cox"
            else:
                gate2_status = "fail_or_indeterminate_pooled_cox"

        gate3 = False
        gate3_status = "not_evaluated_before_gate2"
        if signature == "immune_ssgsea_13gene_2022":
            gate3 = bool(role_aware["gate3_role_aware_pass"])
            gate3_status = (
                "pass_confounder_adjusted_not_target"
                if gate3
                else "fail_confounder_adjusted"
            )

        rows.append(
            {
                "signature": signature,
                "evidence_capacity_effective_adult_clusters": capacity[
                    "adult_non_tcga_effective_cluster_number_herfindahl"
                ],
                "evidence_capacity_adult_events": capacity[
                    "total_adult_events_across_development_and_external"
                ],
                "independent_pair_count": pair_count,
                "gate1_selection": gate1,
                "gate1_percentile": selection_row[
                    "realistic_null_percentile"
                ],
                "gate1_p": selection_row["realistic_null_p"],
                "gate2_independent_transport": gate2,
                "gate2_status": gate2_status,
                "gate3_role_aware": gate3,
                "gate3_status": gate3_status,
                "all_three_gates_pass": gate1 and gate2 and gate3,
                "known_axis_note": (
                    "Formal descriptive mediation by proliferation is 30.9% "
                    "(unadjusted denominator) or 39.0% (confounder-adjusted "
                    "denominator), with wide CIs; stroma/lineage "
                    "confounder-adjusted HR remains >1. Signature-immune-axis "
                    "correlation is only modest."
                    if signature == "immune_ssgsea_13gene_2022"
                    else ""
                ),
            }
        )

    decision = pd.DataFrame(rows)
    decision.to_csv(
        RESULTS / "RATA_v5_three_gate_decisions.csv",
        index=False,
    )
    payload = {
        "gate1_count_pass": int(decision["gate1_selection"].sum()),
        "gate2_count_pass": int(decision["gate2_independent_transport"].sum()),
        "gate3_count_pass": int(decision["gate3_role_aware"].sum()),
        "all_three_gate_pass": decision.loc[
            decision["all_three_gates_pass"],
            "signature",
        ].tolist(),
        "decisions": decision.to_dict(orient="records"),
    }
    (RESULTS / "RATA_v5_three_gate_decisions.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    print(decision.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
