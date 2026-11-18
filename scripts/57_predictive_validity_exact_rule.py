"""Evaluate the frozen preflight rule for RATA predictive validity."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from sklearn.metrics import roc_auc_score
from statsmodels.stats.proportion import proportion_confint


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RANDOM_SEED = 20261110


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


sim = load_module(
    ROOT / "scripts" / "43_rata_known_truth_gate_simulation.py",
    "rata_simulation",
)


def dev_gate3_pass(
    y_dev: np.ndarray,
    score_dev: np.ndarray,
    confounder_dev: np.ndarray,
) -> tuple[bool, float, float]:
    design = sm.add_constant(
        np.column_stack([score_dev, confounder_dev]),
        has_constant="add",
    )
    result = sm.Logit(y_dev, design).fit(disp=False, maxiter=1000)
    beta = float(result.params[1])
    return bool(beta > 0 and result.pvalues[1] < 0.05), float(
        np.exp(beta)
    ), float(result.pvalues[1])


def main() -> None:
    rng = np.random.default_rng(RANDOM_SEED)
    gate1_threshold, _ = sim.calibration_threshold(rng)
    rows = []
    for scenario, parameters in sim.SCENARIOS.items():
        for simulation in range(sim.N_SIMULATIONS):
            dev_x, dev_y, dev_confounder = sim.simulate_cohort(
                rng,
                sim.N_DEV,
                parameters["dev_target_effect"],
                parameters["confounder_effect"],
            )
            ext_x, ext_y, _ = sim.simulate_cohort(
                rng,
                sim.N_EXT,
                parameters["ext_target_effect"],
                parameters["confounder_effect"],
            )
            selected, signs = sim.select_signature(dev_x, dev_y)
            score_dev = sim.score_with_signature(dev_x, selected, signs)
            score_ext = sim.score_with_signature(ext_x, selected, signs)
            dev_auc = roc_auc_score(dev_y, score_dev)
            ext_auc = roc_auc_score(ext_y, score_ext)
            gate1_pass = dev_auc > gate1_threshold
            gate3_pass, dev_or, dev_p = dev_gate3_pass(
                dev_y,
                score_dev,
                dev_confounder,
            )
            predicted_fail = int((not gate1_pass) or (not gate3_pass))
            actual_fail = int(
                ext_auc <= 0.60
                or np.sign(dev_auc - 0.5) != np.sign(ext_auc - 0.5)
            )
            rows.append(
                {
                    "scenario": scenario,
                    "simulation": simulation,
                    "gate1_pass": gate1_pass,
                    "preflight_gate3_pass": gate3_pass,
                    "predicted_gate2_fail": predicted_fail,
                    "actual_gate2_fail": actual_fail,
                    "development_auc": dev_auc,
                    "external_auc": ext_auc,
                    "development_adjusted_or": dev_or,
                    "development_adjusted_p": dev_p,
                }
            )

    frame = pd.DataFrame(rows)
    frame.to_csv(
        RESULTS / "RATA_v5_predictive_validity_simulation_per_run.csv",
        index=False,
    )
    predicted = frame["predicted_gate2_fail"].to_numpy()
    actual = frame["actual_gate2_fail"].to_numpy()
    auc = roc_auc_score(actual, predicted)
    tp = int(np.sum((predicted == 1) & (actual == 1)))
    tn = int(np.sum((predicted == 0) & (actual == 0)))
    fp = int(np.sum((predicted == 1) & (actual == 0)))
    fn = int(np.sum((predicted == 0) & (actual == 1)))
    sensitivity = tp / max(tp + fn, 1)
    specificity = tn / max(tn + fp, 1)
    sens_ci = proportion_confint(tp, tp + fn, method="wilson")
    spec_ci = proportion_confint(tn, tn + fp, method="wilson")

    real_pairs = pd.read_csv(
        RESULTS / "RATA_v3_pair_registry_and_transport.csv"
    )
    real_pairs = real_pairs[
        real_pairs["external_cohort"].isin(["TCGA", "GSE33371", "GSE19750"])
    ]
    real_power_limited = len(real_pairs) < 10

    summary = {
        "gate1_threshold": gate1_threshold,
        "runs": len(frame),
        "auroc": float(auc),
        "sensitivity": float(sensitivity),
        "sensitivity_ci_low": float(sens_ci[0]),
        "sensitivity_ci_high": float(sens_ci[1]),
        "specificity": float(specificity),
        "specificity_ci_low": float(spec_ci[0]),
        "specificity_ci_high": float(spec_ci[1]),
        "success_criteria": {
            "auroc_ge_0_70": bool(auc >= 0.70),
            "sensitivity_ge_0_70": bool(sensitivity >= 0.70),
            "specificity_ge_0_60": bool(specificity >= 0.60),
        },
        "real_data_evaluable_pairs": int(len(real_pairs)),
        "real_data_power_limited": real_power_limited,
        "real_data_decision": (
            "power_limited_case_study_only" if real_power_limited else "eligible"
        ),
    }
    (RESULTS / "RATA_v5_predictive_validity_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
