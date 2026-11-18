"""Real hard-phenotype transport test: pituitary invasion."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from scipy.stats import ttest_ind
from statsmodels.stats.multitest import multipletests


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SCORES = RESULTS / "RATA_v5_pituitary_invasion_scores.csv"
MATRIX = RESULTS / "RATA_v5_pituitary_invasion_discovery_expression.csv.gz"
RANDOM_SEED = 20261110
N_SIMULATIONS = 500
N_CV_NULL_SIMULATIONS = 1000


def bootstrap_auc(
    score: np.ndarray,
    label: np.ndarray,
    seed: int,
    repeats: int = 2000,
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(repeats):
        indices = rng.integers(0, len(label), len(label))
        if np.unique(label[indices]).size < 2:
            continue
        values.append(roc_auc_score(label[indices], score[indices]))
    return float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))


def null_auc_distribution(
    n: int,
    n_positive: int,
    n_candidates: int,
    n_up: int,
    n_down: int,
    seed: int,
    mixture: bool,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    y = np.r_[np.ones(n_positive), np.zeros(n - n_positive)]
    values = np.empty(N_SIMULATIONS, dtype=float)
    signal_count = max(1, int(n_candidates * 0.05))
    for simulation in range(N_SIMULATIONS):
        x = rng.normal(size=(n, n_candidates))
        shuffled = y.copy()
        rng.shuffle(shuffled)
        if mixture:
            genes = rng.choice(n_candidates, signal_count, replace=False)
            x[np.ix_(shuffled == 1, genes)] += 0.20
        stats = x[shuffled == 1].mean(axis=0) - x[shuffled == 0].mean(axis=0)
        up = np.argsort(stats)[-n_up:]
        down = np.argsort(stats)[:n_down]
        score = x[:, up].mean(axis=1) - x[:, down].mean(axis=1)
        values[simulation] = roc_auc_score(shuffled, score)
    return values


def select_invasion_score(
    x: np.ndarray,
    y: np.ndarray,
    n_up: int = 11,
    n_down: int = 15,
) -> tuple[np.ndarray, np.ndarray]:
    statistics, p_values = ttest_ind(
        x[y == 1],
        x[y == 0],
        axis=0,
        equal_var=False,
    )
    fdr = multipletests(p_values, method="fdr_bh")[1]
    eligible = np.flatnonzero(fdr < 0.05)
    if len(eligible) >= n_up + n_down:
        candidate_up = eligible[statistics[eligible] > 0]
        candidate_down = eligible[statistics[eligible] < 0]
        if len(candidate_up) >= n_up and len(candidate_down) >= n_down:
            up = candidate_up[np.argsort(statistics[candidate_up])[-n_up:]]
            down = candidate_down[np.argsort(statistics[candidate_down])[:n_down]]
            return np.r_[up, down], np.r_[
                np.ones(n_up),
                -np.ones(n_down),
            ]
    up = np.argsort(statistics)[-n_up:]
    down = np.argsort(statistics)[:n_down]
    return np.r_[up, down], np.r_[
        np.ones(n_up),
        -np.ones(n_down),
    ]


def selection_cv_auc(
    x: np.ndarray,
    y: np.ndarray,
    seed: int,
) -> float:
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    aucs = []
    for train_indices, test_indices in folds.split(x, y):
        mean = x[train_indices].mean(axis=0)
        sd = np.maximum(x[train_indices].std(axis=0), 1e-6)
        train_x = (x[train_indices] - mean) / sd
        test_x = (x[test_indices] - mean) / sd
        selected, signs = select_invasion_score(
            train_x,
            y[train_indices],
        )
        score = test_x[:, selected] @ signs
        aucs.append(roc_auc_score(y[test_indices], score))
    return float(np.mean(aucs))


def selection_cv_null(
    n: int,
    n_positive: int,
    n_candidates: int,
    seed: int,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    y = np.r_[np.ones(n_positive), np.zeros(n - n_positive)]
    values = np.empty(N_CV_NULL_SIMULATIONS, dtype=float)
    for simulation in range(N_CV_NULL_SIMULATIONS):
        x = rng.normal(size=(n, n_candidates))
        shuffled = y.copy()
        rng.shuffle(shuffled)
        values[simulation] = selection_cv_auc(
            x,
            shuffled,
            seed=seed + simulation + 1,
        )
    return values


def main() -> None:
    scores = pd.read_csv(SCORES)
    discovery = scores[scores["cohort"].eq("GSE169498")]
    expression = pd.read_csv(MATRIX).set_index("gene")
    labels = pd.read_csv(
        RESULTS / "RATA_v5_pituitary_invasion_discovery_labels.csv"
    ).set_index("sample")
    samples = labels.index
    x_discovery = expression[samples].to_numpy(dtype=float).T
    y_discovery = labels.loc[samples, "invasion_binary"].to_numpy(dtype=int)
    n_candidates = expression.shape[0]

    cohort_rows = []
    for index, (cohort, frame) in enumerate(scores.groupby("cohort")):
        auc = roc_auc_score(frame["invasion_binary"], frame["score"])
        low, high = bootstrap_auc(
            frame["score"].to_numpy(),
            frame["invasion_binary"].to_numpy(),
            seed=RANDOM_SEED + index,
        )
        cohort_rows.append(
            {
                "cohort": cohort,
                "n": len(frame),
                "invasive_n": int(frame["invasion_binary"].sum()),
                "non_invasive_n": int((1 - frame["invasion_binary"]).sum()),
                "auc": auc,
                "auc_ci_low": low,
                "auc_ci_high": high,
            }
        )
    cohort_table = pd.DataFrame(cohort_rows).set_index("cohort")

    pure = null_auc_distribution(
        len(discovery),
        int(discovery["invasion_binary"].sum()),
        n_candidates,
        n_up=15,
        n_down=11,
        seed=RANDOM_SEED + 10,
        mixture=False,
    )
    realistic = null_auc_distribution(
        len(discovery),
        int(discovery["invasion_binary"].sum()),
        n_candidates,
        n_up=15,
        n_down=11,
        seed=RANDOM_SEED + 11,
        mixture=True,
    )
    development_auc = float(cohort_table.loc["GSE169498", "auc"])
    selection_cv = selection_cv_auc(
        x_discovery,
        y_discovery,
        seed=RANDOM_SEED + 20,
    )
    cv_null = selection_cv_null(
        len(y_discovery),
        int(y_discovery.sum()),
        n_candidates,
        seed=RANDOM_SEED + 21,
    )
    cv_null_q95 = float(np.quantile(cv_null, 0.95))
    rng = np.random.default_rng(RANDOM_SEED + 22)
    q95_bootstrap = [
        np.quantile(
            rng.choice(cv_null, len(cv_null), replace=True),
            0.95,
        )
        for _ in range(1000)
    ]
    gate1 = selection_cv > cv_null_q95

    external = cohort_table.loc[["GSE136781", "GSE260487"]]
    direction_concordant = (
        np.sign(external["auc"] - 0.5)
        == np.sign(development_auc - 0.5)
    )
    mean_external_auc = float(external["auc"].mean())
    gate2 = bool(
        direction_concordant.all()
        and mean_external_auc > 0.60
        and external["auc"].min() > 0.55
    )
    gate2_status = (
        "pass_two_cohort_binary_transport"
        if gate2
        else "fail_binary_transport"
    )

    cohort_table.reset_index().to_csv(
        RESULTS / "RATA_v5_pituitary_invasion_cohort_auc.csv",
        index=False,
    )
    payload = {
        "phenotype": "pituitary invasion",
        "endpoint_type": "binary hard phenotype",
        "development": "GSE169498",
        "external": ["GSE136781", "GSE260487"],
        "candidate_pool": n_candidates,
        "selected_up": 11,
        "selected_down": 15,
        "development_auc": development_auc,
        "selection_cv_auc": selection_cv,
        "selection_cv_null_q95": cv_null_q95,
        "selection_cv_null_q95_ci_low": float(
            np.quantile(q95_bootstrap, 0.025)
        ),
        "selection_cv_null_q95_ci_high": float(
            np.quantile(q95_bootstrap, 0.975)
        ),
        "selection_cv_null_simulations": N_CV_NULL_SIMULATIONS,
        "pure_null_q95": float(np.quantile(pure, 0.95)),
        "realistic_null_q95": float(np.quantile(realistic, 0.95)),
        "gate1_selection": bool(gate1),
        "external_mean_auc": mean_external_auc,
        "external_min_auc": float(external["auc"].min()),
        "direction_concordant": bool(direction_concordant.all()),
        "gate2_binary_transport": gate2,
        "gate2_status": gate2_status,
        "gate3": "not_evaluated_before_gate2",
        "cohort_results": cohort_table.reset_index().to_dict(orient="records"),
        "notes": (
            "GSE260487 has strong lineage-invasion confounding in the prior "
            "pituitary audit; failure is interpreted as transport/confounding, "
            "not necessarily absence of biological signal."
        ),
    }
    (RESULTS / "RATA_v5_pituitary_invasion_transport.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    print(cohort_table.round(4).to_string())
    print("\nGate1:", gate1, "Gate2:", gate2, "mean external AUC:", mean_external_auc)


if __name__ == "__main__":
    main()
