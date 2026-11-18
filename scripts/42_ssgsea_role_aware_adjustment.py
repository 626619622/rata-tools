"""Role-aware adjustment for the ssGSEA immune prognostic signature."""

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
SIGNATURE = "immune_ssgsea_13gene_2022"
COHORTS = ("GSE33371", "GSE19750")


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


def fit_model(frame: pd.DataFrame, covariates: list[str], name: str) -> dict:
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
    index = covariates.index("signature_score")
    beta = float(result.params[index])
    se = float(result.bse[index])
    return {
        "model": name,
        "covariates": ";".join(covariates),
        "n": len(frame),
        "events": int(frame["event"].sum()),
        "covariate_count": len(covariates),
        "events_per_covariate": int(frame["event"].sum()) / len(covariates),
        "signature_hr": float(np.exp(beta)),
        "signature_ci_low": float(np.exp(beta - 1.96 * se)),
        "signature_ci_high": float(np.exp(beta + 1.96 * se)),
        "signature_p": float(result.pvalues[index]),
        "log_hr": beta,
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
        for axis in [
            "immune",
            "proliferation",
            "fibroblast_ecm",
            "adrenal_cortex",
        ]:
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
        (["signature_score"], "unadjusted_total_effect"),
        (
            [
                "signature_score",
                "fibroblast_ecm",
                "adrenal_cortex",
            ],
            "confounder_adjusted_stroma_lineage",
        ),
        (
            ["signature_score", "proliferation"],
            "mediator_adjusted_proliferation",
        ),
        (
            ["signature_score", "immune"],
            "target_overadjustment_sensitivity",
        ),
        (
            [
                "signature_score",
                "proliferation",
                "immune",
                "fibroblast_ecm",
                "adrenal_cortex",
            ],
            "fully_overadjusted_sensitivity",
        ),
    ]
    result = pd.DataFrame(
        [fit_model(data, covariates, name) for covariates, name in models]
    )

    total_log_hr = result.loc[
        result["model"].eq("unadjusted_total_effect"),
        "log_hr",
    ].iloc[0]
    direct_log_hr = result.loc[
        result["model"].eq("mediator_adjusted_proliferation"),
        "log_hr",
    ].iloc[0]
    proportion_mediated = (
        (total_log_hr - direct_log_hr) / total_log_hr
        if total_log_hr != 0
        else float("nan")
    )
    confounder = result[
        result["model"].eq("confounder_adjusted_stroma_lineage")
    ].iloc[0]
    gate3_pass = (
        confounder["signature_hr"] > 1
        and confounder["signature_ci_low"] > 1
        and confounder["signature_p"] < 0.05
    )

    result.to_csv(
        RESULTS / "RATA_v5_ssgsea_role_aware_adjustment.csv",
        index=False,
    )
    payload = {
        "signature": SIGNATURE,
        "target_domain": "immune-related prognostic program",
        "confounders": ["fibroblast_ecm", "adrenal_cortex"],
        "mediator": "proliferation",
        "do_not_adjust_primary": ["immune"],
        "n": int(len(data)),
        "events": int(data["event"].sum()),
        "gate3_role_aware_pass": bool(gate3_pass),
        "proportion_of_log_hr_mediated_by_proliferation": float(
            proportion_mediated
        ),
        "causal_mediation_note": (
            "The mediated proportion is a descriptive difference in log-HR, "
            "not a formal causal mediation estimate."
        ),
        "models": result.to_dict(orient="records"),
    }
    (RESULTS / "RATA_v5_ssgsea_role_aware_adjustment.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    print(result.round(4).to_string(index=False))
    print("\nGate3 pass:", gate3_pass)
    print("Proportion mediated:", round(proportion_mediated, 4))


if __name__ == "__main__":
    main()
