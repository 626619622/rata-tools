"""Reusable primitives for Role-Aware Transportability Audit."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from typing import Iterable, Mapping, Sequence

import numpy as np
from scipy.stats import chi2
from sklearn.feature_selection import f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.preprocessing import StandardScaler
from statsmodels.duration.hazard_regression import PHReg


def _as_1d(values: Sequence[float], name: str) -> np.ndarray:
    array = np.asarray(values)
    if array.ndim != 1:
        raise ValueError(f"{name} must be one-dimensional")
    if array.size == 0:
        raise ValueError(f"{name} must not be empty")
    return array


def _validate_score_time_event(
    score: Sequence[float],
    time: Sequence[float],
    event: Sequence[int],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    score_array = _as_1d(score, "score").astype(float)
    time_array = _as_1d(time, "time").astype(float)
    event_array = _as_1d(event, "event").astype(int)
    if not (len(score_array) == len(time_array) == len(event_array)):
        raise ValueError("score, time and event must have equal length")
    if np.any(~np.isfinite(score_array)):
        raise ValueError("score contains non-finite values")
    if np.any(~np.isfinite(time_array)) or np.any(time_array < 0):
        raise ValueError("time must be finite and non-negative")
    if not np.isin(event_array, [0, 1]).all():
        raise ValueError("event must contain only 0 and 1")
    return score_array, time_array, event_array


def effective_cluster_number(counts: Sequence[int] | np.ndarray) -> float:
    """Return the inverse-Herfindahl effective number of represented clusters."""
    counts_array = np.asarray(counts, dtype=float)
    if counts_array.ndim != 1 or counts_array.size == 0:
        raise ValueError("counts must be a non-empty one-dimensional sequence")
    if np.any(counts_array < 0):
        raise ValueError("counts must be non-negative")
    total = counts_array.sum()
    if total <= 0:
        raise ValueError("counts must contain at least one positive value")
    probabilities = counts_array / total
    return float(1.0 / np.sum(probabilities**2))


def evidence_capacity(
    cluster_ids: Sequence[str],
    events_per_cluster: Mapping[str, int] | None = None,
    independent_clusters: Iterable[str] | None = None,
    platform_per_cluster: Mapping[str, str] | None = None,
) -> dict:
    """Summarize claim frequency, effective clusters, events and platforms.

    Cluster identifiers should use a reuse-aware family key, not a bare GEO
    accession. Repeated claims in the same cluster are counted as claims but
    contribute only once to cluster-level evidence capacity.
    """
    clusters = [str(value) for value in cluster_ids]
    if not clusters:
        raise ValueError("cluster_ids must not be empty")
    counts = Counter(clusters)
    unique_clusters = sorted(counts)
    independent = (
        set(str(value) for value in independent_clusters)
        if independent_clusters is not None
        else set(unique_clusters)
    )
    unknown_independent = independent - set(unique_clusters)
    if unknown_independent:
        raise ValueError(
            "independent_clusters contains unknown clusters: "
            + ", ".join(sorted(unknown_independent))
        )

    total_events = None
    independent_events = None
    if events_per_cluster is not None:
        missing = set(unique_clusters) - set(events_per_cluster)
        if missing:
            raise ValueError(
                "events_per_cluster is missing clusters: "
                + ", ".join(sorted(missing))
            )
        normalized_events = {
            value: int(events_per_cluster[value]) for value in unique_clusters
        }
        if any(value < 0 for value in normalized_events.values()):
            raise ValueError("event counts must be non-negative")
        total_events = int(sum(normalized_events.values()))
        independent_events = int(
            sum(normalized_events[value] for value in independent)
        )

    platforms = None
    if platform_per_cluster is not None:
        missing = set(unique_clusters) - set(platform_per_cluster)
        if missing:
            raise ValueError(
                "platform_per_cluster is missing clusters: "
                + ", ".join(sorted(missing))
            )
        platforms = sorted({str(platform_per_cluster[value]) for value in unique_clusters})

    return {
        "claims": len(clusters),
        "clusters": len(unique_clusters),
        "cluster_counts": dict(sorted(counts.items())),
        "effective_cluster_number": effective_cluster_number(
            [counts[value] for value in unique_clusters]
        ),
        "total_events": total_events,
        "independent_events": independent_events,
        "platforms": platforms,
        "platform_count": len(platforms) if platforms is not None else None,
    }


def harrell_c_index(
    score: Sequence[float],
    time: Sequence[float],
    event: Sequence[int],
) -> float:
    """Return Harrell's C-index, with ties in score contributing 0.5."""
    score_array, time_array, event_array = _validate_score_time_event(
        score, time, event
    )
    comparable_i = (time_array[:, None] < time_array[None, :]) & (
        event_array[:, None] == 1
    )
    comparable_j = (time_array[None, :] < time_array[:, None]) & (
        event_array[None, :] == 1
    )
    comparable = comparable_i | comparable_j
    concordant = (
        np.sum(comparable_i & (score_array[:, None] > score_array[None, :]))
        + np.sum(comparable_j & (score_array[None, :] > score_array[:, None]))
        + 0.5
        * np.sum(comparable & (score_array[:, None] == score_array[None, :]))
    )
    count = int(np.sum(comparable))
    return float(concordant / count) if count else float("nan")


