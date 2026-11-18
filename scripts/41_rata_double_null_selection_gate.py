"""Pure-null and realistic-mixture-null calibration for selection gate."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RANDOM_SEED = 20261110
N_SAMPLE = 79
N_EVENTS = 28
N_SIMULATIONS = 500
MIXTURE_SIGNAL_FRACTION = 0.05
MIXTURE_EFFECT_SIZE = 0.20

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


def null_distribution(
    pool_size: int,
    selected_k: int,
    seed: int,
    mixture: bool,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    y_base = np.r_[np.ones(N_EVENTS), np.zeros(N_SAMPLE - N_EVENTS)]
    signal_count = max(1, int(round(pool_size * MIXTURE_SIGNAL_FRACTION)))
    values = np.empty(N_SIMULATIONS, dtype=float)
    for simulation in range(N_SIMULATIONS):
        x = rng.normal(size=(N_SAMPLE, pool_size))
        y = y_base.copy()
        rng.shuffle(y)
        if mixture:
            signal_genes = rng.choice(pool_size, signal_count, replace=False)
            positive_indices = np.flatnonzero(y == 1)
            x[np.ix_(positive_indices, signal_genes)] += MIXTURE_EFFECT_SIZE
        effects = x[y == 1].mean(axis=0) - x[y == 0].mean(axis=0)
        selected = np.argsort(np.abs(effects))[-selected_k:]
        score = x[:, selected] @ np.sign(effects[selected])
        values[simulation] = roc_auc_score(y, score)
    return values


def empirical_greater(values: np.ndarray, observed: float) -> float:
    return float((1 + np.sum(values >= observed)) / (1 + len(values)))


def main() -> None:
    observed = observed_auc_map()
    rows = []
    for index, (signature, (pool_size, k)) in enumerate(SIGNATURE_POOLS.items()):
        pure = null_distribution(
            pool_size,
            k,
            seed=RANDOM_SEED + index * 2,
            mixture=False,
        )
        realistic = null_distribution(
            pool_size,
            k,
            seed=RANDOM_SEED + index * 2 + 1,
            mixture=True,
        )
        observed_auc = observed[signature]
        pure_q95 = float(np.quantile(pure, 0.95))
        realistic_q95 = float(np.quantile(realistic, 0.95))
        rows.append(
            {
                "signature": signature,
                "candidate_pool": pool_size,
                "selected_k": k,
                "observed_apparent_auc": observed_auc,
                "pure_null_q95": pure_q95,
                "pure_null_percentile": float(np.mean(pure <= observed_auc) * 100),
                "pure_null_p": empirical_greater(pure, observed_auc),
                "realistic_null_q95": realistic_q95,
                "realistic_null_percentile": float(
                    np.mean(realistic <= observed_auc) * 100
                ),
                "realistic_null_p": empirical_greater(realistic, observed_auc),
                "pass_pure_null_gate": observed_auc > pure_q95,
                "pass_realistic_null_gate": observed_auc > realistic_q95,
                "selection_gate_decision": (
                    "pass"
                    if observed_auc > realistic_q95
                    else "fail"
                ),
                "mixture_signal_fraction": MIXTURE_SIGNAL_FRACTION,
                "mixture_effect_size": MIXTURE_EFFECT_SIZE,
                "simulations_per_null": N_SIMULATIONS,
            }
        )

    result = pd.DataFrame(rows)
    result.to_csv(
        RESULTS / "RATA_v5_double_null_selection_gate.csv",
        index=False,
    )
    payload = {
        "pure_null_definition": "No gene-associated phenotype signal.",
        "realistic_null_definition": (
            "Five percent of candidate genes carry a weak standardized "
            "case-control effect of 0.20; this approximates residual weak "
            "associations and correlated nuisance."
        ),
        "decision_threshold": "95th percentile of realistic mixture null",
        "results": result.to_dict(orient="records"),
    }
    (RESULTS / "RATA_v5_double_null_selection_gate.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    print(result.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
