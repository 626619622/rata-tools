"""Known-axis adjustment of the only pooled independent RATA result."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from statsmodels.duration.hazard_regression import PHReg


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


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

SIGNATURE = "immune_ssgsea_13gene_2022"
COHORTS = ("GSE33371", "GSE19750")
AXES = [
    "proliferation",
    "immune",
    "fibroblast_ecm",
    "hypoxia_glycolysis",
    "adrenal_cortex",
]


def fit_model(
    frame: pd.DataFrame,
    covariates: list[str],
    model_name: str,
) -> dict:
    exog = frame[covariates].to_numpy(dtype=float)
    model = PHReg(
        frame["time"].to_numpy(dtype=float),
        exog,
        status=frame["event"].to_numpy(dtype=int),
        strata=frame["cohort_id"].to_numpy(dtype=int),
        ties="efron",
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = model.fit(disp=False)
    score_index = covariates.index("signature_score")
    beta = float(result.params[score_index])
    se = float(result.bse[score_index])
    p_value = float(result.pvalues[score_index])
    events = int(frame["event"].sum())
    return {
        "model": model_name,
        "covariates": ";".join(covariates),
        "n": len(frame),
        "events": events,
        "covariate_count": len(covariates),
        "events_per_covariate": events / len(covariates),
        "signature_hr": float(np.exp(beta)),
        "signature_ci_low": float(np.exp(beta - 1.96 * se)),
        "signature_ci_high": float(np.exp(beta + 1.96 * se)),
        "signature_p": p_value,
    }


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
    for cohort in COHORTS:
        score, _ = base.score_signature(
            expressions[cohort],
            definition["genes"],
            definition["weights"],
        )
        axes = base.program_scores(expressions[cohort])
        available_axes = [axis for axis in AXES if axis in axes.columns]
        frame = pd.DataFrame(
            {
                "cohort": cohort,
                "signature_score": StandardScaler().fit_transform(
                    score.to_numpy().reshape(-1, 1)
                ).ravel(),
                "time": outcomes[cohort]["os_years"].to_numpy(dtype=float),
                "event": outcomes[cohort]["os_event"].to_numpy(dtype=int),
            },
            index=score.index,
        )
        for axis in available_axes:
            frame[axis] = StandardScaler().fit_transform(
                axes.loc[score.index, axis].to_numpy().reshape(-1, 1)
            ).ravel()
        frames.append(frame)
    data = pd.concat(frames)
    data["cohort_id"] = pd.Categorical(
        data["cohort"],
        categories=list(COHORTS),
    ).codes

    models = [
        (["signature_score"], "unadjusted"),
        (["signature_score", "proliferation"], "adjust_proliferation"),
        (["signature_score", "immune"], "adjust_immune"),
        (["signature_score", "fibroblast_ecm"], "adjust_fibroblast_stroma"),
        (["signature_score", "hypoxia_glycolysis"], "adjust_hypoxia"),
        (
            [
                "signature_score",
                "proliferation",
                "immune",
                "fibroblast_ecm",
            ],
            "adjust_proliferation_immune_stroma",
        ),
        (
            ["signature_score", *AXES],
            "adjust_all_available_axes_sensitivity",
        ),
    ]
    rows = [fit_model(data, covariates, name) for covariates, name in models]
    result = pd.DataFrame(rows)

    unadjusted_hr = result.loc[
        result["model"].eq("unadjusted"),
        "signature_hr",
    ].iloc[0]
    fully_adjusted_hr = result.loc[
        result["model"].eq("adjust_proliferation_immune_stroma"),
        "signature_hr",
    ].iloc[0]
    fully_adjusted_p = result.loc[
        result["model"].eq("adjust_proliferation_immune_stroma"),
        "signature_p",
    ].iloc[0]
    attenuation = (unadjusted_hr - fully_adjusted_hr) / unadjusted_hr

    if fully_adjusted_p > 0.05:
        interpretation = "adjusted_signal_attenuated_or_uncertain"
    elif attenuation >= 0.30:
        interpretation = "partly_explained_by_known_axes_but_residual"
    else:
        interpretation = "largely_retained_after_known_axes"

    result.to_csv(
        RESULTS / "RATA_v4_ssgsea_known_axis_adjustment.csv",
        index=False,
    )
    payload = {
        "signature": SIGNATURE,
        "cohorts": list(COHORTS),
        "n": int(len(data)),
        "events": int(data["event"].sum()),
        "unadjusted_hr": float(unadjusted_hr),
        "full_adjusted_hr": float(fully_adjusted_hr),
        "full_adjusted_p": float(fully_adjusted_p),
        "relative_hr_attenuation": float(attenuation),
        "interpretation": interpretation,
        "purity_note": (
            "Direct tumor purity was unavailable in both external cohorts. "
            "Immune and fibroblast expression programs were used as measured "
            "microenvironment proxies; residual purity confounding remains."
        ),
        "models": result.to_dict(orient="records"),
    }
    (RESULTS / "RATA_v4_ssgsea_known_axis_adjustment.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    print(result.round(4).to_string(index=False))
    print("\nInterpretation:", interpretation)


if __name__ == "__main__":
    main()
