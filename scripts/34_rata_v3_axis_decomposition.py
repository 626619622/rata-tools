"""Per-axis and leave-one-gene-out decomposition for independent RATA pairs."""

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

EXTERNAL_PAIRS = {
    "hypoxia_3gene_2021": ["GSE33371"],
    "prognostic_3gene_2021": ["TCGA"],
    "immune_ssgsea_13gene_2022": ["GSE33371", "GSE19750"],
    "metabolic_5gene_2021": ["GSE33371"],
    "atf_creb_7gene_2025": ["GSE19750"],
}


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


def in_sample_r2(target: np.ndarray, design: np.ndarray) -> float:
    model = LinearRegression().fit(design, target)
    prediction = model.predict(design)
    residual = np.sum((target - prediction) ** 2)
    total = np.sum((target - target.mean()) ** 2)
    return float(1 - residual / max(total, 1e-12))


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

    axis_rows = []
    gene_rows = []
    null_rows = []

    for signature_index, (signature, cohorts) in enumerate(EXTERNAL_PAIRS.items()):
        definition = audit.SIGNATURES[signature]
        for cohort_index, cohort in enumerate(cohorts):
            score, _ = base.score_signature(
                expressions[cohort],
                definition["genes"],
                definition["weights"],
            )
            axes = cohort_axes(cohort, expressions[cohort], outcomes[cohort])
            axis_names = list(axes.columns)
            x_axes = axes.to_numpy(dtype=float)
            y = score.to_numpy(dtype=float)

            full_r2 = audit.fast_cross_fitted_r2(
                y,
                x_axes,
                seed=RANDOM_SEED + signature_index * 100 + cohort_index,
            )
            full_r2_in_sample = in_sample_r2(y, x_axes)
            for axis_index, axis in enumerate(axis_names):
                single_r2 = in_sample_r2(y, x_axes[:, [axis_index]])
                reduced_columns = [
                    index for index in range(len(axis_names)) if index != axis_index
                ]
                reduced_r2 = in_sample_r2(y, x_axes[:, reduced_columns])
                axis_rows.append(
                    {
                        "signature": signature,
                        "cohort": cohort,
                        "axis": axis,
                        "single_axis_in_sample_r2": single_r2,
                        "partial_r2_full_minus_drop_one": full_r2_in_sample - reduced_r2,
                        "full_model_in_sample_r2": full_r2_in_sample,
                        "drop_one_axis_in_sample_r2": reduced_r2,
                        "full_model_cross_fitted_r2": full_r2,
                    }
                )

            for gene_index, gene in enumerate(definition["genes"]):
                keep = [
                    index
                    for index in range(len(definition["genes"]))
                    if index != gene_index
                ]
                if keep:
                    reduced_score = (
                        base.zscore_rows(expressions[cohort].loc[
                            [definition["genes"][index] for index in keep]
                        ]).to_numpy().T
                        @ np.asarray(
                            [definition["weights"][index] for index in keep],
                            dtype=float,
                        )
                    )
                else:
                    reduced_score = np.zeros(len(score))
                leave_gene_out_r2 = audit.fast_cross_fitted_r2(
                    reduced_score,
                    x_axes,
                    seed=RANDOM_SEED + 300 + signature_index * 10 + gene_index,
                )
                gene_rows.append(
                    {
                        "signature": signature,
                        "cohort": cohort,
                        "gene": gene,
                        "weight": definition["weights"][gene_index],
                        "full_model_r2": full_r2,
                        "leave_this_gene_out_r2": leave_gene_out_r2,
                        "r2_drop_when_removed": full_r2 - leave_gene_out_r2,
                    }
                )

            null = audit.axis_null_benchmark(
                expressions[cohort],
                axes,
                k=len(definition["genes"]),
                observed_weights=definition["weights"],
                observed_r2=full_r2,
                seed=RANDOM_SEED + 500 + signature_index * 10 + cohort_index,
            )
            null_rows.append(
                {
                    "signature": signature,
                    "cohort": cohort,
                    "full_model_r2": full_r2,
                    "null_mean": null["null_mean"],
                    "null_q95": null["null_q95"],
                    "null_q99": null["null_q99"],
                    "empirical_p": null["empirical_p"],
                }
            )

    axis_table = pd.DataFrame(axis_rows)
    axis_table.to_csv(
        RESULTS / "RATA_v3_per_axis_r2.csv",
        index=False,
    )
    gene_table = pd.DataFrame(gene_rows)
    gene_table.to_csv(
        RESULTS / "RATA_v3_leave_one_gene_out_axis_r2.csv",
        index=False,
    )
    null_table = pd.DataFrame(null_rows)
    null_table.to_csv(
        RESULTS / "RATA_v3_axis_null_benchmark.csv",
        index=False,
    )

    dominant = (
        axis_table.sort_values(
            "partial_r2_full_minus_drop_one",
            ascending=False,
        )
        .groupby(["signature", "cohort"], as_index=False)
        .head(1)
    )
    payload = {
        "pairs": int(len(null_table)),
        "dominant_axis_by_pair": dominant.to_dict(orient="records"),
        "null_benchmark": null_table.to_dict(orient="records"),
    }
    (RESULTS / "RATA_v3_axis_decomposition.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    print(
        axis_table.sort_values(
            ["signature", "cohort", "partial_r2_full_minus_drop_one"],
            ascending=[True, True, False],
        )
        .round(4)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
