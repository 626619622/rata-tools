"""Place each observed apparent AUC in a pure top-k selection null distribution."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RANDOM_SEED = 20261109
N_SAMPLE = 79
N_EVENTS = 28
N_SIMULATIONS = 500

SIGNATURE_POOLS = {
    "hypoxia_3gene_2021": (144, 3),
    "immune_irg_3gene_2022": (332, 3),
    "prognostic_3gene_2021": (985, 3),
    "immune_ssgsea_13gene_2022": (57, 13),
    "metabolic_5gene_2021": (37, 5),
    "atf_creb_7gene_2025": (21, 7),
}


def observed_auc_map() -> dict[str, float]:
    summary = pd.read_csv(RESULTS / "ACC_transport_audit_v2_summary.csv")
    return (
        summary.set_index("signature")["apparent_internal_auc"]
        .astype(float)
        .to_dict()
    )


def null_apparent_distribution(
    pool_size: int,
    selected_k: int,
    seed: int,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    y_base = np.r_[np.ones(N_EVENTS), np.zeros(N_SAMPLE - N_EVENTS)]
    values = np.empty(N_SIMULATIONS, dtype=float)
    for simulation in range(N_SIMULATIONS):
        x = rng.normal(size=(N_SAMPLE, pool_size))
        y = y_base.copy()
        rng.shuffle(y)
        effects = x[y == 1].mean(axis=0) - x[y == 0].mean(axis=0)
        selected = np.argsort(np.abs(effects))[-selected_k:]
        score = x[:, selected] @ np.sign(effects[selected])
        values[simulation] = roc_auc_score(y, score)
    return values


def classify(observed: float, q50: float, q95: float, p_value: float) -> str:
    if observed < q50:
        return "observed_below_null_median"
    if observed <= q95:
        return "indistinguishable_from_topk_selection_noise"
    if p_value <= 0.05:
        return "observed_above_selection_noise"
    return "observed_above_q95_but_p_gt_0.05"


def main() -> None:
    observed = observed_auc_map()
    rows = []
    distributions = {}

    for index, (signature, (pool_size, k)) in enumerate(SIGNATURE_POOLS.items()):
        values = null_apparent_distribution(
            pool_size,
            k,
            seed=RANDOM_SEED + index,
        )
        distributions[signature] = values
        observed_value = observed[signature]
        percentile = float(np.mean(values <= observed_value) * 100)
        empirical_p = float(
            (1 + np.sum(values >= observed_value)) / (1 + len(values))
        )
        q50 = float(np.quantile(values, 0.50))
        q75 = float(np.quantile(values, 0.75))
        q90 = float(np.quantile(values, 0.90))
        q95 = float(np.quantile(values, 0.95))
        q99 = float(np.quantile(values, 0.99))
        rows.append(
            {
                "signature": signature,
                "candidate_pool": pool_size,
                "selected_k": k,
                "observed_apparent_auc": observed_value,
                "null_auc_q50": q50,
                "null_auc_q75": q75,
                "null_auc_q90": q90,
                "null_auc_q95": q95,
                "null_auc_q99": q99,
                "observed_percentile_under_null": percentile,
                "empirical_p_greater_or_equal": empirical_p,
                "observed_minus_null_median": observed_value - q50,
                "selection_noise_classification": classify(
                    observed_value,
                    q50,
                    q95,
                    empirical_p,
                ),
                "simulations": N_SIMULATIONS,
            }
        )

    result = pd.DataFrame(rows)
    result.to_csv(
        RESULTS / "RATA_v4_selection_optimism_percentile.csv",
        index=False,
    )
    payload = {
        "simulations": N_SIMULATIONS,
        "sample_size": N_SAMPLE,
        "events": N_EVENTS,
        "results": result.to_dict(orient="records"),
        "null_distribution_samples": {
            signature: values[:200].tolist()
            for signature, values in distributions.items()
        },
    }
    (RESULTS / "RATA_v4_selection_optimism_percentile.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    print(result.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
