"""Pilot the transport audit with three fully specified ACC signatures.

The goal is not to develop another signature. It is to test whether published
ACC prognostic scores transport across a different platform and to separate
true external validation from cohorts already used in signature development.
"""

from __future__ import annotations

import gzip
import io
import json
from pathlib import Path
import re

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import LinearRegression
from sklearn.metrics import roc_auc_score


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESULTS = ROOT / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

TCGA_EXPRESSION = DATA / "unified" / "tcga" / "ACC_primary_expression.tsv"
TCGA_OUTCOMES = DATA / "unified" / "tcga" / "ACC_primary_outcomes_axes.tsv"
GSE33371_MATRIX = DATA / "geo_audit" / "GSE33371" / "GSE33371_series_matrix.txt.gz"
GSE33371_SAMPLES = ROOT / "registry" / "samples" / "GSE33371-samples.csv"
GPL570_MAP = DATA / "platforms" / "GPL570_probe_to_symbol_20261109.csv"


SIGNATURES = {
    "hypoxia_3gene_2021": {
        "source_pmid": "34603443",
        "doi": "10.1155/2021/2298973",
        "genes": ["CCNA2", "EFNA3", "COL5A1"],
        "weights": [0.81, 0.46, 0.38],
        "development": ["TCGA"],
        "reported_validation": ["GSE19750"],
        "gse33371_independent": True,
        "independence_reason": (
            "Original score used TCGA and GSE19750; GSE33371 is not either."
        ),
    },
    "immune_irg_3gene_2022": {
        "source_pmid": "36039643",
        "doi": "10.1002/iid3.680",
        "genes": ["INHBA", "HELLS", "HDAC4"],
        "weights": [1.647, 2.583, 2.61],
        "development": ["TCGA training subset"],
        "reported_validation": ["TCGA testing", "GSE10927", "GSE19750"],
        "gse33371_independent": False,
        "independence_reason": (
            "GSE33371 contains the same expression arrays as GSE10927."
        ),
    },
    "prognostic_3gene_2021": {
        "source_pmid": "34858497",
        "doi": "10.1155/2021/2077633",
        "genes": ["TIGD1", "SGK1", "MKI67"],
        "weights": [0.036112, -0.10388, 0.065722],
        "development": ["GSE10927", "GSE19750"],
        "reported_validation": ["GSE49278", "TCGA"],
        "gse33371_independent": False,
        "independence_reason": (
            "GSE33371 contains the same expression arrays as discovery data."
        ),
    },
}

PROGRAMS = {
    "adrenal_cortex": [
        "NR5A1",
        "STAR",
        "CYP11A1",
        "HSD3B2",
        "CYP21A2",
        "CYP11B1",
        "CYP17A1",
        "MC2R",
    ],
    "proliferation": [
        "MKI67",
        "TOP2A",
        "CCNB1",
        "CDK1",
        "AURKA",
        "BUB1",
        "PLK1",
        "PCNA",
    ],
    "immune": [
        "PTPRC",
        "CD3D",
        "CD3E",
        "CD8A",
        "CD68",
        "AIF1",
        "CXCL9",
        "CXCL10",
        "GZMA",
        "PRF1",
    ],
    "fibroblast_ecm": [
        "COL1A1",
        "COL1A2",
        "COL3A1",
        "FAP",
        "ACTA2",
        "TAGLN",
        "FN1",
        "POSTN",
        "LUM",
    ],
    "hypoxia_glycolysis": [
        "VEGFA",
        "CA9",
        "SLC2A1",
        "LDHA",
        "PGK1",
        "ENO1",
        "HK2",
        "PFKP",
    ],
}

POSITIVE_CONTROL = {
    "proliferation_positive_control": {
        "source_pmid": "positive control",
        "doi": "",
        "genes": PROGRAMS["proliferation"],
        "weights": [1.0] * len(PROGRAMS["proliferation"]),
        "development": ["predefined biological program"],
        "reported_validation": [],
        "gse33371_independent": True,
        "independence_reason": "Predefined positive control.",
    }
}

SIGNATURES.update(POSITIVE_CONTROL)


def zscore_rows(matrix: pd.DataFrame) -> pd.DataFrame:
    mean = matrix.mean(axis=1)
    sd = matrix.std(axis=1).replace(0, np.nan)
    return matrix.sub(mean, axis=0).div(sd, axis=0)


