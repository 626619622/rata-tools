"""Audit the direction anomaly in the GSE19750 ACC survival subset."""

from __future__ import annotations

import importlib.util
import gzip
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RESULTS = ROOT / "results"
SAMPLES = ROOT / "registry" / "samples" / "GSE19750-samples_20261109.csv"
MATRIX = DATA / "geo_audit" / "GSE19750" / "GSE19750_series_matrix.txt.gz"
PROBE_MAP = DATA / "platforms" / "GPL570_probe_to_symbol_20261109.csv"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_module(ROOT / "scripts" / "28_acc_signature_transport_pilot.py", "acc_base")
audit = load_module(ROOT / "scripts" / "29_acc_transport_audit_v2.py", "acc_audit")


def load_expression() -> pd.DataFrame:
    lines = gzip.open(
        MATRIX,
        "rt",
        encoding="utf-8",
        errors="replace",
    ).readlines()
    begin = next(
        i for i, line in enumerate(lines) if line.startswith("!series_matrix_table_begin")
    )
    end = next(
        i for i, line in enumerate(lines) if line.startswith("!series_matrix_table_end")
    )
    probes = pd.read_csv(
        io.StringIO("".join(lines[begin + 1 : end])),
        sep="\t",
        index_col=0,
    )
    annotation = pd.read_csv(PROBE_MAP).dropna(
        subset=["PROBEID", "SYMBOL"]
    )[["PROBEID", "SYMBOL"]].drop_duplicates()
    probe_data = probes.rename_axis("PROBEID").reset_index()
    mapped = (
        probe_data.merge(annotation, on="PROBEID", how="inner")
        .drop(columns=["PROBEID"])
        .set_index("SYMBOL")
    )
    return base.collapse_genes(mapped)


def load_samples() -> pd.DataFrame:
    samples = pd.read_csv(SAMPLES).set_index("gsm")
    parsed = samples["characteristics"].map(base.parse_characteristics).apply(pd.Series)
    samples = samples.join(parsed)
    samples = samples[
        samples["title"].astype(str).str.contains(
            "Carcinoma",
            case=False,
            na=False,
        )
    ].copy()
    samples["time"] = pd.to_numeric(samples["survival in years"], errors="coerce")
    samples["event"] = samples["survival status"].map({"dead": 1, "alive": 0})
    samples["grade"] = pd.to_numeric(samples["tumor grade"], errors="coerce")
    samples["stage_numeric"] = pd.to_numeric(samples["stage"], errors="coerce")
    samples["batch"] = pd.to_numeric(samples["batch"], errors="coerce")
    samples["has_survival"] = (
        samples["time"].gt(0) & samples["event"].notna()
    ).astype(int)
    samples["grade_high"] = pd.Series(
        np.where(
            samples["grade"].notna(),
            (samples["grade"] >= 3).astype(float),
            np.nan,
        ),
        index=samples.index,
    )
    samples["stage_high"] = pd.Series(
        np.where(
            samples["stage_numeric"].notna(),
            (samples["stage_numeric"] >= 3).astype(float),
            np.nan,
        ),
        index=samples.index,
    )
    return samples


def safe_auc(score: pd.Series, labels: pd.Series) -> float:
    usable = pd.concat(
        [score.rename("score"), labels.rename("label")],
        axis=1,
    ).dropna()
    if usable["label"].nunique() < 2:
        return float("nan")
    return float(roc_auc_score(usable["label"], usable["score"]))


def bootstrap_ci(
    score: pd.Series,
    labels: pd.Series,
    seed: int,
    repeats: int = 2000,
) -> tuple[float, float]:
    usable = pd.concat(
        [score.rename("score"), labels.rename("label")],
        axis=1,
    ).dropna()
    if usable["label"].nunique() < 2:
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(repeats):
        indices = rng.integers(0, len(usable), len(usable))
        sample = usable.iloc[indices]
        if sample["label"].nunique() < 2:
            continue
        values.append(roc_auc_score(sample["label"], sample["score"]))
    return float(np.quantile(values, 0.025)), float(np.quantile(values, 0.975))


def direction_call(auc: float) -> str:
    if not np.isfinite(auc):
        return "not_estimable"
    if auc > 0.60:
        return "higher_score_worse"
    if auc < 0.40:
        return "higher_score_better"
    return "unstable_or_null"


