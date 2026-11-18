"""Build a signature-by-cohort ACC transportability matrix.

Independence is assessed at the signature-cohort pair level, not by calling an
entire dataset "external". A cohort may be independent for one published model
and have been used during development or validation of another.
"""

from __future__ import annotations

import gzip
import importlib.util
import io
import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
DATA = ROOT / "data"
REGISTRY = ROOT / "registry" / "samples"
PROBE_MAP = DATA / "platforms" / "GPL570_probe_to_symbol_20261109.csv"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = load_module(ROOT / "scripts" / "28_acc_signature_transport_pilot.py", "acc_base")
audit = load_module(ROOT / "scripts" / "29_acc_transport_audit_v2.py", "acc_audit_v2")


def load_gpl570_series(
    matrix_path: Path,
    sample_path: Path,
    source_pattern: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    lines = gzip.open(
        matrix_path,
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
    probes = pd.read_csv(
        io.StringIO("".join(lines[begin + 1 : end])),
        sep="\t",
        index_col=0,
    )

    annotation = pd.read_csv(PROBE_MAP).dropna(
        subset=["PROBEID", "SYMBOL"]
    )[["PROBEID", "SYMBOL"]].drop_duplicates()
    probe_data = probes.rename_axis("PROBEID").reset_index()
    mapped = probe_data.merge(annotation, on="PROBEID", how="inner")
    mapped = mapped.drop(columns=["PROBEID"]).set_index("SYMBOL")
    expression = base.collapse_genes(mapped)

    samples = pd.read_csv(sample_path).set_index("gsm")
    parsed = samples["characteristics"].map(base.parse_characteristics).apply(pd.Series)
    samples = samples.join(parsed)
    samples = samples[
        samples["title"].astype(str).str.contains(
            source_pattern,
            case=False,
            na=False,
        )
    ].copy()
    samples["os_years"] = pd.to_numeric(
        samples["survival in years"],
        errors="coerce",
    )
    samples["os_event"] = samples["survival status"].map(
        {"dead": 1, "alive": 0}
    )
    samples["stage"] = pd.to_numeric(samples["stage"], errors="coerce")
    samples["male"] = samples["gender"].map({"M": 1, "F": 0})
    samples["age"] = pd.to_numeric(samples["age in years"], errors="coerce")
    samples = samples[
        samples["os_years"].gt(0)
        & samples["os_event"].notna()
        & samples.index.isin(expression.columns)
    ]
    shared = expression.columns.intersection(samples.index)
    return expression[shared], samples.loc[shared]


INDEPENDENCE = {
    "hypoxia_3gene_2021": {
        "TCGA": ("D", "TCGA development cohort."),
        "GSE33371": ("A", "Not used in development or reported validation."),
        "GSE19750": ("C", "Used as reported validation."),
    },
    "immune_irg_3gene_2022": {
        "TCGA": ("D", "TCGA training/testing data."),
        "GSE33371": ("C", "Same arrays as GSE10927 validation."),
        "GSE19750": ("C", "Used as reported validation."),
    },
    "prognostic_3gene_2021": {
        "TCGA": ("A", "Reported external validation; not development data."),
        "GSE33371": ("C", "Same arrays as GSE10927 development."),
        "GSE19750": ("D", "GSE19750 is a development cohort."),
    },
    "immune_ssgsea_13gene_2022": {
        "TCGA": ("D", "TCGA development cohort."),
        "GSE33371": ("A", "Not used in development or reported validation."),
        "GSE19750": ("A", "Not used in development or reported validation."),
    },
    "metabolic_5gene_2021": {
        "TCGA": ("D", "TCGA development cohort."),
        "GSE33371": ("A", "Not used in development or reported validation."),
        "GSE19750": ("C", "Used as reported validation."),
    },
    "atf_creb_7gene_2025": {
        "TCGA": ("D", "TCGA development cohort."),
        "GSE33371": ("C", "Same arrays as GSE10927 validation."),
        "GSE19750": ("A", "Not used in development or reported validation."),
    },
}


def main() -> None:
    tcga_expression, tcga_outcomes = base.load_tcga()
    geo33371_expression, geo33371_samples = base.load_gse33371()
    gse19750_expression, gse19750_samples = load_gpl570_series(
        DATA / "geo_audit" / "GSE19750" / "GSE19750_series_matrix.txt.gz",
        REGISTRY / "GSE19750-samples_20261109.csv",
        "Carcinoma",
    )
    cohorts = {
        "TCGA": (tcga_expression, tcga_outcomes),
        "GSE33371": (geo33371_expression, geo33371_samples),
        "GSE19750": (gse19750_expression, gse19750_samples),
    }

    control_definition = {
        "genes": base.PROGRAMS["proliferation"],
        "weights": [1.0] * len(base.PROGRAMS["proliferation"]),
    }
    control_scores = {
        name: base.score_signature(expression, **control_definition)[0]
        for name, (expression, _) in cohorts.items()
    }

    rows = []
    for signature_index, (signature, definition) in enumerate(
        audit.SIGNATURES.items()
    ):
        signature_scores = {
            name: base.score_signature(
                expression,
                definition["genes"],
                definition["weights"],
            )[0]
            for name, (expression, _) in cohorts.items()
        }
        reference_auc = base.auc_with_direction(
            signature_scores["TCGA"],
            cohorts["TCGA"][1]["os_event"],
        )
        control_reference_auc = float(
            base.roc_auc_score(
                cohorts["TCGA"][1]["os_event"],
                control_scores["TCGA"],
            )
        )

        for cohort_index, (cohort_name, (_, outcomes)) in enumerate(cohorts.items()):
            score = signature_scores[cohort_name]
            auc = base.auc_with_direction(score, outcomes["os_event"])
            auc_low, auc_high = base.bootstrap_auc(
                score,
                outcomes["os_event"],
                seed=20261109 + signature_index * 10 + cohort_index,
            )
            control_auc = float(
                base.roc_auc_score(
                    outcomes["os_event"],
                    control_scores[cohort_name],
                )
            )
            grade, reason = INDEPENDENCE[signature][cohort_name]
            is_independent = grade == "A"

            if cohort_name != "TCGA" and is_independent:
                ratio, ratio_low, ratio_high, ratio_valid = (
                    audit.control_ratio_bootstrap(
                        signature_scores["TCGA"],
                        score,
                        control_scores["TCGA"],
                        control_scores[cohort_name],
                        cohorts["TCGA"][1]["os_event"],
                        outcomes["os_event"],
                        seed=20261109 + signature_index * 10 + cohort_index,
                    )
                )
            else:
                ratio = ratio_low = ratio_high = float("nan")
                ratio_valid = float("nan")

            direction_concordant = np.sign(reference_auc - 0.5) == np.sign(
                auc - 0.5
            )
            if not is_independent:
                transport_status = "not_independently_testable"
            elif not direction_concordant:
                transport_status = "direction_reversal"
            elif not np.isfinite(ratio):
                transport_status = "indeterminate_missing_matched_development_comparator"
            elif len(score) < 50 or int(outcomes["os_event"].sum()) < 20:
                transport_status = "indeterminate_underpowered"
            elif np.isfinite(ratio_low) and ratio_low > 1.0:
                transport_status = "relative_nontransport"
            elif np.isfinite(ratio_high) and ratio_high < 1.0:
                transport_status = "relative_transport_supported"
            else:
                transport_status = "indeterminate_ratio_ci_crosses_one"

            rows.append(
                {
                    "signature": signature,
                    "cohort": cohort_name,
                    "n": len(score),
                    "events": int(outcomes["os_event"].sum()),
                    "auc": auc,
                    "auc_ci_low": auc_low,
                    "auc_ci_high": auc_high,
                    "tcga_reference_auc": reference_auc,
                    "absolute_gap_vs_tcga": reference_auc - auc,
                    "direction_concordant_with_tcga": direction_concordant,
                    "positive_control_auc": control_auc,
                    "tcga_positive_control_auc": control_reference_auc,
                    "control_normalized_gap_ratio": ratio,
                    "control_normalized_gap_ratio_ci_low": ratio_low,
                    "control_normalized_gap_ratio_ci_high": ratio_high,
                    "control_ratio_bootstrap_valid_fraction": ratio_valid,
                    "provenance_grade": grade,
                    "independence_reason": reason,
                    "independent_test": is_independent,
                    "transportability_status": transport_status,
                }
            )

    matrix = pd.DataFrame(rows)
    matrix.to_csv(
        RESULTS / "ACC_signature_cohort_transport_matrix.csv",
        index=False,
    )

    independent = matrix[matrix["independent_test"]]
    summary = {
        "signature_cohort_pairs": int(len(matrix)),
        "independent_external_pairs": int(len(independent)),
        "independent_pairs_underpowered": int(
            independent["transportability_status"]
            .eq("indeterminate_underpowered")
            .sum()
        ),
        "provenance_grade_counts": matrix["provenance_grade"]
        .value_counts()
        .to_dict(),
        "independent_pair_status_counts": independent[
            "transportability_status"
        ]
        .value_counts()
        .to_dict(),
    }
    (RESULTS / "ACC_signature_cohort_transport_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    columns = [
        "signature",
        "cohort",
        "n",
        "events",
        "auc",
        "auc_ci_low",
        "auc_ci_high",
        "control_normalized_gap_ratio",
        "provenance_grade",
        "independent_test",
        "transportability_status",
    ]
    print(matrix[columns].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