def collapse_genes(matrix: pd.DataFrame) -> pd.DataFrame:
    matrix = matrix.apply(pd.to_numeric, errors="coerce")
    matrix = matrix.loc[matrix.notna().all(axis=1)]
    return matrix.groupby(level=0).median()


def load_tcga() -> tuple[pd.DataFrame, pd.DataFrame]:
    expression = pd.read_csv(TCGA_EXPRESSION, sep="\t").set_index("gene")
    expression = collapse_genes(expression)
    outcomes = pd.read_csv(TCGA_OUTCOMES, sep="\t").set_index("sample")
    shared = expression.columns.intersection(outcomes.index)
    return expression[shared], outcomes.loc[shared]


def load_series_matrix() -> pd.DataFrame:
    lines = gzip.open(
        GSE33371_MATRIX,
        "rt",
        encoding="utf-8",
        errors="replace",
    ).readlines()
    begin = next(
        index
        for index, line in enumerate(lines)
        if line.startswith("!series_matrix_table_begin")
    )
    end = next(
        index
        for index, line in enumerate(lines)
        if line.startswith("!series_matrix_table_end")
    )
    table_lines = lines[begin + 1 : end]
    return pd.read_csv(io.StringIO("".join(table_lines)), sep="\t", index_col=0)


def parse_characteristics(value: str) -> dict[str, str]:
    result = {}
    for part in str(value).split(" | "):
        if ":" not in part:
            continue
        key, item = part.split(":", 1)
        result[key.strip().lower()] = item.strip()
    return result


def load_gse33371() -> tuple[pd.DataFrame, pd.DataFrame]:
    probes = load_series_matrix()
    annotation = pd.read_csv(GPL570_MAP)
    annotation = annotation.dropna(subset=["PROBEID", "SYMBOL"])
    annotation = annotation[["PROBEID", "SYMBOL"]].drop_duplicates()
    probe_data = probes.rename_axis("PROBEID").reset_index()
    mapped = probe_data.merge(annotation, on="PROBEID", how="inner")
    mapped = mapped.drop(columns=["PROBEID"]).set_index("SYMBOL")
    expression = collapse_genes(mapped)

    samples = pd.read_csv(GSE33371_SAMPLES).set_index("gsm")
    parsed = samples["characteristics"].map(parse_characteristics).apply(pd.Series)
    samples = samples.join(parsed)
    samples = samples[
        samples["source"].astype(str).str.contains(
            "Adrenocortical Carcinoma",
            case=False,
            na=False,
        )
    ].copy()

    samples["os_years"] = pd.to_numeric(
        samples.get("years to last followup"),
        errors="coerce",
    )
    samples["os_event"] = samples.get("dead or alive at last followup").map(
        {"dead": 1, "alive": 0}
    )
    samples["stage"] = pd.to_numeric(samples.get("tumor stage"), errors="coerce")
    samples["male"] = samples.get("sex").map({"M": 1, "F": 0})
    samples["age"] = pd.to_numeric(
        samples.get("age").astype(str).str.extract(r"(\d+)")[0],
        errors="coerce",
    )

    usable = (
        samples["os_years"].gt(0)
        & samples["os_event"].notna()
        & samples.index.isin(expression.columns)
    )
    samples = samples.loc[usable]
    shared = expression.columns.intersection(samples.index)
    return expression[shared], samples.loc[shared]


def score_signature(
    expression: pd.DataFrame,
    genes: list[str],
    weights: list[float],
) -> tuple[pd.Series, list[str]]:
    present = [gene for gene in genes if gene in expression.index]
    if len(present) != len(genes):
        missing = sorted(set(genes) - set(present))
        raise ValueError(f"Missing genes for score: {missing}")
    z = zscore_rows(expression.loc[genes])
    score = z.to_numpy().T @ np.asarray(weights, dtype=float)
    return pd.Series(score, index=expression.columns), genes


def auc_with_direction(score: pd.Series, labels: pd.Series) -> float:
    usable = pd.concat([score.rename("score"), labels.rename("label")], axis=1).dropna()
    if usable["label"].nunique() < 2:
        return float("nan")
    return float(roc_auc_score(usable["label"], usable["score"]))


def bootstrap_auc(
    score: pd.Series,
    labels: pd.Series,
    seed: int,
    repeats: int = 1500,
) -> tuple[float, float]:
    usable = pd.concat([score.rename("score"), labels.rename("label")], axis=1).dropna()
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(repeats):
        indices = rng.integers(0, len(usable), len(usable))
        sampled = usable.iloc[indices]
        if sampled["label"].nunique() < 2:
            continue
        values.append(roc_auc_score(sampled["label"], sampled["score"]))
    return float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))