def main() -> None:
    expression = load_expression()
    samples = load_samples()
    shared = expression.columns.intersection(samples.index)
    expression = expression[shared]
    samples = samples.loc[shared]

    rows = []
    for index, (signature, definition) in enumerate(audit.SIGNATURES.items()):
        score, _ = base.score_signature(
            expression,
            definition["genes"],
            definition["weights"],
        )
        valid_survival = samples["has_survival"].eq(1)
        valid_score = score.loc[valid_survival]
        valid_events = samples.loc[valid_survival, "event"]
        auc_grade = safe_auc(score, samples["grade_high"])
        auc_stage = safe_auc(score, samples["stage_high"])
        auc_death = safe_auc(valid_score, valid_events)
        auc_survival_subset = safe_auc(score, samples["has_survival"])
        auc_batch = safe_auc(score, samples["batch"].eq(2).astype(int))
        grade_ci = bootstrap_ci(
            score,
            samples["grade_high"],
            seed=20261109 + index,
        )
        stage_ci = bootstrap_ci(
            score,
            samples["stage_high"],
            seed=20261110 + index,
        )
        death_ci = bootstrap_ci(
            valid_score,
            valid_events,
            seed=20261111 + index,
        )

        calls = [direction_call(auc_grade), direction_call(auc_stage)]
        if calls.count("higher_score_worse") >= 1 and "higher_score_better" not in calls:
            overall_direction = "higher_score_worse_supported_by_grade_or_stage"
        elif calls.count("higher_score_better") >= 1:
            overall_direction = "clinical_direction_also_reversed"
        else:
            overall_direction = "clinical_direction_null_or_indeterminate"

        rows.append(
            {
                "signature": signature,
                "source_pmid": definition["source_pmid"],
                "formula_direction": "higher_score_worse",
                "gene_weight_signs": ";".join(
                    "positive" if weight >= 0 else "negative"
                    for weight in definition["weights"]
                ),
                "expression_n": len(score),
                "survival_n": int(samples["has_survival"].sum()),
                "events": int(valid_events.sum()),
                "event_definition": "dead=1; alive=0",
                "grade_high_n": int(samples["grade_high"].sum()),
                "stage_high_n": int(samples["stage_high"].sum()),
                "grade_auc": auc_grade,
                "grade_auc_ci_low": grade_ci[0],
                "grade_auc_ci_high": grade_ci[1],
                "grade_direction": direction_call(auc_grade),
                "stage_auc": auc_stage,
                "stage_auc_ci_low": stage_ci[0],
                "stage_auc_ci_high": stage_ci[1],
                "stage_direction": direction_call(auc_stage),
                "death_auc": auc_death,
                "death_auc_ci_low": death_ci[0],
                "death_auc_ci_high": death_ci[1],
                "death_direction": direction_call(auc_death),
                "survival_subset_membership_auc": auc_survival_subset,
                "batch_2_auc": auc_batch,
                "clinical_direction_audit": overall_direction,
                "interpretation_rule": (
                    "If grade/stage follow published direction but survival subset "
                    "does not, prioritise survival-subset or follow-up selection "
                    "over true biological reversal."
                ),
            }
        )

    result = pd.DataFrame(rows)
    result.to_csv(
        RESULTS / "GSE19750_direction_audit.csv",
        index=False,
    )

    payload = {
        "expression_n": int(len(score)),
        "survival_n": int(samples["has_survival"].sum()),
        "events": int(
            samples.loc[samples["has_survival"].eq(1), "event"].sum()
        ),
        "dead_status_total": int(samples["event"].eq(1).sum()),
        "zero_time_dead_excluded": int(
            (
                samples["event"].eq(1)
                & ~samples["has_survival"].eq(1)
            ).sum()
        ),
        "grade_high_n": int(samples["grade_high"].sum()),
        "stage_high_n": int(samples["stage_high"].sum()),
        "event_definition_verified": {
            "dead": int(samples["survival status"].eq("dead").sum()),
            "alive": int(samples["survival status"].eq("alive").sum()),
            "unknown": int(samples["survival status"].eq("Unknown").sum()),
            "na": int(samples["survival status"].isna().sum()),
        },
        "rows": result.to_dict(orient="records"),
    }
    (RESULTS / "GSE19750_direction_audit.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )

    columns = [
        "signature",
        "grade_auc",
        "grade_auc_ci_low",
        "grade_auc_ci_high",
        "stage_auc",
        "stage_auc_ci_low",
        "stage_auc_ci_high",
        "death_auc",
        "death_auc_ci_low",
        "death_auc_ci_high",
        "survival_subset_membership_auc",
        "batch_2_auc",
        "clinical_direction_audit",
    ]
    print(result[columns].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
