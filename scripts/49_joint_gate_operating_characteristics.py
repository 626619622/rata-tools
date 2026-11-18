"""Joint gate pass rates with binomial confidence intervals."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from statsmodels.stats.proportion import proportion_confint


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def main() -> None:
    runs = pd.read_csv(
        RESULTS / "RATA_v5_known_truth_gate_simulation_per_run.csv"
    )
    combinations = {
        "Gate1_only": runs["gate1_selection"],
        "Gate1_plus_Gate2": (
            runs["gate1_selection"] & runs["gate2_independent_transport"]
        ),
        "Gate1_plus_Gate2_plus_Gate3": (
            runs["gate1_selection"]
            & runs["gate2_independent_transport"]
            & runs["gate3_role_aware_adjustment"]
        ),
    }
    rows = []
    for scenario in [
        "pure_null",
        "confounded_only",
        "true_non_transport",
        "true_portable",
        "attenuated_true_effect",
    ]:
        scenario_mask = runs["scenario"].eq(scenario)
        for combination, values in combinations.items():
            subset = values[scenario_mask]
            successes = int(subset.sum())
            total = int(len(subset))
            low, high = proportion_confint(
                successes,
                total,
                alpha=0.05,
                method="wilson",
            )
            rows.append(
                {
                    "scenario": scenario,
                    "gate_combination": combination,
                    "successes": successes,
                    "runs": total,
                    "pass_rate": successes / total,
                    "ci_low": low,
                    "ci_high": high,
                }
            )

    long = pd.DataFrame(rows)
    long.to_csv(
        RESULTS / "RATA_v5_joint_gate_operating_characteristics_long.csv",
        index=False,
    )
    wide = long.pivot(
        index="gate_combination",
        columns="scenario",
        values="pass_rate",
    ).reset_index()
    wide.to_csv(
        RESULTS / "RATA_v5_joint_gate_operating_characteristics.csv",
        index=False,
    )
    payload = {
        "confidence_interval": "Wilson 95%",
        "operating_characteristics": long.to_dict(orient="records"),
    }
    (RESULTS / "RATA_v5_joint_gate_operating_characteristics.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    print(
        wide.round(4).to_string(index=False)
    )


if __name__ == "__main__":
    main()