def harrell_c_index(
    score: pd.Series,
    time: pd.Series,
    event: pd.Series,
) -> float:
    frame = pd.concat(
        [
            score.rename("score"),
            time.rename("time"),
            event.rename("event"),
        ],
        axis=1,
    ).dropna()
    concordant = 0.0
    comparable = 0
    values = frame.to_numpy(dtype=float)
    for first in range(len(values) - 1):
        for second in range(first + 1, len(values)):
            score_a, time_a, event_a = values[first]
            score_b, time_b, event_b = values[second]
            if time_a == time_b:
                continue
            if time_a < time_b and event_a == 1:
                comparable += 1
                concordant += float(score_a > score_b) + 0.5 * float(score_a == score_b)
            elif time_b < time_a and event_b == 1:
                comparable += 1
                concordant += float(score_b > score_a) + 0.5 * float(score_b == score_a)
    return concordant / comparable if comparable else float("nan")


def program_scores(expression: pd.DataFrame) -> pd.DataFrame:
    z = zscore_rows(expression)
    scores = {}
    for name, genes in PROGRAMS.items():
        present = [gene for gene in genes if gene in z.index]
        scores[name] = z.loc[present].mean(axis=0)
    return pd.DataFrame(scores)


def cross_fitted_axis_r2(
    score: pd.Series,
    axes: pd.DataFrame,
    seed: int,
    folds: int = 5,
) -> float:
    frame = pd.concat([score.rename("score"), axes], axis=1).dropna()
    x = frame[axes.columns].to_numpy(dtype=float)
    y = frame["score"].to_numpy(dtype=float)
    rng = np.random.default_rng(seed)
    indices = np.arange(len(y))
    rng.shuffle(indices)
    predictions = np.zeros_like(y)
    for fold_indices in np.array_split(indices, folds):
        train_indices = np.setdiff1d(indices, fold_indices)
        model = LinearRegression().fit(x[train_indices], y[train_indices])
        predictions[fold_indices] = model.predict(x[fold_indices])
    residual = np.sum((y - predictions) ** 2)
    total = np.sum((y - y.mean()) ** 2)
    return float(1 - residual / max(total, 1e-12))