def bootstrap_auc_ci(
    score: Sequence[float],
    label: Sequence[int],
    repeats: int = 2000,
    seed: int = 1,
) -> tuple[float, float]:
    """Return a percentile bootstrap CI for a binary AUC."""
    score_array = _as_1d(score, "score").astype(float)
    label_array = _as_1d(label, "label").astype(int)
    if len(score_array) != len(label_array):
        raise ValueError("score and label must have equal length")
    if np.unique(label_array).size != 2:
        raise ValueError("label must contain both outcome classes")
    if repeats < 1:
        raise ValueError("repeats must be positive")

    rng = np.random.default_rng(seed)
    values = []
    for _ in range(repeats):
        indices = rng.integers(0, len(label_array), len(label_array))
        if np.unique(label_array[indices]).size < 2:
            continue
        values.append(roc_auc_score(label_array[indices], score_array[indices]))
    if not values:
        raise ValueError("no valid bootstrap resamples were generated")
    return float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))


def cindex_difference_in_differences(
    signature_internal: Sequence[float],
    signature_external: Sequence[float],
    control_internal: Sequence[float],
    control_external: Sequence[float],
    time_internal: Sequence[float],
    event_internal: Sequence[int],
    time_external: Sequence[float],
    event_external: Sequence[int],
) -> float:
    """Estimate a control-normalized signature transport contrast."""
    signature_gap = harrell_c_index(
        signature_internal, time_internal, event_internal
    ) - harrell_c_index(signature_external, time_external, event_external)
    control_gap = harrell_c_index(
        control_internal, time_internal, event_internal
    ) - harrell_c_index(control_external, time_external, event_external)
    return float(signature_gap - control_gap)


def selection_cv_auc(
    expression: np.ndarray,
    label: Sequence[int],
    selected_k: int = 3,
    folds: int = 5,
    seed: int = 1,
) -> float:
    """Estimate selection-aware binary AUC with feature selection inside folds."""
    matrix = np.asarray(expression, dtype=float)
    labels = _as_1d(label, "label").astype(int)
    if matrix.ndim != 2:
        raise ValueError("expression must be a two-dimensional matrix")
    if matrix.shape[0] != len(labels):
        raise ValueError("expression rows must match label length")
    if not (1 <= selected_k <= matrix.shape[1]):
        raise ValueError("selected_k must be between 1 and the number of features")
    if folds < 2:
        raise ValueError("folds must be at least 2")
    if np.unique(labels).size != 2:
        raise ValueError("label must contain both outcome classes")
    if any(count < folds for count in np.bincount(labels)):
        raise ValueError("each outcome class must have at least `folds` samples")

    splitter = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    aucs = []
    for train_index, test_index in splitter.split(matrix, labels):
        x_train = matrix[train_index]
        x_test = matrix[test_index]
        y_train = labels[train_index]
        y_test = labels[test_index]
        f_values, _ = f_classif(x_train, y_train)
        f_values = np.nan_to_num(f_values, nan=-np.inf)
        selected = np.argsort(f_values)[-selected_k:]
        model = LogisticRegression(max_iter=2000)
        model.fit(x_train[:, selected], y_train)
        probabilities = model.predict_proba(x_test[:, selected])[:, 1]
        aucs.append(roc_auc_score(y_test, probabilities))
    return float(np.mean(aucs))


