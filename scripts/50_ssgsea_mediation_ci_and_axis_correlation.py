"""Bootstrap mediation proportions and target-axis correlation for ssGSEA."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from scipy.stats import pearsonr, spearmanr
from sklearn.preprocessing import StandardScaler
from statsmodels.duration.hazard_regression import PHReg


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SIGNATURE = "immune_ssgsea_13gene_2022"
COHORTS = ("GSE33371", "GSE19750")
BOOTSTRAP_REPEATS = 500
RANDOM_SEED = 20261110


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_module(ROOT / "scripts" / "28_acc_signature_transport_pilot.py", "acc_base")
audit = load_module(ROOT / "scripts" / "29_acc_transport_audit_v2.py", "acc_audit")
multi = load_module(
    ROOT / "scripts" / "31_acc_signature_cohort_transport_matrix.py",
    "acc_multi",
)


def fit_beta(frame: pd.DataFrame, covariates: list[str]) -> float:
    model = PHReg(
        frame["time"].to_numpy(dtype=float),
        frame[covariates].to_numpy(dtype=float),
        status=frame["event"].to_numpy(dtype=int),
        strata=frame["cohort_id"].to_numpy(dtype=int),
        ties="efron",
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = model.fit(disp=False)
    return float(result.params[covariates.index("signature_score")])


def proportions(
    beta_total_unadjusted: float,
    beta_total_confounder: float,
    beta_direct: float,
) -> tuple[float, float]:
    unadjusted_denominator = (
        (beta_total_unadjusted - beta_direct) / beta_total_unadjusted
    )
    confounder_denominator = (
        (beta_total_confounder - beta_direct) / beta_total_confounder
    )
    return float(unadjusted_denominator), float(confounder_denominator)


def main() -> None:
    geo33371_expression, geo33371_samples = base.load_gse33371()
    gse19750_expression, gse19750_samples = multi.load_gpl570_series(
        ROOT / "data" / "geo_audit" / "GSE19750" / "GSE19750_series_matrix.txt.gz",
        ROOT / "registry" / "samples" / "GSE19750-samples_20261109.csv",
        "Carcinoma",
    )
    expressions = {
        "GSE33371": geo33371_expression,
        "GSE19750": gse19750_expression,
    }
    outcomes = {
        "GSE33371": geo33371_samples,
        "GSE19750": gse19750_samples,
    }
    definition = audit.SIGNATURES[SIGNATURE]

    frames = []
    correlation_rows = []
    for cohort in COHORTS:
        score, _ = base.score_signature(
            expressions[cohort],
            definition["genes"],
            definition["weights"],
        )
        axes = base.program_scores(expressions[cohort])
        score_z = StandardScaler().fit_transform(
            score.to_numpy().reshape(-1, 1)
        ).ravel()
        immune_z = StandardScaler().fit_transform(
            axes.loc[score.index, "immune"].to_numpy().reshape(-1, 1)
        ).ravel()
        pearson_r, pearson_p = pearsonr(score_z, immune_z)
        spearman_r, spearman_p = spearmanr(score_z, immune_z)
        correlation_rows.append(
            {
                "cohort": cohort,
                "n": len(score_z),
                "pearson_r_with_immune_axis": pearson_r,
                "pearson_p": pearson_p,
                "spearman_rho_with_immune_axis": spearman_r,
                "spearman_p": spearman_p,
            }
        )
        frame = pd.DataFrame(
            {
                "cohort": cohort,
                "signature_score": score_z,
                "time": outcomes[cohort]["os_years"].to_numpy(dtype=float),
                "event": outcomes[cohort]["os_event"].to_numpy(dtype=int),
            },
            index=score.index,
        )
        for axis in ["proliferation", "fibroblast_ecm", "adrenal_cortex"]:
            frame[axis] = StandardScaler().fit_transform(
                axes.loc[score.index, axis].to_numpy().reshape(-1, 1)
            ).ravel()
        frames.append(frame)

    data = pd.concat(frames)
    data["cohort_id"] = pd.Categorical(
        data["cohort"],
        categories=list(COHORTS),
    ).codes

    total_unadjusted = fit_beta(data, ["signature_score"])
    total_confounder = fit_beta(
        data,
        [
            "signature_score",
            "fibroblast_ecm",
            "adrenal_cortex",
        ],
    )
    direct = fit_beta(
        data,
        [
            "signature_score",
            "proliferation",
            "fibroblast_ecm",
            "adrenal_cortex",
        ],
    )
    prop_unadjusted, prop_confounder = proportions(
        total_unadjusted,
        total_confounder,
        direct,
    )

    rng = np.random.default_rng(RANDOM_SEED)
    bootstrap = {
        "total_unadjusted": [],
        "total_confounder": [],
        "direct": [],
        "prop_unadjusted": [],
        "prop_confounder": [],
    }
    cohort_frames = {
        cohort: data[data["cohort"].eq(cohort)]
        for cohort in COHORTS
    }
    for _ in range(BOOTSTRAP_REPEATS):
        sampled = []
        for cohort in COHORTS:
            cohort_frame = cohort_frames[cohort]
            indices = rng.integers(0, len(cohort_frame), len(cohort_frame))
            sampled.append(cohort_frame.iloc[indices])
        sample = pd.concat(sampled)
        sample["cohort_id"] = pd.Categorical(
            sample["cohort"],
            categories=list(COHORTS),
        ).codes
        try:
            beta_total_unadj = fit_beta(sample, ["signature_score"])
            beta_total_conf = fit_beta(
                sample,
                [
                    "signature_score",
                    "fibroblast_ecm",
                    "adrenal_cortex",
                ],
            )
            beta_direct = fit_beta(
                sample,
                [
                    "signature_score",
                    "proliferation",
                    "fibroblast_ecm",
                    "adrenal_cortex",
                ],
            )
        except Exception:
            continue
        prop_unadj, prop_conf = proportions(
            beta_total_unadj,
            beta_total_conf,
            beta_direct,
        )
        bootstrap["total_unadjusted"].append(beta_total_unadj)
        bootstrap["total_confounder"].append(beta_total_conf)
        bootstrap["direct"].append(beta_direct)
        bootstrap["prop_unadjusted"].append(prop_unadj)
        bootstrap["prop_confounder"].append(prop_conf)

    result = pd.DataFrame(
        [
            {
                "metric": "total_unadjusted_log_hr",
                "estimate": total_unadjusted,
                "ci_low": np.quantile(bootstrap["total_unadjusted"], 0.025),
                "ci_high": np.quantile(bootstrap["total_unadjusted"], 0.975),
            },
            {
                "metric": "total_confounder_adjusted_log_hr",
                "estimate": total_confounder,
                "ci_low": np.quantile(bootstrap["total_confounder"], 0.025),
                "ci_high": np.quantile(bootstrap["total_confounder"], 0.975),
            },
            {
                "metric": "direct_log_hr_adjusting_mediator_and_confounders",
                "estimate": direct,
                "ci_low": np.quantile(bootstrap["direct"], 0.025),
                "ci_high": np.quantile(bootstrap["direct"], 0.975),
            },
            {
                "metric": "proportion_mediated_unadjusted_denominator",
                "estimate": prop_unadjusted,
                "ci_low": np.quantile(bootstrap["prop_unadjusted"], 0.025),
                "ci_high": np.quantile(bootstrap["prop_unadjusted"], 0.975),
            },
            {
                "metric": "proportion_mediated_confounder_adjusted_denominator",
                "estimate": prop_confounder,
                "ci_low": np.quantile(bootstrap["prop_confounder"], 0.025),
                "ci_high": np.quantile(bootstrap["prop_confounder"], 0.975),
            },
        ]
    )
    result["bootstrap_method"] = "percentile"
    result["bootstrap_repeats_requested"] = BOOTSTRAP_REPEATS
    result["bootstrap_repeats_valid"] = len(
        bootstrap["total_unadjusted"]
    )
    result["stratified_by_cohort"] = True
    result["ci_type"] = "percentile_2.5_97.5"
    result.to_csv(
        RESULTS / "RATA_v5_ssgsea_mediation_bootstrap.csv",
        index=False,
    )
    correlations = pd.DataFrame(correlation_rows)
    correlations.to_csv(
        RESULTS / "RATA_v5_ssgsea_immune_axis_correlation.csv",
        index=False,
    )

    payload = {
        "signature": SIGNATURE,
        "bootstrap_repeats_requested": BOOTSTRAP_REPEATS,
        "bootstrap_repeats_valid": len(bootstrap["total_unadjusted"]),
        "bootstrap_method": "percentile",
        "stratified_by_cohort": True,
        "ci_type": "percentile_2.5_97.5",
        "mediation_results": result.to_dict(orient="records"),
        "axis_correlations": correlations.to_dict(orient="records"),
        "note": (
            "Descriptive mediation: direct model adjusts proliferation, "
            "fibroblast/stroma and lineage. No causal mediation claim. "
            "Negative CI lower bounds mean indirect and direct effects may "
            "have opposite signs, not a negative mediated proportion."
        ),
    }
    (RESULTS / "RATA_v5_ssgsea_mediation_bootstrap.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    print(result.round(4).to_string(index=False))
    print("\nAxis correlations")
    print(correlations.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