def main() -> None:
    tcga_expression, tcga_outcomes = load_tcga()
    geo_expression, geo_samples = load_gse33371()

    tcga_axes = tcga_outcomes[
        [
            "adrenal_cortex",
            "proliferation",
            "immune",
            "fibroblast_ecm",
            "hypoxia_glycolysis",
        ]
    ]
    geo_axes = program_scores(geo_expression)

    score_rows = []
    axis_rows = []
    summary_rows = []
    provenance_rows = []

    for index, (signature, definition) in enumerate(SIGNATURES.items()):
        tcga_score, present = score_signature(
            tcga_expression,
            definition["genes"],
            definition["weights"],
        )
        geo_score, geo_present = score_signature(
            geo_expression,
            definition["genes"],
            definition["weights"],
        )
        if present != geo_present:
            raise RuntimeError("Gene coverage differs between cohorts")

        for cohort, score, outcomes, axes in (
            ("TCGA_ACC_internal", tcga_score, tcga_outcomes, tcga_axes),
            ("GSE33371_cross_platform", geo_score, geo_samples, geo_axes),
        ):
            os_auc = auc_with_direction(score, outcomes["os_event"])
            sex_auc = auc_with_direction(score, outcomes["male"])
            c_index = harrell_c_index(
                score,
                outcomes["os_years"] if cohort.startswith("GSE") else outcomes["os_months"],
                outcomes["os_event"],
            )
            axis_r2 = cross_fitted_axis_r2(
                score,
                axes,
                seed=20261109 + index,
            )
            score_rows.append(
                pd.DataFrame(
                    {
                        "signature": signature,
                        "cohort": cohort,
                        "sample": score.index,
                        "score": score.to_numpy(),
                    }
                )
            )
            summary_rows.append(
                {
                    "signature": signature,
                    "cohort": cohort,
                    "n": len(score),
                    "events": int(outcomes["os_event"].sum()),
                    "os_auc": os_auc,
                    "os_auc_ci_low": bootstrap_auc(
                        score,
                        outcomes["os_event"],
                        seed=20261109 + index,
                    )[0],
                    "os_auc_ci_high": bootstrap_auc(
                        score,
                        outcomes["os_event"],
                        seed=20261109 + index,
                    )[1],
                    "c_index": c_index,
                    "sex_auc_negative_control": sex_auc,
                    "cross_fitted_axis_r2": axis_r2,
                    "score_mean": float(score.mean()),
                    "score_sd": float(score.std()),
                }
            )
            for program in axes.columns:
                usable = pd.concat(
                    [score.rename("score"), axes[program].rename("program")],
                    axis=1,
                ).dropna()
                rho, p_value = spearmanr(usable["score"], usable["program"])
                axis_rows.append(
                    {
                        "signature": signature,
                        "cohort": cohort,
                        "program": program,
                        "spearman_rho": rho,
                        "p_value": p_value,
                    }
                )

        provenance_rows.append(
            {
                "signature": signature,
                "source_pmid": definition["source_pmid"],
                "doi": definition["doi"],
                "genes": ";".join(definition["genes"]),
                "weights": ";".join(map(str, definition["weights"])),
                "development": ";".join(definition["development"]),
                "reported_validation": ";".join(definition["reported_validation"]),
                "GSE33371_independent": definition["gse33371_independent"],
                "independence_reason": definition["independence_reason"],
            }
        )

    score_table = pd.concat(score_rows, ignore_index=True)
    summary = pd.DataFrame(summary_rows)
    axis_correlations = pd.DataFrame(axis_rows)
    provenance = pd.DataFrame(provenance_rows)

    internal = summary[summary["cohort"].eq("TCGA_ACC_internal")].set_index(
        "signature"
    )
    external = summary[summary["cohort"].eq("GSE33371_cross_platform")].set_index(
        "signature"
    )
    transport = provenance.set_index("signature").join(
        internal[["n", "events", "os_auc", "c_index"]].add_prefix("internal_")
    ).join(
        external[["n", "events", "os_auc", "c_index", "sex_auc_negative_control", "cross_fitted_axis_r2"]]
        .add_prefix("external_")
    )
    transport["internal_external_auc_gap"] = (
        transport["internal_os_auc"] - transport["external_os_auc"]
    )
    transport["direction_concordant"] = (
        np.sign(transport["internal_os_auc"] - 0.5)
        == np.sign(transport["external_os_auc"] - 0.5)
    )
    transport["true_independent_external_test"] = transport["GSE33371_independent"]

    def classify(row: pd.Series) -> str:
        if not row["true_independent_external_test"]:
            return "not_independently_testable"
        if row["external_os_auc"] >= 0.70 and row["direction_concordant"]:
            return "portable"
        if row["external_os_auc"] < 0.60 or not row["direction_concordant"]:
            return "failed_or_unstable"
        return "uncertain"

    transport["pilot_classification"] = transport.apply(classify, axis=1)

    score_table.to_csv(RESULTS / "ACC_signature_transport_pilot_scores.csv", index=False)
    summary.to_csv(RESULTS / "ACC_signature_transport_pilot_summary.csv", index=False)
    axis_correlations.to_csv(
        RESULTS / "ACC_signature_transport_pilot_axis_correlations.csv",
        index=False,
    )
    provenance.to_csv(
        RESULTS / "ACC_signature_transport_pilot_provenance.csv",
        index=False,
    )
    transport.reset_index().to_csv(
        RESULTS / "ACC_signature_transport_pilot_transport.csv",
        index=False,
    )

    payload = {
        "purpose": "ACC published-signature transport pilot",
        "tcga_samples": int(tcga_expression.shape[1]),
        "tcga_os_events": int(tcga_outcomes["os_event"].sum()),
        "gse33371_samples_with_survival": int(geo_expression.shape[1]),
        "gse33371_os_events": int(geo_samples["os_event"].sum()),
        "transport_results": transport.reset_index().to_dict(orient="records"),
    }
    (RESULTS / "ACC_signature_transport_pilot.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    columns = [
        "signature",
        "internal_os_auc",
        "external_os_auc",
        "internal_external_auc_gap",
        "external_c_index",
        "external_sex_auc_negative_control",
        "external_cross_fitted_axis_r2",
        "direction_concordant",
        "true_independent_external_test",
        "pilot_classification",
    ]
    print(transport.reset_index()[columns].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
