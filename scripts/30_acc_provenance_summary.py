"""Summarize cohort reuse in the ACC signature registry."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "ACC_Signature_Registry_v2.csv"
RESULTS = ROOT / "results"


def split_sources(value: object) -> list[str]:
    if pd.isna(value):
        return []
    return [
        item.strip()
        for item in str(value).split(";")
        if item.strip() and item.strip().upper() not in {"NA", "NONE"}
    ]


def provenance_cluster(source: str) -> str:
    mapping = {
        "TCGA": "TCGA_ACC",
        "TCGA_training": "TCGA_ACC",
        "TCGA_testing": "TCGA_ACC",
        "TCGA_pan_cancer": "TCGA_pan_cancer",
        "TCGA_presumed": "TCGA_ACC",
        "GSE10927": "GEO_ACC_U133_MICHIGAN_2011",
        "GSE33371": "GEO_ACC_U133_MICHIGAN_2011",
        "GSE19750": "GEO_ACC_U133_ASU_2010",
        "GSE19776": "GEO_ACC_U133_ASU_2010",
        "GSE49278": "GEO_ACC_ENSAT_2014",
        "GSE49280": "GEO_ACC_ENSAT_2014",
    }
    return mapping.get(source, source)


def main() -> None:
    registry = pd.read_csv(REGISTRY)
    development_rows = []
    validation_rows = []

    for _, row in registry.iterrows():
        for source in split_sources(row["development_sources"]):
            development_rows.append(
                {
                    "signature_id": row["signature_id"],
                    "source": source,
                    "cluster": provenance_cluster(source),
                    "role": "development",
                }
            )
        for source in split_sources(row["external_expression_sources"]):
            if source.startswith(
                ("not_recovered", "invalid_", "untraceable_")
            ):
                continue
            validation_rows.append(
                {
                    "signature_id": row["signature_id"],
                    "source": source,
                    "cluster": provenance_cluster(source),
                    "role": "external_expression",
                }
            )

    development = pd.DataFrame(development_rows)
    validation = pd.DataFrame(validation_rows)

    development_counts = (
        development.groupby("source")
        .agg(
            signature_count=("signature_id", "nunique"),
            signatures=("signature_id", lambda values: ";".join(sorted(values))),
        )
        .reset_index()
        .sort_values(["signature_count", "source"], ascending=[False, True])
    )
    validation_counts = (
        validation.groupby("source")
        .agg(
            signature_count=("signature_id", "nunique"),
            signatures=("signature_id", lambda values: ";".join(sorted(values))),
        )
        .reset_index()
        .sort_values(["signature_count", "source"], ascending=[False, True])
    )
    development_cluster_counts = (
        development.groupby("cluster")
        .agg(
            signature_count=("signature_id", "nunique"),
            signatures=("signature_id", lambda values: ";".join(sorted(values))),
        )
        .reset_index()
        .sort_values(["signature_count", "cluster"], ascending=[False, True])
    )
    validation_cluster_counts = (
        validation.groupby("cluster")
        .agg(
            signature_count=("signature_id", "nunique"),
            signatures=("signature_id", lambda values: ";".join(sorted(values))),
        )
        .reset_index()
        .sort_values(["signature_count", "cluster"], ascending=[False, True])
    )

    claimed_external = registry[
        registry["external_sources"].notna()
        & ~registry["external_sources"].astype(str).str.upper().isin(
            ["NA", "NONE", "NAN"]
        )
        & ~registry["external_sources"].astype(str).str.startswith(
            ("not_recovered", "none")
        )
    ]
    verifiable_external = registry[
        registry["external_expression_sources"].map(
            lambda value: any(
                not source.startswith(
                    ("not_recovered", "invalid_", "untraceable_")
                )
                for source in split_sources(value)
            )
        )
    ]
    reused_sources = set(
        validation_counts.loc[
            validation_counts["signature_count"] > 1,
            "source",
        ]
    )
    reused_clusters = set(
        validation_cluster_counts.loc[
            validation_cluster_counts["signature_count"] > 1,
            "cluster",
        ]
    )
    reused_signature_ids = set(
        validation.loc[
            validation["source"].isin(reused_sources)
            | validation["cluster"].isin(reused_clusters),
            "signature_id",
        ]
    )
    reuse_fraction = (
        len(reused_signature_ids) / len(verifiable_external)
        if len(verifiable_external)
        else float("nan")
    )

    summary = {
        "registry_signatures": int(len(registry)),
        "scoreable_rna_signatures": int(
            registry["scoreable_in_rna_pilot"].astype(str).str.lower().eq("yes").sum()
        ),
        "signatures_claiming_external_expression_validation": int(
            len(claimed_external)
        ),
        "signatures_with_verifiable_external_expression_source": int(
            len(verifiable_external)
        ),
        "invalid_or_untraceable_external_claims": int(
            len(claimed_external) - len(verifiable_external)
        ),
        "signatures_using_at_least_one_cross_study_reused_external_source": int(
            len(reused_signature_ids)
        ),
        "cross_study_reuse_fraction": float(reuse_fraction),
        "provenance_grade_counts": registry["provenance_grade"]
        .value_counts()
        .to_dict(),
        "development_source_counts": development_counts.to_dict(orient="records"),
        "external_source_counts": validation_counts.to_dict(orient="records"),
        "development_cluster_counts": development_cluster_counts.to_dict(
            orient="records"
        ),
        "external_cluster_counts": validation_cluster_counts.to_dict(
            orient="records"
        ),
        "reused_external_sources": sorted(reused_sources),
        "reused_external_clusters": sorted(reused_clusters),
    }

    development_counts.to_csv(
        RESULTS / "ACC_provenance_development_source_counts.csv",
        index=False,
    )
    validation_counts.to_csv(
        RESULTS / "ACC_provenance_external_source_counts.csv",
        index=False,
    )
    development_cluster_counts.to_csv(
        RESULTS / "ACC_provenance_development_cluster_counts.csv",
        index=False,
    )
    validation_cluster_counts.to_csv(
        RESULTS / "ACC_provenance_external_cluster_counts.csv",
        index=False,
    )
    (RESULTS / "ACC_provenance_summary.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
