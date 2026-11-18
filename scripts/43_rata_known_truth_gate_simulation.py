"""Known-truth operating characteristics for the three-gate RATA framework."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import roc_auc_score


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RANDOM_SEED = 20261110
N_DEV = 120
N_EXT = 180
N_CANDIDATES = 500
N_TARGET = 20
N_CONFOUNDER = 20
SELECTED_K = 5
N_SIMULATIONS = 300
N_CALIBRATION = 500


def sigmoid(value: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-value))


def select_signature(
    x: np.ndarray,
    y: np.ndarray,
    k: int = SELECTED_K,
) -> tuple[np.ndarray, np.ndarray]:
    effects = x[y == 1].mean(axis=0) - x[y == 0].mean(axis=0)
    selected = np.argsort(np.abs(effects))[-k:]
    return selected, np.sign(effects[selected])


def score_with_signature(
    x: np.ndarray,
    selected: np.ndarray,
    signs: np.ndarray,
) -> np.ndarray:
    return x[:, selected] @ signs


def calibration_threshold(
    rng: np.random.Generator,
) -> tuple[float, np.ndarray]:
    values = []
    for _ in range(N_CALIBRATION):
        latent = rng.normal(size=N_DEV)
        y = rng.binomial(1, sigmoid(-0.4 + 0.25 * latent))
        x = rng.normal(size=(N_DEV, N_CANDIDATES))
        weak_genes = rng.choice(N_CANDIDATES, 25, replace=False)
        x[np.ix_(y == 1, weak_genes)] += 0.20
        selected, signs = select_signature(x, y)
        values.append(
            roc_auc_score(
                y,
                score_with_signature(x, selected, signs),
            )
        )
    values = np.asarray(values)
    return float(np.quantile(values, 0.95)), values


SCENARIOS = {
    "pure_null": {
        "dev_target_effect": 0.0,
        "ext_target_effect": 0.0,
        "confounder_effect": 0.0,
    },
    "true_portable": {
        "dev_target_effect": 2.5,
        "ext_target_effect": 2.2,
        "confounder_effect": 0.5,
    },
    "confounded_only": {
        "dev_target_effect": 0.0,
        "ext_target_effect": 0.0,
        "confounder_effect": 2.5,
    },
    "attenuated_true_effect": {
        "dev_target_effect": 2.5,
        "ext_target_effect": 0.80,
        "confounder_effect": 0.5,
    },
    "true_non_transport": {
        "dev_target_effect": 2.5,
        "ext_target_effect": -2.2,
        "confounder_effect": 0.5,
    },
}


def simulate_cohort(
    rng: np.random.Generator,
    n: int,
    target_effect: float,
    confounder_effect: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    target_latent = rng.normal(size=n)
    confounder_latent = rng.normal(size=n)
    x = rng.normal(size=(n, N_CANDIDATES))
    x[:, :N_TARGET] += 1.1 * target_latent[:, None]
    x[:, N_TARGET : N_TARGET + N_CONFOUNDER] += (
        1.1 * confounder_latent[:, None]
    )
    probability = sigmoid(
        -0.4
        + target_effect * target_latent
        + confounder_effect * confounder_latent
    )
    y = rng.binomial(1, probability)
    return x, y, confounder_latent


def gate3_pass(
    y_ext: np.ndarray,
    score_ext: np.ndarray,
    confounder_ext: np.ndarray,
) -> tuple[bool, float, float]:
    design = sm.add_constant(
        np.column_stack([score_ext, confounder_ext]),
        has_constant="add",
    )
    result = sm.Logit(y_ext, design).fit(disp=False, maxiter=1000)
    coefficient = float(result.params[1])
    odds_ratio = float(np.exp(coefficient))
    p_value = float(result.pvalues[1])
    passed = odds_ratio > 1 and p_value < 0.05
    return passed, odds_ratio, p_value


def main() -> None:
    rng = np.random.default_rng(RANDOM_SEED)
    gate1_threshold, calibration_values = calibration_threshold(rng)
    rows = []

    for scenario_index, (scenario, parameters) in enumerate(SCENARIOS.items()):
        for simulation in range(N_SIMULATIONS):
            dev_x, dev_y, _ = simulate_cohort(
                rng,
                N_DEV,
                parameters["dev_target_effect"],
                parameters["confounder_effect"],
            )
            ext_x, ext_y, ext_confounder = simulate_cohort(
                rng,
                N_EXT,
                parameters["ext_target_effect"],
                parameters["confounder_effect"],
            )
            selected, signs = select_signature(dev_x, dev_y)
            score_dev = score_with_signature(dev_x, selected, signs)
            score_ext = score_with_signature(ext_x, selected, signs)

            dev_auc = roc_auc_score(dev_y, score_dev)
            ext_auc = roc_auc_score(ext_y, score_ext)
            gate1 = dev_auc > gate1_threshold
            gate2 = (
                ext_auc > 0.60
                and np.sign(dev_auc - 0.5) == np.sign(ext_auc - 0.5)
            )
            gate3, adjusted_or, adjusted_p = gate3_pass(
                ext_y,
                score_ext,
                ext_confounder,
            )
            rows.append(
                {
                    "scenario": scenario,
                    "simulation": simulation,
                    "development_auc": dev_auc,
                    "external_auc": ext_auc,
                    "gate1_selection": gate1,
                    "gate2_independent_transport": gate2,
                    "gate3_role_aware_adjustment": gate3,
                    "all_gates_pass": gate1 and gate2 and gate3,
                    "adjusted_external_or": adjusted_or,
                    "adjusted_external_p": adjusted_p,
                }
            )

    result = pd.DataFrame(rows)
    result.to_csv(
        RESULTS / "RATA_v5_known_truth_gate_simulation_per_run.csv",
        index=False,
    )
    summary = (
        result.groupby("scenario", as_index=False)
        .agg(
            runs=("simulation", "size"),
            gate1_pass_rate=("gate1_selection", "mean"),
            gate2_pass_rate=("gate2_independent_transport", "mean"),
            gate3_pass_rate=("gate3_role_aware_adjustment", "mean"),
            all_gates_pass_rate=("all_gates_pass", "mean"),
            median_development_auc=("development_auc", "median"),
            median_external_auc=("external_auc", "median"),
            median_adjusted_external_or=("adjusted_external_or", "median"),
        )
    )
    summary.to_csv(
        RESULTS / "RATA_v5_known_truth_gate_simulation_summary.csv",
        index=False,
    )

    pure_null_false_portable = float(
        result.loc[result["scenario"].eq("pure_null"), "all_gates_pass"].mean()
    )
    confounded_false_mechanistic = float(
        result.loc[
            result["scenario"].eq("confounded_only"),
            "all_gates_pass",
        ].mean()
    )
    payload = {
        "gate1_realistic_null_q95": gate1_threshold,
        "gate1_calibration_median": float(np.median(calibration_values)),
        "simulations_per_scenario": N_SIMULATIONS,
        "pure_null_false_portable_rate": pure_null_false_portable,
        "confounded_false_mechanistic_pass_rate": confounded_false_mechanistic,
        "summary": summary.to_dict(orient="records"),
        "gate_definitions": {
            "gate1_selection": "development apparent AUC > realistic-mixture-null q95",
            "gate2_independent_transport": (
                "independent external AUC>0.60 and direction concordant"
            ),
            "gate3_role_aware_adjustment": (
                "adjusted external score OR>1 with p<0.05 after adjusting "
                "pre-specified confounder, not target"
            ),
        },
    }
    (RESULTS / "RATA_v5_known_truth_gate_simulation.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    print(summary.round(4).to_string(index=False))
    print("\nGate1 threshold:", round(gate1_threshold, 4))
    print("Pure-null false portable:", round(pure_null_false_portable, 4))
    print(
        "Confounded false mechanistic pass:",
        round(confounded_false_mechanistic, 4),
    )


if __name__ == "__main__":
    main()
