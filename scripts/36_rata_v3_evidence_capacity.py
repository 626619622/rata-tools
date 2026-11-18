"""Compute the evidence-capacity headline for the ACC RATA registry."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "ACC_Provenance_Pairs_v3.csv"
RESULTS = ROOT / "results"


def main() -> None:
    pairs = pd.read_csv(REGISTRY)
    development = pairs[pairs["pair_role"].eq("development")]
    reported = pairs[pairs["pair_role"].eq("reported_validation")]
    pilot = pairs[pairs["pair_role"].eq("independent_pilot")]

    non_tcga_adult_clusters = sorted(
        {
            cluster
            for cluster in pairs["reuse_cluster_id"].dropna().unique()
            if cluster
            in {
                "GEO_ACC_U133_ASU_2010",
                "GEO_ACC_U133_MICHIGAN_2011",
                "GEO_ACC_ENSAT_2014",
            }
        }
    )
    adult_cluster_rows = pairs[
        pairs["reuse_cluster_id"].isin(non_tcga_adult_clusters)
    ]
    adult_platform_map = (
        adult_cluster_rows.groupby("reuse_cluster_id")["platform"]
        .agg(lambda values: ";".join(sorted(set(values.dropna().astype(str)))))
        .to_dict()
    )
    adult_platforms = sorted(
        {
            platform
            for value in adult_platform_map.values()
            for platform in value.split(";")
            if platform
        }
    )
    adult_expression_platforms = [
        platform for platform in adult_platforms if platform.startswith("GPL")
    ]
    tcga_developed = development[
        development["reuse_cluster_id"].eq("TCGA_ACC")
    ]["signature_id"].nunique()
    tcga_presumed_ids = set(
        development[
            development["reuse_cluster_id"].eq("TCGA_ACC_PRESUMED")
        ]["signature_id"]
    )
    tcga_confirmed_ids = set(
        development[
            development["reuse_cluster_id"].eq("TCGA_ACC")
        ]["signature_id"]
    )
    tcga_total_with_presumed = len(
        tcga_confirmed_ids.union(tcga_presumed_ids)
    )
    reported_verifiable = reported[
        ~reported["design_independence_grade"].isin(["U"])
    ]["signature_id"].nunique()
    reported_invalid = reported[
        reported["design_independence_grade"].eq("U")
    ]["signature_id"].nunique()
    reported_cluster_counts = (
        reported[
            ~reported["design_independence_grade"].eq("U")
        ]
        .groupby("reuse_cluster_id")
        .agg(
            signature_count=("signature_id", "nunique"),
            signatures=("signature_id", lambda values: ";".join(sorted(values))),
        )
        .reset_index()
        .sort_values(["signature_count", "reuse_cluster_id"], ascending=[False, True])
    )
    pilot_counts = (
        pilot.groupby("reuse_cluster_id")
        .agg(
            pair_count=("signature_id", "size"),
            signatures=("signature_id", lambda values: ";".join(sorted(values))),
        )
        .reset_index()
        .sort_values(["pair_count", "reuse_cluster_id"], ascending=[False, True])
    )

    summary = {
        "registry_signatures": int(pairs["signature_id"].nunique()),
        "tcga_developed_signatures_confirmed": int(tcga_developed),
        "tcga_developed_or_presumed_signatures": int(tcga_total_with_presumed),
        "tcga_presumed_signatures": int(len(tcga_presumed_ids)),
        "verifiable_reported_validation_signatures": int(reported_verifiable),
        "invalid_or_untraceable_reported_validation_signatures": int(
            reported_invalid
        ),
        "adult_non_tcga_expression_clusters": non_tcga_adult_clusters,
        "adult_non_tcga_cluster_count": len(non_tcga_adult_clusters),
        "adult_non_tcga_platforms": adult_platforms,
        "adult_non_tcga_expression_platforms": adult_expression_platforms,
        "adult_non_tcga_cluster_platform_map": adult_platform_map,
        "reported_validation_cluster_counts": reported_cluster_counts.to_dict(
            orient="records"
        ),
        "independent_pilot_pair_counts": pilot_counts.to_dict(orient="records"),
        "headline": (
            "ACC evidence capacity: nine signatures were TCGA-developed; "
            "verifiable reported expression validation is concentrated in "
            "three adult non-TCGA microarray cohort clusters spanning GPL570 "
            "and GPL16686, plus TCGA for one signature."
        ),
    }
    reported_cluster_counts.to_csv(
        RESULTS / "RATA_v3_reported_validation_clusters.csv",
        index=False,
    )
    pilot_counts.to_csv(
        RESULTS / "RATA_v3_independent_pilot_pair_counts.csv",
        index=False,
    )
    (RESULTS / "RATA_v3_evidence_capacity.json").write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
