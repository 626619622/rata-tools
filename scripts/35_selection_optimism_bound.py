"""Simulate a sensitivity bound for selection-path optimism.

This is intentionally not called a correction for the published coefficients.
It estimates how much apparent discrimination a top-k selection procedure can
create from pure noise under different candidate-pool sizes.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RANDOM_SEED = 20261109
N_SAMPLE = 79
N_EVENTS = 28
N_SIMULATIONS = 250
POOL_SIZES = [21, 37, 57, 100, 144, 275, 332, 1000, 10000]
SIGNATURE_SIZES = [3, 5, 7, 13]

SIGNATURE_POOLS = {
    "hypoxia_3gene_2021": (144, 3),
    "immune_irg_3gene_2022": (332, 3),
    "prognostic_3gene_2021": (985, 3),
    "immune_ssgsea_13gene_2022": (57, 13),
    "metabolic_5gene_2021": (37, 5),
    "atf_creb_7gene_2025": (21, 7),
}


def select_score(
    x: np.ndarray,
    y: np.ndarray,
    k: int,
) -> np.ndarray:
    event_mean = x[y == 1].mean(axis=0)
    control_mean = x[y == 0].mean(axis=0)
    effects = event_mean - control_mean
    selected = np.argsort(np.abs(effects))[-k:]
    signs = np.sign(effects[selected])
    return x[:, selected] @ signs


def evaluate_pool(
    pool_size: int,
    seed: int,
) -> list[dict]:
    rng = np.random.default_rng(seed)
    y_base = np.r_[np.ones(N_EVENTS), np.zeros(N_SAMPLE - N_EVENTS)]
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)

    optimism_values = {k: [] for k in SIGNATURE_SIZES}
    apparent_values = {k: [] for k in SIGNATURE_SIZES}
    cv_values = {k: [] for k in SIGNATURE_SIZES}

    for simulation in range(N_SIMULATIONS):
        x = rng.normal(size=(N_SAMPLE, pool_size))
        y = y_base.copy()
        rng.shuffle(y)
        fold_definitions = list(
            folds.split(np.zeros(len(y)), y)
        )
        fold_effects = []
        for train_indices, test_indices in fold_definitions:
            fold_effects.append(
                (
                    test_indices,
                    x[train_indices][y[train_indices] == 1].mean(axis=0)
                    - x[train_indices][y[train_indices] == 0].mean(axis=0),
                )
            )
        for k in SIGNATURE_SIZES:
            full_score = select_score(x, y, k)
            apparent = roc_auc_score(y, full_score)
            fold_aucs = []
            for test_indices, effects in fold_effects:
                selected = np.argsort(np.abs(effects))[-k:]
                signs = np.sign(effects[selected])
                test_score = x[test_indices][:, selected] @ signs
                if np.unique(y[test_indices]).size == 2:
                    fold_aucs.append(
                        roc_auc_score(y[test_indices], test_score)
                    )
            cross_validated = float(np.mean(fold_aucs))
            optimism_values[k].append(apparent - cross_validated)
            apparent_values[k].append(apparent)
            cv_values[k].append(cross_validated)

    rows = []
    for k in SIGNATURE_SIZES:
        values = np.asarray(optimism_values[k])
        rows.append(
            {
                "pool_size": pool_size,
                "selected_k": k,
                "simulations": N_SIMULATIONS,
                "null_apparent_auc_median": float(
                    np.median(apparent_values[k])
                ),
                "null_cv_auc_median": float(np.median(cv_values[k])),
                "optimism_median": float(np.median(values)),
                "optimism_ci_low": float(np.quantile(values, 0.025)),
                "optimism_ci_high": float(np.quantile(values, 0.975)),
                "optimism_q95": float(np.quantile(values, 0.95)),
            }
        )
    return rows


def main() -> None:
    all_rows = []
    for pool_index, pool_size in enumerate(POOL_SIZES):
        all_rows.extend(
            evaluate_pool(
                pool_size,
                seed=RANDOM_SEED + pool_index,
            )
        )
    table = pd.DataFrame(all_rows)
    table.to_csv(
        RESULTS / "RATA_v3_selection_optimism_bound.csv",
        index=False,
    )

    mapping_rows = []
    for signature, (pool_size, k) in SIGNATURE_POOLS.items():
        if pool_size not in POOL_SIZES:
            nearest = min(POOL_SIZES, key=lambda value: abs(value - pool_size))
        else:
            nearest = pool_size
        match = table[
            table["pool_size"].eq(nearest)
            & table["selected_k"].eq(k)
        ].iloc[0]
        mapping_rows.append(
            {
                "signature": signature,
                "reported_candidate_pool": pool_size,
                "simulated_pool": nearest,
                "selected_k": k,
                "optimism_median": match["optimism_median"],
                "optimism_ci_low": match["optimism_ci_low"],
                "optimism_ci_high": match["optimism_ci_high"],
                "optimism_q95": match["optimism_q95"],
                "interpretation": (
                    "Sensitivity bound under null top-k selection; "
                    "not subtracted from or added to the published AUC."
                ),
            }
        )
    mapping = pd.DataFrame(mapping_rows)
    mapping.to_csv(
        RESULTS / "RATA_v3_selection_optimism_signature_map.csv",
        index=False,
    )

    payload = {
        "sample_size": N_SAMPLE,
        "events": N_EVENTS,
        "simulations": N_SIMULATIONS,
        "overall_optimism_range_median": [
            float(table["optimism_median"].min()),
            float(table["optimism_median"].max()),
        ],
        "overall_optimism_range_q95": [
            float(table["optimism_q95"].min()),
            float(table["optimism_q95"].max()),
        ],
        "signature_map": mapping.to_dict(orient="records"),
    }
    (RESULTS / "RATA_v3_selection_optimism_bound.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    print(mapping.round(4).to_string(index=False))
    print("\nOverall range")
    print(json.dumps(payload["overall_optimism_range_median"], indent=2))
    print(json.dumps(payload["overall_optimism_range_q95"], indent=2))


if __name__ == "__main__":
    main()