@dataclass(frozen=True)
class SelectionDecision:
    observed_percentile: float
    empirical_p: float
    decision: str


def selection_null_decision(
    observed: float,
    null_values: Sequence[float],
    lower_q: float = 0.50,
    upper_q: float = 0.95,
) -> SelectionDecision:
    """Compare an observed score with a matched selection null."""
    values = _as_1d(null_values, "null_values").astype(float)
    if np.any(~np.isfinite(values)):
        raise ValueError("null_values contains non-finite values")
    if not 0 <= lower_q <= upper_q <= 1:
        raise ValueError("quantiles must satisfy 0 <= lower_q <= upper_q <= 1")
    percentile = float(np.mean(values <= observed) * 100)
    empirical_p = float((1 + np.sum(values >= observed)) / (len(values) + 1))
    q_low = float(np.quantile(values, lower_q))
    q_high = float(np.quantile(values, upper_q))
    if observed < q_low:
        decision = "below_null_median"
    elif observed <= q_high:
        decision = "indistinguishable_from_selection_noise"
    else:
        decision = "above_selection_noise"
    return SelectionDecision(percentile, empirical_p, decision)


def binary_transport_gate(
    external_auc: float,
    direction_concordant: bool,
    auc_threshold: float = 0.60,
) -> str:
    """Classify a single binary external-validation result."""
    if not 0 <= external_auc <= 1:
        raise ValueError("external_auc must be in [0, 1]")
    if not 0 < auc_threshold < 1:
        raise ValueError("auc_threshold must be in (0, 1)")
    if not direction_concordant:
        return "direction_reversal"
    if external_auc < auc_threshold:
        return "fail_binary_transport"
    return "positive_control_binary_pass"


def multi_cohort_binary_gate(
    external_aucs: Mapping[str, float],
    auc_threshold: float = 0.60,
    rule: str = "min",
) -> dict:
    """Apply a prespecified minimum or all-cohort binary-AUC rule."""
    if not external_aucs:
        raise ValueError("external_aucs must not be empty")
    values = np.asarray(list(external_aucs.values()), dtype=float)
    if np.any((values < 0) | (values > 1)):
        raise ValueError("all AUC values must be in [0, 1]")
    if not 0 < auc_threshold < 1:
        raise ValueError("auc_threshold must be in (0, 1)")
    if rule == "min" or rule == "all":
        passed = bool(np.all(values >= auc_threshold))
    else:
        raise ValueError("rule must be 'min' or 'all'")
    return {
        "status": (
            "multi_cohort_binary_pass" if passed else "fail_binary_transport"
        ),
        "min_auc": float(values.min()),
        "mean_auc": float(values.mean()),
        "auc_threshold": auc_threshold,
        "direction_all_above_chance": bool(np.all(values > 0.5)),
        "cohort_aucs": dict(external_aucs),
    }


def _factorize(values: np.ndarray) -> np.ndarray:
    unique = {value: index for index, value in enumerate(np.unique(values))}
    return np.asarray([unique[value] for value in values], dtype=int)


