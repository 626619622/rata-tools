"""RATA v3: pair-level provenance, difference-in-differences, stratified Cox."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import warnings

import numpy as np
import pandas as pd
from scipy.stats import chi2
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler
from statsmodels.duration.hazard_regression import PHReg


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
RANDOM_SEED = 20261109
N_BOOTSTRAP = 2000


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
    "acc_multicohort",
)

CLUSTERS = {
    "TCGA": "TCGA_ACC",
    "GSE33371": "GEO_ACC_U133_MICHIGAN_2011",
    "GSE19750": "GEO_ACC_U133_ASU_2010",
}

EXPRESSION_N = {
    "TCGA": 79,
    "GSE33371": 33,
    "GSE19750": 44,
}

REFERENCE_COHORTS = {
    signature: ("TCGA",)
    for signature in audit.SIGNATURES
}
REFERENCE_COHORTS["prognostic_3gene_2021"] = ("GSE33371", "GSE19750")
REFERENCE_DISPLAY = {
    "GSE33371": "GSE10927",
}

INDEPENDENT_PAIRS = {
    "hypoxia_3gene_2021": ["GSE33371"],
    "immune_irg_3gene_2022": [],
    "prognostic_3gene_2021": ["TCGA"],
    "immune_ssgsea_13gene_2022": ["GSE33371", "GSE19750"],
    "metabolic_5gene_2021": ["GSE33371"],
    "atf_creb_7gene_2025": ["GSE19750"],
}

PAIR_GRADES = {
    "hypoxia_3gene_2021": {
        "TCGA": ("D", "TCGA development cohort."),
        "GSE33371": ("A", "Independent adult validation candidate."),
        "GSE19750": ("C", "Used as reported validation."),
    },
    "immune_irg_3gene_2022": {
        "TCGA": ("D", "TCGA training/testing data."),
        "GSE33371": ("C", "Same arrays as GSE10927 validation."),
        "GSE19750": ("C", "Used as reported validation."),
    },
    "prognostic_3gene_2021": {
        "TCGA": ("A", "Independent external validation cohort."),
        "GSE33371": ("C", "Same arrays as GSE10927 development."),
        "GSE19750": ("D", "Development cohort."),
    },
    "immune_ssgsea_13gene_2022": {
        "TCGA": ("D", "TCGA development cohort."),
        "GSE33371": ("A", "Independent adult validation candidate."),
        "GSE19750": ("A", "Independent adult validation candidate."),
    },
    "metabolic_5gene_2021": {
        "TCGA": ("D", "TCGA development cohort."),
        "GSE33371": ("A", "Independent adult validation candidate."),
        "GSE19750": ("C", "Used as reported validation."),
    },
    "atf_creb_7gene_2025": {
        "TCGA": ("D", "TCGA development cohort."),
        "GSE33371": ("C", "Same arrays as GSE10927 validation."),
        "GSE19750": ("A", "Independent adult validation candidate."),
    },
}


def event_status_auc(score: pd.Series, event: pd.Series) -> float:
    return float(roc_auc_score(event, score))


def harrell_c_index_fast(
    score: np.ndarray,
    time: np.ndarray,
    event: np.ndarray,
) -> float:
    score = np.asarray(score, dtype=float)
    time = np.asarray(time, dtype=float)
    event = np.asarray(event, dtype=int)
    time_i = time[:, None]
    time_j = time[None, :]
    event_i = event[:, None]
    score_i = score[:, None]
    score_j = score[None, :]
    comparable_i = (time_i < time_j) & (event_i == 1)
    comparable_j = (time_j < time_i) & (event[None, :] == 1)
    concordant_i = score_i > score_j
    concordant_j = score_j > score_i
    ties = score_i == score_j
    concordant = (
        np.sum(comparable_i & concordant_i)
        + np.sum(comparable_j & concordant_j)
        + 0.5 * np.sum((comparable_i | comparable_j) & ties)
    )
    comparable_count = np.sum(comparable_i | comparable_j)
    return float(concordant / comparable_count) if comparable_count else float("nan")


def cindex(
    score: pd.Series,
    outcomes: pd.DataFrame,
) -> float:
    return harrell_c_index_fast(
        score.to_numpy(dtype=float),
        outcomes["time"].to_numpy(dtype=float),
        outcomes["event"].to_numpy(dtype=int),
    )


def weighted_cohort_event_auc(
    cohorts: tuple[str, ...],
    score_by_cohort: dict[str, pd.Series],
    outcomes_by_cohort: dict[str, pd.DataFrame],
) -> float:
    values = []
    weights = []
    for cohort in cohorts:
        values.append(
            event_status_auc(
                score_by_cohort[cohort],
                outcomes_by_cohort[cohort]["os_event"],
            )
        )
        weights.append(len(score_by_cohort[cohort]))
    return float(np.average(values, weights=weights))


def weighted_cohort_cindex(
    cohorts: tuple[str, ...],
    score_by_cohort: dict[str, pd.Series],
    outcomes_by_cohort: dict[str, pd.DataFrame],
) -> float:
    values = []
    weights = []
    for cohort in cohorts:
        values.append(cindex(score_by_cohort[cohort], outcomes_by_cohort[cohort]))
        weights.append(len(score_by_cohort[cohort]))
    return float(np.average(values, weights=weights))


def difference_in_differences(
    reference_cohorts: tuple[str, ...],
    external_cohort: str,
    signature_scores: dict[str, pd.Series],
    control_scores: dict[str, pd.Series],
    outcomes: dict[str, pd.DataFrame],
    seed: int,
) -> dict:
    sig_reference_auc = weighted_cohort_event_auc(
        reference_cohorts,
        signature_scores,
        outcomes,
    )
    ctrl_reference_auc = weighted_cohort_event_auc(
        reference_cohorts,
        control_scores,
        outcomes,
    )
    sig_external_auc = event_status_auc(
        signature_scores[external_cohort],
        outcomes[external_cohort]["os_event"],
    )
    ctrl_external_auc = event_status_auc(
        control_scores[external_cohort],
        outcomes[external_cohort]["os_event"],
    )

    sig_reference_c = weighted_cohort_cindex(
        reference_cohorts,
        signature_scores,
        outcomes,
    )
    ctrl_reference_c = weighted_cohort_cindex(
        reference_cohorts,
        control_scores,
        outcomes,
    )
    sig_external_c = cindex(
        signature_scores[external_cohort],
        outcomes[external_cohort],
    )
    ctrl_external_c = cindex(
        control_scores[external_cohort],
        outcomes[external_cohort],
    )
    sig_gap_auc = sig_reference_auc - sig_external_auc
    control_gap_auc = ctrl_reference_auc - ctrl_external_auc
    did_auc = sig_gap_auc - control_gap_auc
    sig_gap_c = sig_reference_c - sig_external_c
    control_gap_c = ctrl_reference_c - ctrl_external_c
    did_c = sig_gap_c - control_gap_c

    rng = np.random.default_rng(seed)
    bootstrap_auc_values = []
    bootstrap_c_values = []
    for _ in range(N_BOOTSTRAP):
        reference_sig_auc = []
        reference_ctrl_auc = []
        reference_sig_c = []
        reference_ctrl_c = []
        reference_weights = []
        valid = True
        for cohort in reference_cohorts:
            event = outcomes[cohort]["os_event"].to_numpy()
            indices = rng.integers(0, len(event), len(event))
            if np.unique(event[indices]).size < 2:
                valid = False
                break
            sampled_time = outcomes[cohort]["time"].to_numpy()[indices]
            reference_sig_auc.append(
                roc_auc_score(
                    event[indices],
                    signature_scores[cohort].to_numpy()[indices],
                )
            )
            reference_ctrl_auc.append(
                roc_auc_score(
                    event[indices],
                    control_scores[cohort].to_numpy()[indices],
                )
            )
            reference_sig_c.append(
                harrell_c_index_fast(
                    signature_scores[cohort].to_numpy()[indices],
                    sampled_time,
                    event[indices],
                )
            )
            reference_ctrl_c.append(
                harrell_c_index_fast(
                    control_scores[cohort].to_numpy()[indices],
                    sampled_time,
                    event[indices],
                )
            )
            reference_weights.append(len(event))
        if not valid:
            continue

        ext_event = outcomes[external_cohort]["os_event"].to_numpy()
        ext_time = outcomes[external_cohort]["time"].to_numpy()
        ext_indices = rng.integers(0, len(ext_event), len(ext_event))
        if np.unique(ext_event[ext_indices]).size < 2:
            continue
        bootstrap_sig_ref_auc = np.average(
            reference_sig_auc,
            weights=reference_weights,
        )
        bootstrap_ctrl_ref_auc = np.average(
            reference_ctrl_auc,
            weights=reference_weights,
        )
        bootstrap_sig_ext_auc = roc_auc_score(
            ext_event[ext_indices],
            signature_scores[external_cohort].to_numpy()[ext_indices],
        )
        bootstrap_ctrl_ext_auc = roc_auc_score(
            ext_event[ext_indices],
            control_scores[external_cohort].to_numpy()[ext_indices],
        )
        bootstrap_auc_values.append(
            (bootstrap_sig_ref_auc - bootstrap_sig_ext_auc)
            - (bootstrap_ctrl_ref_auc - bootstrap_ctrl_ext_auc)
        )

        bootstrap_sig_ref_c = np.average(
            reference_sig_c,
            weights=reference_weights,
        )
        bootstrap_ctrl_ref_c = np.average(
            reference_ctrl_c,
            weights=reference_weights,
        )
        bootstrap_sig_ext_c = harrell_c_index_fast(
            signature_scores[external_cohort].to_numpy()[ext_indices],
            ext_time[ext_indices],
            ext_event[ext_indices],
        )
        bootstrap_ctrl_ext_c = harrell_c_index_fast(
            control_scores[external_cohort].to_numpy()[ext_indices],
            ext_time[ext_indices],
            ext_event[ext_indices],
        )
        bootstrap_c_values.append(
            (bootstrap_sig_ref_c - bootstrap_sig_ext_c)
            - (bootstrap_ctrl_ref_c - bootstrap_ctrl_ext_c)
        )

    return {
        "signature_reference_event_auc": sig_reference_auc,
        "control_reference_event_auc": ctrl_reference_auc,
        "signature_external_event_auc": sig_external_auc,
        "control_external_event_auc": ctrl_external_auc,
        "signature_event_auc_gap": sig_gap_auc,
        "control_event_auc_gap": control_gap_auc,
        "event_auc_did": did_auc,
        "event_auc_did_ci_low": float(np.quantile(bootstrap_auc_values, 0.025)),
        "event_auc_did_ci_high": float(np.quantile(bootstrap_auc_values, 0.975)),
        "signature_reference_cindex": sig_reference_c,
        "control_reference_cindex": ctrl_reference_c,
        "signature_external_cindex": sig_external_c,
        "control_external_cindex": ctrl_external_c,
        "signature_cindex_gap": sig_gap_c,
        "control_cindex_gap": control_gap_c,
        "cindex_did": did_c,
        "cindex_did_ci_low": float(np.quantile(bootstrap_c_values, 0.025)),
        "cindex_did_ci_high": float(np.quantile(bootstrap_c_values, 0.975)),
        "bootstrap_valid_fraction": min(
            len(bootstrap_auc_values),
            len(bootstrap_c_values),
        )
        / N_BOOTSTRAP,
    }


def fit_cox(
    frame: pd.DataFrame,
    stratified: bool,
) -> tuple[float, float, float, float]:
    formula_exog = frame[["score_z"]].to_numpy(dtype=float)
    model = PHReg(
        frame["time"].to_numpy(dtype=float),
        formula_exog,
        status=frame["event"].to_numpy(dtype=int),
        strata=frame["cohort_id"].to_numpy(dtype=int) if stratified else None,
        ties="efron",
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = model.fit(disp=False)
    beta = float(result.params[0])
    se = float(result.bse[0])
    p_value = float(result.pvalues[0])
    return beta, se, p_value, float(np.exp(beta))


def meta_analysis(cox_rows: pd.DataFrame) -> dict:
    if len(cox_rows) < 2:
        return {
            "meta_beta": float("nan"),
            "meta_hr": float("nan"),
            "meta_ci_low": float("nan"),
            "meta_ci_high": float("nan"),
            "q": float("nan"),
            "q_df": 0,
            "q_p": float("nan"),
            "i2": float("nan"),
        }
    beta = cox_rows["beta"].to_numpy(dtype=float)
    se = cox_rows["se"].to_numpy(dtype=float)
    weights = 1 / np.maximum(se**2, 1e-12)
    meta_beta = float(np.sum(weights * beta) / np.sum(weights))
    meta_se = float(np.sqrt(1 / np.sum(weights)))
    q = float(np.sum(weights * (beta - meta_beta) ** 2))
    q_df = len(beta) - 1
    i2 = float(max(0.0, (q - q_df) / max(q, 1e-12)) * 100)
    return {
        "meta_beta": meta_beta,
        "meta_hr": float(np.exp(meta_beta)),
        "meta_ci_low": float(np.exp(meta_beta - 1.96 * meta_se)),
        "meta_ci_high": float(np.exp(meta_beta + 1.96 * meta_se)),
        "q": q,
        "q_df": q_df,
        "q_p": float(chi2.sf(q, q_df)) if q_df > 0 else float("nan"),
        "i2": i2,
    }


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
        "TCGA": tcga_outcomes.assign(
            time=tcga_outcomes["os_months"],
            event=tcga_outcomes["os_event"],
        ),
        "GSE33371": geo33371_samples.assign(
            time=geo33371_samples["os_years"],
            event=geo33371_samples["os_event"],
        ),
        "GSE19750": gse19750_samples.assign(
            time=gse19750_samples["os_years"],
            event=gse19750_samples["os_event"],
        ),
    }

    control_definition = {
        "genes": base.PROGRAMS["proliferation"],
        "weights": [1.0] * len(base.PROGRAMS["proliferation"]),
    }
    control_scores = {
        cohort: base.score_signature(
            expressions[cohort],
            control_definition["genes"],
            control_definition["weights"],
        )[0]
        for cohort in expressions
    }

    pair_rows = []
    cox_rows_all = []
    cox_rows_independent = []

    for signature_index, (signature, definition) in enumerate(
        audit.SIGNATURES.items()
    ):
        signature_scores = {
            cohort: base.score_signature(
                expressions[cohort],
                definition["genes"],
                definition["weights"],
            )[0]
            for cohort in expressions
        }
        reference_cohorts = REFERENCE_COHORTS[signature]
        reference_label = ";".join(
            REFERENCE_DISPLAY.get(cohort, cohort)
            for cohort in reference_cohorts
        )

        for cohort in INDEPENDENT_PAIRS[signature]:
            did = difference_in_differences(
                reference_cohorts,
                cohort,
                signature_scores,
                control_scores,
                outcomes,
                seed=RANDOM_SEED + signature_index * 10 + list(expressions).index(cohort),
            )
            external_n = len(signature_scores[cohort])
            external_events = int(outcomes[cohort]["event"].sum())
            if external_n < 50 or external_events < 20:
                status = "inconclusive_underpowered"
            elif did["cindex_did_ci_low"] > 0:
                status = "more_fragile_than_positive_control"
            elif did["cindex_did_ci_high"] < 0:
                status = "more_stable_than_positive_control"
            else:
                status = "inconclusive_cindex_did_ci_crosses_zero"
            pair_rows.append(
                {
                    "signature": signature,
                    "source_pmid": definition["source_pmid"],
                    "reference_cohorts": reference_label,
                    "reference_data_accessions": ";".join(reference_cohorts),
                    "external_cohort": cohort,
                    "reuse_cluster_id": CLUSTERS[cohort],
                    "provenance_grade": "A",
                    "expression_n": EXPRESSION_N[cohort],
                    "survival_n": external_n,
                    "events": external_events,
                    **did,
                    "did_status": status,
                }
            )

        # Descriptive all-available stratified Cox. Cohort remains a stratum and
        # expression scores are standardized within cohort.
        cox_input = []
        for cohort, (score, frame) in zip(
            expressions,
            [(signature_scores[c], outcomes[c]) for c in expressions],
        ):
            cox_input.append(
                pd.DataFrame(
                    {
                        "cohort": cohort,
                        "score_z": StandardScaler().fit_transform(
                            score.to_numpy().reshape(-1, 1)
                        ).ravel(),
                        "time": frame["time"].to_numpy(dtype=float),
                        "event": frame["event"].to_numpy(dtype=int),
                    }
                )
            )
        all_frame = pd.concat(cox_input, ignore_index=True)
        all_frame["cohort_id"] = pd.Categorical(
            all_frame["cohort"],
            categories=list(expressions),
        ).codes
        common_beta, common_se, common_p, common_hr = fit_cox(
            all_frame,
            stratified=True,
        )
        per_cohort = []
        for cohort in expressions:
            cohort_frame = all_frame[all_frame["cohort"].eq(cohort)].copy()
            beta, se, p_value, hr = fit_cox(cohort_frame, stratified=False)
            per_cohort.append(
                {
                    "signature": signature,
                    "analysis": "all_available",
                    "cohort": cohort,
                    "n": len(cohort_frame),
                    "events": int(cohort_frame["event"].sum()),
                    "beta": beta,
                    "se": se,
                    "p_value": p_value,
                    "hr": hr,
                }
            )
        cox_rows_all.extend(per_cohort)
        per_cohort_frame = pd.DataFrame(per_cohort)
        meta = meta_analysis(per_cohort_frame)
        pair_rows.append(
            {
                "signature": signature,
                "source_pmid": definition["source_pmid"],
                "reference_cohorts": "none",
                "external_cohort": "ALL_AVAILABLE_STRATIFIED_COX",
                "reuse_cluster_id": "multiple",
                "provenance_grade": "mixed",
                "expression_n": int(len(all_frame)),
                "survival_n": int(len(all_frame)),
                "events": int(all_frame["event"].sum()),
                "signature_reference_event_auc": float("nan"),
                "control_reference_event_auc": float("nan"),
                "signature_external_event_auc": float("nan"),
                "control_external_event_auc": float("nan"),
                "signature_event_auc_gap": float("nan"),
                "control_event_auc_gap": float("nan"),
                "event_auc_did": float("nan"),
                "event_auc_did_ci_low": float("nan"),
                "event_auc_did_ci_high": float("nan"),
                "signature_reference_cindex": float("nan"),
                "control_reference_cindex": float("nan"),
                "signature_external_cindex": float("nan"),
                "control_external_cindex": float("nan"),
                "signature_cindex_gap": float("nan"),
                "control_cindex_gap": float("nan"),
                "cindex_did": float("nan"),
                "cindex_did_ci_low": float("nan"),
                "cindex_did_ci_high": float("nan"),
                "bootstrap_valid_fraction": float("nan"),
                "common_cox_beta": common_beta,
                "common_cox_se": common_se,
                "common_cox_p": common_p,
                "common_cox_hr": common_hr,
                "common_cox_ci_low": float(np.exp(common_beta - 1.96 * common_se)),
                "common_cox_ci_high": float(np.exp(common_beta + 1.96 * common_se)),
                **meta,
                "did_status": "descriptive_stratified_cox",
            }
        )

        independent_cohorts = INDEPENDENT_PAIRS[signature]
        if len(independent_cohorts) >= 2:
            independent_frame = all_frame[
                all_frame["cohort"].isin(independent_cohorts)
            ].copy()
            independent_frame["cohort_id"] = pd.Categorical(
                independent_frame["cohort"],
                categories=independent_cohorts,
            ).codes
            common_beta, common_se, common_p, common_hr = fit_cox(
                independent_frame,
                stratified=True,
            )
            per_cohort = []
            for cohort in independent_cohorts:
                cohort_frame = independent_frame[
                    independent_frame["cohort"].eq(cohort)
                ].copy()
                beta, se, p_value, hr = fit_cox(
                    cohort_frame,
                    stratified=False,
                )
                per_cohort.append(
                    {
                        "signature": signature,
                        "analysis": "independent_only",
                        "cohort": cohort,
                        "n": len(cohort_frame),
                        "events": int(cohort_frame["event"].sum()),
                        "beta": beta,
                        "se": se,
                        "p_value": p_value,
                        "hr": hr,
                    }
                )
            cox_rows_independent.extend(per_cohort)
            meta = meta_analysis(pd.DataFrame(per_cohort))
            pair_rows.append(
                {
                    "signature": signature,
                    "source_pmid": definition["source_pmid"],
                    "reference_cohorts": "none",
                    "external_cohort": "INDEPENDENT_ONLY_STRATIFIED_COX",
                    "reuse_cluster_id": ";".join(
                        CLUSTERS[c] for c in independent_cohorts
                    ),
                    "provenance_grade": "A",
                    "expression_n": int(len(independent_frame)),
                    "survival_n": int(len(independent_frame)),
                    "events": int(independent_frame["event"].sum()),
                    "signature_reference_event_auc": float("nan"),
                    "control_reference_event_auc": float("nan"),
                    "signature_external_event_auc": float("nan"),
                    "control_external_event_auc": float("nan"),
                    "signature_event_auc_gap": float("nan"),
                    "control_event_auc_gap": float("nan"),
                    "event_auc_did": float("nan"),
                    "event_auc_did_ci_low": float("nan"),
                    "event_auc_did_ci_high": float("nan"),
                    "signature_reference_cindex": float("nan"),
                    "control_reference_cindex": float("nan"),
                    "signature_external_cindex": float("nan"),
                    "control_external_cindex": float("nan"),
                    "signature_cindex_gap": float("nan"),
                    "control_cindex_gap": float("nan"),
                    "cindex_did": float("nan"),
                    "cindex_did_ci_low": float("nan"),
                    "cindex_did_ci_high": float("nan"),
                    "bootstrap_valid_fraction": float("nan"),
                    "common_cox_beta": common_beta,
                    "common_cox_se": common_se,
                    "common_cox_p": common_p,
                    "common_cox_hr": common_hr,
                    "common_cox_ci_low": float(np.exp(common_beta - 1.96 * common_se)),
                    "common_cox_ci_high": float(np.exp(common_beta + 1.96 * common_se)),
                    **meta,
                    "did_status": "independent_stratified_cox",
                }
            )

    pair_table = pd.DataFrame(pair_rows)
    pair_table.to_csv(
        RESULTS / "RATA_v3_pair_registry_and_transport.csv",
        index=False,
    )
    pd.DataFrame(cox_rows_all + cox_rows_independent).to_csv(
        RESULTS / "RATA_v3_per_cohort_cox.csv",
        index=False,
    )

    did_rows = pair_table[
        pair_table["external_cohort"].isin(["TCGA", "GSE33371", "GSE19750"])
    ]
    cox_summary = pair_table[
        pair_table["external_cohort"].str.contains("COX", na=False)
    ]
    summary = {
        "did_pairs": int(len(did_rows)),
        "did_underpowered": int(
            did_rows["did_status"].eq("inconclusive_underpowered").sum()
        ),
        "stratified_cox_models": int(len(cox_summary)),
        "signatures_with_independent_only_cox": int(
            cox_summary["external_cohort"]
            .eq("INDEPENDENT_ONLY_STRATIFIED_COX")
            .sum()
        ),
    }
    (RESULTS / "RATA_v3_transport_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    columns = [
        "signature",
        "reference_cohorts",
        "external_cohort",
        "survival_n",
        "events",
        "signature_reference_cindex",
        "signature_external_cindex",
        "cindex_did",
        "cindex_did_ci_low",
        "cindex_did_ci_high",
        "did_status",
        "common_cox_hr",
        "common_cox_ci_low",
        "common_cox_ci_high",
        "i2",
    ]
    print(pair_table[columns].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
