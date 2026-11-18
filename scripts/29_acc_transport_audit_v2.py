"""Role-aware ACC transport audit v2.

This analysis addresses five methodological critiques of the first pilot:
  1. separate apparent, fixed-score bootstrap, and same-gene CV performance;
  2. normalize the signature gap by a predefined positive-control gap;
  3. classify transportability and novelty on separate axes;
  4. benchmark axis R2 against size- and weight-matched random gene sets;
  5. preserve explicit provenance grades and underpowered status.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
BASE_SCRIPT = ROOT / "scripts" / "28_acc_signature_transport_pilot.py"

spec = importlib.util.spec_from_file_location("acc_pilot_v1", BASE_SCRIPT)
if spec is None or spec.loader is None:
    raise RuntimeError("Could not load ACC pilot helpers")
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

RANDOM_SEED = 20261109
N_NULL_SETS = 5000
N_BOOTSTRAP = 1500

SIGNATURES = {
    "hypoxia_3gene_2021": {
        "source_pmid": "34603443",
        "genes": ["CCNA2", "EFNA3", "COL5A1"],
        "weights": [0.81, 0.46, 0.38],
        "development": "TCGA",
        "reported_validation": "GSE19750",
        "gse33371_independent": True,
        "provenance_grade": "A",
        "provenance_reason": (
            "Independent project and platform from development; one external cohort."
        ),
    },
    "immune_irg_3gene_2022": {
        "source_pmid": "36039643",
        "genes": ["INHBA", "HELLS", "HDAC4"],
        "weights": [1.647, 2.583, 2.61],
        "development": "TCGA training subset",
        "reported_validation": "TCGA testing;GSE10927;GSE19750",
        "gse33371_independent": False,
        "provenance_grade": "C",
        "provenance_reason": (
            "GSE33371 consists of the same expression arrays as GSE10927, "
            "which was used as validation."
        ),
    },
    "prognostic_3gene_2021": {
        "source_pmid": "34858497",
        "genes": ["TIGD1", "SGK1", "MKI67"],
        "weights": [0.036112, -0.10388, 0.065722],
        "development": "GSE10927;GSE19750",
        "reported_validation": "GSE49278;TCGA",
        "gse33371_independent": False,
        "provenance_grade": "C",
        "provenance_reason": (
            "GSE33371 overlaps the GSE10927 discovery arrays."
        ),
    },
    "immune_ssgsea_13gene_2022": {
        "source_pmid": "35210821",
        "genes": [
            "RAC2",
            "KRAS",
            "IL11RA",
            "C3",
            "GHR",
            "VGF",
            "TOR2A",
            "PTGFR",
            "TGFBR2",
            "TNFAIP3",
            "PAK4",
            "IRF7",
            "SDC4",
        ],
        "weights": [
            -0.0722415,
            0.6064765,
            0.6911548,
            -0.0375132,
            -0.1608705,
            0.0646402,
            0.4313901,
            -0.0413595,
            -0.0223629,
            0.3557257,
            0.1153306,
            0.5941446,
            -0.0655002,
        ],
        "development": "TCGA",
        "reported_validation": "GSE76201",
        "gse33371_independent": True,
        "provenance_grade": "A",
        "provenance_reason": (
            "GSE33371 differs from both TCGA development and GSE76201 validation."
        ),
    },
    "metabolic_5gene_2021": {
        "source_pmid": "34918636",
        "genes": ["RPL31", "IRF9", "UBE2C", "GSTM2", "CYP11B1"],
        "weights": [0.904238627, 0.671920087, 0.717969594, -0.561156263, -0.141209604],
        "development": "TCGA",
        "reported_validation": "GSE76021;GSE19750",
        "gse33371_independent": True,
        "provenance_grade": "A",
        "provenance_reason": (
            "GSE33371 is not the development or claimed validation data."
        ),
    },
    "atf_creb_7gene_2025": {
        "source_pmid": "40696947",
        "genes": ["ATF3", "ATF4", "BATF", "CREB3", "CREM", "CREB3L3", "CREBZF"],
        "weights": [0.1322, 0.6195, 0.1538, 0.0075, 0.0771, -0.6828, 0.2369],
        "development": "TCGA",
        "reported_validation": "GSE10927;WCH IHC",
        "gse33371_independent": False,
        "provenance_grade": "C",
        "provenance_reason": (
            "GSE33371 uses the same expression arrays as GSE10927 validation."
        ),
    },
}


def fast_cross_fitted_r2(
    target: np.ndarray,
    axes: np.ndarray,
    folds: int = 5,
    seed: int = RANDOM_SEED,
) -> float:
    rng = np.random.default_rng(seed)
    indices = np.arange(len(target))
    rng.shuffle(indices)
    predictions = np.zeros_like(target, dtype=float)
    for fold_indices in np.array_split(indices, folds):
        train_indices = np.setdiff1d(indices, fold_indices)
        design = np.column_stack(
            [np.ones(len(train_indices)), axes[train_indices]]
        )
        coefficients, *_ = np.linalg.lstsq(
            design,
            target[train_indices],
            rcond=None,
        )
        validation_design = np.column_stack(
            [np.ones(len(fold_indices)), axes[fold_indices]]
        )
        predictions[fold_indices] = validation_design @ coefficients
    residual = np.sum((target - predictions) ** 2)
    total = np.sum((target - target.mean()) ** 2)
    return float(1 - residual / max(total, 1e-12))


def axis_null_benchmark(
    expression: pd.DataFrame,
    axes: pd.DataFrame,
    k: int,
    observed_weights: list[float],
    observed_r2: float,
    seed: int,
) -> dict:
    common_genes = expression.index.intersection(axes.index.union(expression.index))
    candidate_genes = np.asarray(list(common_genes), dtype=object)
    available = []
    for gene in candidate_genes:
        if gene in expression.index:
            values = expression.loc[gene].to_numpy(dtype=float)
            if np.isfinite(values).all() and np.std(values) > 0:
                available.append(gene)
    available = np.asarray(available, dtype=object)
    axis_values = axes.to_numpy(dtype=float)

    # Use an observed-size matched design. Weight signs and magnitudes are
    # permuted so the null preserves the published score's scale profile.
    weights = np.asarray(observed_weights, dtype=float)
    null_values = []
    rng = np.random.default_rng(seed)
    for repeat in range(N_NULL_SETS):
        genes = rng.choice(available, size=k, replace=False)
        shuffled_weights = rng.permutation(weights)
        score = expression.loc[genes].to_numpy(dtype=float).T @ shuffled_weights
        null_values.append(
            fast_cross_fitted_r2(
                score,
                axis_values,
                seed=seed + repeat,
            )
        )
    null_values = np.asarray(null_values)
    empirical_p = (1 + np.sum(null_values >= observed_r2)) / (1 + len(null_values))
    return {
        "null_mean": float(null_values.mean()),
        "null_sd": float(null_values.std()),
        "null_q95": float(np.quantile(null_values, 0.95)),
        "null_q99": float(np.quantile(null_values, 0.99)),
        "empirical_p": float(empirical_p),
        "null_values_sample": null_values[:500].tolist(),
    }


def bootstrap_axis_r2(
    score: np.ndarray,
    axes: np.ndarray,
    seed: int,
) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    values = []
    for repeat in range(500):
        indices = rng.integers(0, len(score), len(score))
        values.append(
            fast_cross_fitted_r2(
                score[indices],
                axes[indices],
                seed=seed + repeat,
            )
        )
    return float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))


def fixed_score_bootstrap(
    score: pd.Series,
    event: pd.Series,
    seed: int,
) -> tuple[float, float, float]:
    rng = np.random.default_rng(seed)
    values = []
    score_values = score.to_numpy(dtype=float)
    event_values = event.to_numpy(dtype=int)
    for repeat in range(N_BOOTSTRAP):
        indices = rng.integers(0, len(score_values), len(score_values))
        if np.unique(event_values[indices]).size < 2:
            continue
        values.append(
            roc_auc_score(
                event_values[indices],
                score_values[indices],
            )
        )
    apparent = float(roc_auc_score(event_values, score_values))
    return (
        apparent - float(np.mean(values)),
        float(np.quantile(values, 0.025)),
        float(np.quantile(values, 0.975)),
    )


def same_gene_cv_auc(
    expression: pd.DataFrame,
    genes: list[str],
    events: pd.Series,
    seed: int,
) -> float:
    x = StandardScaler().fit_transform(expression.loc[genes].T)
    model = LogisticRegression(C=0.5, max_iter=3000)
    folds = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    predictions = cross_val_predict(
        model,
        x,
        events,
        cv=folds,
        method="decision_function",
    )
    return float(roc_auc_score(events, predictions))


def control_ratio_bootstrap(
    score_internal: pd.Series,
    score_external: pd.Series,
    control_internal: pd.Series,
    control_external: pd.Series,
    events_internal: pd.Series,
    events_external: pd.Series,
    seed: int,
) -> tuple[float, float, float, float]:
    sig_in = float(roc_auc_score(events_internal, score_internal))
    sig_out = float(roc_auc_score(events_external, score_external))
    ctrl_in = float(roc_auc_score(events_internal, control_internal))
    ctrl_out = float(roc_auc_score(events_external, control_external))
    denominator = ctrl_in - ctrl_out
    if denominator <= 0.01:
        return float("nan"), float("nan"), float("nan"), 0.0
    ratio = (sig_in - sig_out) / denominator

    rng = np.random.default_rng(seed)
    ratios = []
    for repeat in range(N_BOOTSTRAP):
        in_idx = rng.integers(0, len(score_internal), len(score_internal))
        out_idx = rng.integers(0, len(score_external), len(score_external))
        in_events = events_internal.to_numpy()[in_idx]
        out_events = events_external.to_numpy()[out_idx]
        if np.unique(in_events).size < 2 or np.unique(out_events).size < 2:
            continue
        ctrl_gap = (
            roc_auc_score(in_events, control_internal.to_numpy()[in_idx])
            - roc_auc_score(out_events, control_external.to_numpy()[out_idx])
        )
        if ctrl_gap <= 0.01:
            continue
        sig_gap = (
            roc_auc_score(in_events, score_internal.to_numpy()[in_idx])
            - roc_auc_score(out_events, score_external.to_numpy()[out_idx])
        )
        ratios.append(sig_gap / ctrl_gap)
    if len(ratios) < 100:
        return ratio, float("nan"), float("nan"), len(ratios) / N_BOOTSTRAP
    return (
        ratio,
        float(np.quantile(ratios, 0.025)),
        float(np.quantile(ratios, 0.975)),
        len(ratios) / N_BOOTSTRAP,
    )


def transportability_status(
    row: dict,
) -> tuple[str, str]:
    if not row["gse33371_independent"]:
        return "not_independently_testable", "provenance_C"
    if not row["direction_concordant"]:
        return "direction_reversal", "directional_evidence"
    if not np.isfinite(row["control_normalized_gap_ratio"]):
        return "indeterminate", "positive_control_gap_nonpositive"
    if row["external_events"] < 20 or row["external_n"] < 50:
        return "indeterminate", "underpowered"
    low = row["control_normalized_gap_ratio_ci_low"]
    high = row["control_normalized_gap_ratio_ci_high"]
    if np.isfinite(low) and low > 1.0:
        return "relative_nontransport", "adequate"
    if np.isfinite(high) and high < 1.0:
        return "relative_transport_supported", "adequate"
    return "indeterminate", "ratio_ci_crosses_one"


def main() -> None:
    tcga_expression, tcga_outcomes = base.load_tcga()
    geo_expression, geo_samples = base.load_gse33371()

    tcga_axes = tcga_outcomes[
        [
            "adrenal_cortex",
            "proliferation",
            "immune",
            "fibroblast_ecm",
            "hypoxia_glycolysis",
        ]
    ]
    geo_axes = base.program_scores(geo_expression)

    control_definition = {
        "genes": base.PROGRAMS["proliferation"],
        "weights": [1.0] * len(base.PROGRAMS["proliferation"]),
    }
    control_internal, _ = base.score_signature(
        tcga_expression,
        control_definition["genes"],
        control_definition["weights"],
    )
    control_external, _ = base.score_signature(
        geo_expression,
        control_definition["genes"],
        control_definition["weights"],
    )

    summary_rows = []
    null_rows = []
    provenance_rows = []

    for index, (signature, definition) in enumerate(SIGNATURES.items()):
        internal_score, _ = base.score_signature(
            tcga_expression,
            definition["genes"],
            definition["weights"],
        )
        external_score, _ = base.score_signature(
            geo_expression,
            definition["genes"],
            definition["weights"],
        )

        internal_auc = base.auc_with_direction(
            internal_score,
            tcga_outcomes["os_event"],
        )
        external_auc = base.auc_with_direction(
            external_score,
            geo_samples["os_event"],
        )
        external_auc_low, external_auc_high = base.bootstrap_auc(
            external_score,
            geo_samples["os_event"],
            seed=RANDOM_SEED + 500 + index,
        )
        fixed_optimism, fixed_low, fixed_high = fixed_score_bootstrap(
            internal_score,
            tcga_outcomes["os_event"],
            seed=RANDOM_SEED + index,
        )
        same_gene_cv = same_gene_cv_auc(
            tcga_expression,
            definition["genes"],
            tcga_outcomes["os_event"],
            seed=RANDOM_SEED + index,
        )
        ratio, ratio_low, ratio_high, ratio_valid = control_ratio_bootstrap(
            internal_score,
            external_score,
            control_internal,
            control_external,
            tcga_outcomes["os_event"],
            geo_samples["os_event"],
            seed=RANDOM_SEED + index,
        )

        external_axis_values = geo_axes.to_numpy(dtype=float)
        observed_axis_r2 = fast_cross_fitted_r2(
            external_score.to_numpy(dtype=float),
            external_axis_values,
            seed=RANDOM_SEED + index,
        )
        r2_low, r2_high = bootstrap_axis_r2(
            external_score.to_numpy(dtype=float),
            external_axis_values,
            seed=RANDOM_SEED + 1000 + index,
        )
        null = axis_null_benchmark(
            geo_expression,
            geo_axes,
            k=len(definition["genes"]),
            observed_weights=definition["weights"],
            observed_r2=observed_axis_r2,
            seed=RANDOM_SEED + 2000 + index,
        )
        if null["empirical_p"] <= 0.05:
            novelty_status = "known_axis_proxy_supported"
        elif null["empirical_p"] <= 0.20:
            novelty_status = "possible_known_axis_proxy"
        else:
            novelty_status = "axis_independence_not_rejected"
        axis_r2_stability = (
            "stable"
            if r2_low > null["null_q95"]
            else "unstable_small_cohort"
        )
        row = {
            "signature": signature,
            "source_pmid": definition["source_pmid"],
            "n_genes": len(definition["genes"]),
            "development": definition["development"],
            "reported_validation": definition["reported_validation"],
            "gse33371_independent": definition["gse33371_independent"],
            "provenance_grade": definition["provenance_grade"],
            "provenance_reason": definition["provenance_reason"],
            "internal_n": len(internal_score),
            "internal_events": int(tcga_outcomes["os_event"].sum()),
            "external_n": len(external_score),
            "external_events": int(geo_samples["os_event"].sum()),
            "apparent_internal_auc": internal_auc,
            "fixed_score_bootstrap_optimism": fixed_optimism,
            "fixed_score_bootstrap_ci_low": fixed_low,
            "fixed_score_bootstrap_ci_high": fixed_high,
            "same_gene_cv_auc_sensitivity": same_gene_cv,
            "selection_path_optimism": "not_recoverable_from_fixed_formula",
            "external_auc": external_auc,
            "external_auc_ci_low": external_auc_low,
            "external_auc_ci_high": external_auc_high,
            "external_direction_concordant": (
                np.sign(internal_auc - 0.5) == np.sign(external_auc - 0.5)
            ),
            "absolute_internal_external_gap": internal_auc - external_auc,
            "positive_control_internal_auc": float(
                roc_auc_score(tcga_outcomes["os_event"], control_internal)
            ),
            "positive_control_external_auc": float(
                roc_auc_score(geo_samples["os_event"], control_external)
            ),
            "control_normalized_gap_ratio": ratio,
            "control_normalized_gap_ratio_ci_low": ratio_low,
            "control_normalized_gap_ratio_ci_high": ratio_high,
            "control_ratio_bootstrap_valid_fraction": ratio_valid,
            "axis_r2_observed": observed_axis_r2,
            "axis_r2_ci_low": r2_low,
            "axis_r2_ci_high": r2_high,
            "axis_r2_null_mean": null["null_mean"],
            "axis_r2_null_q95": null["null_q95"],
            "axis_r2_null_q99": null["null_q99"],
            "axis_r2_empirical_p": null["empirical_p"],
            "novelty_axis_status": novelty_status,
            "axis_r2_stability": axis_r2_stability,
        }
        row["direction_concordant"] = row["external_direction_concordant"]
        status, evidence = transportability_status(row)
        row["transportability_status"] = status
        row["statistical_evidence_status"] = evidence

        summary_rows.append(row)
        null_rows.append(
            {
                "signature": signature,
                "observed_axis_r2": observed_axis_r2,
                "null_mean": null["null_mean"],
                "null_sd": null["null_sd"],
                "null_q95": null["null_q95"],
                "null_q99": null["null_q99"],
                "empirical_p": null["empirical_p"],
                "null_sample_json": json.dumps(null["null_values_sample"]),
            }
        )
        provenance_rows.append(
            {
                "signature": signature,
                "source_pmid": definition["source_pmid"],
                "development": definition["development"],
                "reported_validation": definition["reported_validation"],
                "GSE33371_independent": definition["gse33371_independent"],
                "provenance_grade": definition["provenance_grade"],
                "provenance_reason": definition["provenance_reason"],
            }
        )

    summary = pd.DataFrame(summary_rows)
    null_summary = pd.DataFrame(null_rows)
    provenance = pd.DataFrame(provenance_rows)

    summary.to_csv(
        RESULTS / "ACC_transport_audit_v2_summary.csv",
        index=False,
    )
    null_summary.to_csv(
        RESULTS / "ACC_transport_audit_v2_axis_null.csv",
        index=False,
    )
    provenance.to_csv(
        RESULTS / "ACC_transport_audit_v2_provenance.csv",
        index=False,
    )

    auditable = summary[summary["gse33371_independent"]]
    provenance_payload = {
        "registry_signatures": len(SIGNATURES),
        "gse33371_independently_testable": int(
            summary["gse33371_independent"].sum()
        ),
        "gse33371_nonindependent": int(
            (~summary["gse33371_independent"]).sum()
        ),
        "grade_counts": summary["provenance_grade"]
        .value_counts()
        .to_dict(),
        "transportability_counts": auditable["transportability_status"]
        .value_counts()
        .to_dict(),
        "novelty_counts": auditable["novelty_axis_status"]
        .value_counts()
        .to_dict(),
    }
    payload = {
        "seed": RANDOM_SEED,
        "null_gene_sets_per_signature": N_NULL_SETS,
        "bootstrap_repeats": N_BOOTSTRAP,
        "provenance": provenance_payload,
        "summary": summary.to_dict(orient="records"),
    }
    (RESULTS / "ACC_transport_audit_v2.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    columns = [
        "signature",
        "apparent_internal_auc",
        "same_gene_cv_auc_sensitivity",
        "external_auc",
        "absolute_internal_external_gap",
        "external_auc_ci_low",
        "external_auc_ci_high",
        "control_normalized_gap_ratio",
        "control_normalized_gap_ratio_ci_low",
        "control_normalized_gap_ratio_ci_high",
        "axis_r2_observed",
        "axis_r2_null_q95",
        "axis_r2_empirical_p",
        "transportability_status",
        "novelty_axis_status",
        "axis_r2_stability",
        "provenance_grade",
    ]
    print(summary[columns].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
