"""Per-axis R2 with bootstrap CI and internal/external comparison."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RANDOM_SEED = 20261109
BOOTSTRAP_REPEATS = 500


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

CONTEXTS = {
    "hypoxia_3gene_2021": [
        ("TCGA", "development"),
        ("GSE33371", "independent_external"),
    ],
    "immune_irg_3gene_2022": [
        ("TCGA", "development"),
        ("GSE33371", "overlap_external"),
    ],
    "prognostic_3gene_2021": [
        ("GSE33371", "development"),
        ("GSE19750", "development"),
        ("TCGA", "independent_external"),
    ],
    "immune_ssgsea_13gene_2022": [
        ("TCGA", "development"),
        ("GSE33371", "independent_external"),
        ("GSE19750", "independent_external"),
    ],
    "metabolic_5gene_2021": [
        ("TCGA", "development"),
        ("GSE33371", "independent_external"),
    ],
    "atf_creb_7gene_2025": [
        ("TCGA", "development"),
        ("GSE19750", "independent_external"),
    ],
}


def in_sample_r2(target: np.ndarray, design: np.ndarray) -> float:
    model = LinearRegression().fit(design, target)
    prediction = model.predict(design)
    residual = np.sum((target - prediction) ** 2)
    total = np.sum((target - target.mean()) ** 2)
    return float(1 - residual / max(total, 1e-12))


def axis_estimates(
    target: np.ndarray,
    axes: np.ndarray,
    axis_names: list[str],
) -> dict[str, tuple[float, float]]:
    full = in_sample_r2(target, axes)
    estimates = {}
    for index, axis in enumerate(axis_names):
        single = in_sample_r2(target, axes[:, [index]])
        reduced = in_sample_r2(
            target,
            axes[:, [i for i in range(len(axis_names)) if i != index]],
        )
        estimates[axis] = (single, full - reduced)
    return estimates


def cohort_axes(
    cohort: str,
    expression: pd.DataFrame,
    outcomes: pd.DataFrame,
) -> pd.DataFrame:
    if cohort == "TCGA":
        return outcomes[
            [
                "adrenal_cortex",
                "proliferation",
                "immune",
                "fibroblast_ecm",
                "hypoxia_glycolysis",
            ]
        ]
    return base.program_scores(expression)


def main() -> None:
    tcga_expression, tcga_outcomes = base.load_tcga()
    geo33371_expression, geo33371_samples = base.load_gse33371()
    gse19750_expression, gse19750_samples = multi.load_gpl570_series(
        ROOT / "data" / "geo_audit" / "GSE19750" / "GSE19750_series_matrix.txt.gz",
        ROOT / "registry" / "samples" / "GSE19750-samples_20261109.csv",
        "Carcinoma",
    )
    expressions = {
        "TCGA": tcga_expression,
        "GSE33371": geo33371_expression,
        "GSE19750": gse19750_expression,
    }
    outcomes = {
        "TCGA": tcga_outcomes,
        "GSE33371": geo33371_samples,
        "GSE19750": gse19750_samples,
    }

    rows = []
    for signature_index, (signature, contexts) in enumerate(CONTEXTS.items()):
        definition = audit.SIGNATURES[signature]
        for context_index, (cohort, role) in enumerate(contexts):
            score, _ = base.score_signature(
                expressions[cohort],
                definition["genes"],
                definition["weights"],
            )
            axes = cohort_axes(cohort, expressions[cohort], outcomes[cohort])
            axis_names = list(axes.columns)
            x = axes.to_numpy(dtype=float)
            y = score.to_numpy(dtype=float)
            point = axis_estimates(y, x, axis_names)

            rng = np.random.default_rng(
                RANDOM_SEED + signature_index * 100 + context_index
            )
            bootstrap = {
                axis: {"single": [], "partial": []}
                for axis in axis_names
            }
            for _ in range(BOOTSTRAP_REPEATS):
                indices = rng.integers(0, len(y), len(y))
                estimates = axis_estimates(y[indices], x[indices], axis_names)
                for axis, (single, partial) in estimates.items():
                    bootstrap[axis]["single"].append(single)
                    bootstrap[axis]["partial"].append(partial)

            for axis in axis_names:
                single, partial = point[axis]
                single_values = np.asarray(bootstrap[axis]["single"])
                partial_values = np.asarray(bootstrap[axis]["partial"])
                partial_low = float(np.quantile(partial_values, 0.025))
                partial_high = float(np.quantile(partial_values, 0.975))
                rows.append(
                    {
                        "signature": signature,
                        "cohort": cohort,
                        "cohort_role": role,
                        "n": len(score),
                        "axis": axis,
                        "single_axis_r2": single,
                        "single_axis_r2_ci_low": float(
                            np.quantile(single_values, 0.025)
                        ),
                        "single_axis_r2_ci_high": float(
                            np.quantile(single_values, 0.975)
                        ),
                        "partial_r2": partial,
                        "partial_r2_ci_low": partial_low,
                        "partial_r2_ci_high": partial_high,
                        "stable_partial_axis": partial_low > 0,
                    }
                )

    result = pd.DataFrame(rows)
    result.to_csv(
        RESULTS / "RATA_v4_per_axis_r2_ci.csv",
        index=False,
    )

    hypoxia = result[
        result["signature"].eq("hypoxia_3gene_2021")
    ].copy()
    hypoxia.to_csv(
        RESULTS / "RATA_v4_hypoxia_axis_internal_external.csv",
        index=False,
    )
    dominant = (
        result.sort_values("partial_r2", ascending=False)
        .groupby(["signature", "cohort"], as_index=False)
        .head(3)
    )
    payload = {
        "bootstrap_repeats": BOOTSTRAP_REPEATS,
        "hypoxia_comparison": hypoxia.to_dict(orient="records"),
        "dominant_axes": dominant.to_dict(orient="records"),
    }
    (RESULTS / "RATA_v4_axis_ci_comparison.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    print(hypoxia.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
