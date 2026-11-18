"""Formal evidence-capacity metrics for the ACC signature-cohort graph."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PAIRS = ROOT / "registry" / "ACC_Provenance_Pairs_v3.csv"
RESULTS = ROOT / "results"


def effective_clusters(counts: pd.Series) -> float:
    probabilities = counts.astype(float) / counts.sum()
    return float(1 / np.sum(probabilities**2))


def graph_components(
    edges: list[tuple[str, str]],
) -> list[list[str]]:
    parent = {}

    def find(node: str) -> str:
        parent.setdefault(node, node)
        if parent[node] != node:
            parent[node] = find(parent[node])
        return parent[node]

    def union(first: str, second: str) -> None:
        root_first = find(first)
        root_second = find(second)
        if root_first != root_second:
            parent[root_second] = root_first

    for signature, cluster in edges:
        union(f"S:{signature}", f"C:{cluster}")
    components = {}
    for node in parent:
        components.setdefault(find(node), []).append(node)
    return [
        sorted(nodes)
        for nodes in sorted(components.values(), key=lambda values: sorted(values))
    ]


def main() -> None:
    pairs = pd.read_csv(PAIRS)
    reported = pairs[
        pairs["pair_role"].eq("reported_validation")
        & ~pairs["design_independence_grade"].eq("U")
    ].copy()
    adult = reported[
        reported["reuse_cluster_id"].isin(
            [
                "GEO_ACC_U133_ASU_2010",
                "GEO_ACC_U133_MICHIGAN_2011",
                "GEO_ACC_ENSAT_2014",
            ]
        )
    ].copy()

    reported_counts = (
        reported.groupby("reuse_cluster_id")["signature_id"].nunique()
    )
    adult_counts = adult.groupby("reuse_cluster_id")["signature_id"].nunique()
    reported_effective = effective_clusters(reported_counts)
    adult_effective = effective_clusters(adult_counts)

    reported_edges = list(
        zip(
            reported["signature_id"].astype(str),
            reported["reuse_cluster_id"].astype(str),
        )
    )
    adult_edges = list(
        zip(
            adult["signature_id"].astype(str),
            adult["reuse_cluster_id"].astype(str),
        )
    )

    adult_expression = pairs[
        pairs["reuse_cluster_id"].isin(
            [
                "TCGA_ACC",
                "GEO_ACC_U133_ASU_2010",
                "GEO_ACC_U133_MICHIGAN_2011",
            ]
        )
        & pairs["pair_role"].isin(
            ["development", "reported_validation", "independent_pilot"]
        )
    ].copy()
    at_risk = adult_expression.drop_duplicates(
        ["reuse_cluster_id", "cohort", "survival_n", "events"]
    )
    event_capacity = at_risk.groupby("reuse_cluster_id")["events"].max()
    adult_expression_platforms = sorted(
        {
            platform
            for platform in adult["platform"].dropna().astype(str)
            if platform.startswith("GPL")
        }
    )
    reported_components = graph_components(reported_edges)
    adult_components = graph_components(adult_edges)

    metrics = {
        "verifiable_reported_validation_signatures": int(
            reported["signature_id"].nunique()
        ),
        "reported_cluster_counts": reported_counts.to_dict(),
        "reported_effective_cluster_number_herfindahl": reported_effective,
        "reported_graph_connected_components": len(reported_components),
        "reported_graph_components": reported_components,
        "adult_non_tcga_cluster_counts": adult_counts.to_dict(),
        "adult_non_tcga_effective_cluster_number_herfindahl": adult_effective,
        "adult_non_tcga_graph_connected_components": len(adult_components),
        "adult_non_tcga_graph_components": adult_components,
        "adult_expression_platform_count": len(adult_expression_platforms),
        "adult_expression_platforms": adult_expression_platforms,
        "total_adult_event_capacity_by_cluster": (
            event_capacity.to_dict()
        ),
        "total_adult_events_across_development_and_external": int(
            event_capacity.sum()
        ),
        "independent_only_events_max_available": (
            17 + 16
        ),
        "independent_only_events_note": (
            "For ssGSEA, the RATA-unseen adult cohorts contain 33 events "
            "(GSE33371=16, GSE19750=17); TCGA 28 events are development for ssGSEA "
            "and therefore excluded from independent-only capacity."
        ),
        "metric_note": (
            "Herfindahl effective cluster count is 1/sum(p_i^2); it measures "
            "concentration, not statistical precision."
        ),
    }

    reported_counts.rename("signature_count").to_csv(
        RESULTS / "RATA_v5_reported_cluster_counts.csv",
        header=True,
    )
    adult_counts.rename("signature_count").to_csv(
        RESULTS / "RATA_v5_adult_cluster_counts.csv",
        header=True,
    )
    (RESULTS / "RATA_v5_evidence_capacity_metrics.json").write_text(
        json.dumps(metrics, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