def survival_transport_gate(
    score: Sequence[float],
    time: Sequence[float],
    event: Sequence[int],
    cohort: Sequence[str],
    min_events_per_cohort: int = 10,
    min_total_events: int = 20,
    unstable_ci_width: float = 2.0,
) -> dict:
    """Run a cohort-stratified survival transport gate with guardrails."""
    score_array, time_array, event_array = _validate_score_time_event(
        score, time, event
    )
    cohort_array = _as_1d(cohort, "cohort").astype(str)
    if len(cohort_array) != len(score_array):
        raise ValueError("cohort must match score length")
    cohorts = np.unique(cohort_array)
    event_counts = {
        str(value): int(np.sum(event_array[cohort_array == value]))
        for value in cohorts
    }
    if (
        len(cohorts) < 2
        or min(event_counts.values()) < min_events_per_cohort
        or int(event_array.sum()) < min_total_events
    ):
        return {
            "status": "provisional_or_untestable",
            "events_by_cohort": event_counts,
            "total_events": int(event_array.sum()),
        }

    standardized = np.empty_like(score_array, dtype=float)
    per_cohort = []
    for value in cohorts:
        mask = cohort_array == value
        standardized[mask] = StandardScaler().fit_transform(
            score_array[mask].reshape(-1, 1)
        ).ravel()
        cohort_model = PHReg(
            time_array[mask],
            standardized[mask].reshape(-1, 1),
            status=event_array[mask],
            ties="efron",
        )
        cohort_result = cohort_model.fit(disp=False)
        cohort_beta = float(cohort_result.params[0])
        cohort_se = float(cohort_result.bse[0])
        cohort_ci_low = float(np.exp(cohort_beta - 1.96 * cohort_se))
        cohort_ci_high = float(np.exp(cohort_beta + 1.96 * cohort_se))
        unstable = bool(
            event_counts[str(value)] <= 10
            or (cohort_ci_high - cohort_ci_low) > unstable_ci_width
        )
        per_cohort.append(
            {
                "cohort": str(value),
                "beta": cohort_beta,
                "se": cohort_se,
                "hr": float(np.exp(cohort_beta)),
                "ci_low": cohort_ci_low,
                "ci_high": cohort_ci_high,
                "p_value": float(cohort_result.pvalues[0]),
                "events": event_counts[str(value)],
                "unstable": unstable,
            }
        )

    model = PHReg(
        time_array,
        standardized.reshape(-1, 1),
        status=event_array,
        strata=_factorize(cohort_array),
        ties="efron",
    )
    result = model.fit(disp=False)
    beta = float(result.params[0])
    se = float(result.bse[0])
    betas = np.asarray([item["beta"] for item in per_cohort], dtype=float)
    ses = np.asarray([item["se"] for item in per_cohort], dtype=float)
    direction_concordant = bool(np.all(betas > 0) or np.all(betas < 0))
    per_cohort_unstable = any(item["unstable"] for item in per_cohort)
    weights = 1 / np.maximum(ses**2, 1e-12)
    meta_beta = float(np.sum(weights * betas) / np.sum(weights))
    q = float(np.sum(weights * (betas - meta_beta) ** 2))
    q_df = len(betas) - 1
    i2 = float(max(0.0, (q - q_df) / max(q, 1e-12)) * 100)

    if not direction_concordant and per_cohort_unstable:
        status = "direction_reversal_unstable"
    elif not direction_concordant:
        status = "direction_reversal"
    elif per_cohort_unstable:
        status = "per_cohort_unstable"
    elif beta > 0 and np.exp(beta - 1.96 * se) > 1:
        status = "full_survival_transport_pass"
    else:
        status = "survival_transport_indeterminate"

    return {
        "status": status,
        "common_hr": float(np.exp(beta)),
        "ci_low": float(np.exp(beta - 1.96 * se)),
        "ci_high": float(np.exp(beta + 1.96 * se)),
        "p_value": float(result.pvalues[0]),
        "events_by_cohort": event_counts,
        "total_events": int(event_array.sum()),
        "per_cohort": per_cohort,
        "direction_concordant": direction_concordant,
        "per_cohort_unstable": per_cohort_unstable,
        "q": q,
        "q_df": q_df,
        "q_p_value": float(chi2.sf(q, q_df)),
        "i2": i2,
    }


@dataclass(frozen=True)
class GateDecision:
    gate1: str
    gate2: str
    gate3: str
    overall: str

    def to_dict(self) -> dict:
        return asdict(self)


def three_gate_decision(gate1: str, gate2: str, gate3: str) -> GateDecision:
    """Combine gate-specific labels without collapsing provisional evidence."""
    if gate1 != "above_selection_noise":
        overall = (
            "selection_uninformative"
            if gate1 == "uninformative_saturated"
            else "selection_sensitive"
        )
    elif gate2 == "provisional_single_cohort":
        overall = "provisional_transport"
    elif gate2 in {
        "survival_transport_indeterminate",
        "per_cohort_unstable",
        "direction_reversal_unstable",
    }:
        overall = "transport_indeterminate"
    elif gate2 not in {
        "full_survival_transport_pass",
        "positive_control_binary_pass",
        "multi_cohort_binary_pass",
    }:
        overall = "transport_fail"
    elif gate3 not in {"role_aware_pass", "role_integrity_pass"}:
        overall = "role_dependent"
    else:
        overall = "three_gate_pass"
    return GateDecision(gate1=gate1, gate2=gate2, gate3=gate3, overall=overall)

