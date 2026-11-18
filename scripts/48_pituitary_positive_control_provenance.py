"""Provenance and negative-control audit for the pituitary positive control."""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
OFFICIAL_SAMPLES = ROOT / "registry" / "samples" / "GSE147786-official-samples-20261110.csv"
SIGNATURE_GENES = RESULTS / "RATA_v5_pituitary_lineage_signature_genes.csv"
EXTERNAL_GENES = RESULTS / "RATA_v5_GSE147786_gene_space.csv"
EXTERNAL_SCORES = (
    ROOT.parent
    / "pituitary-project"
    / "results"
    / "GSE147786-lineage-signature-scores.csv"
)
RANDOM_SEED = 20261110


def permutation_p(
    score: np.ndarray,
    binary_label: np.ndarray,
    observed_auc: float,
    repeats: int = 10000,
) -> float:
    rng = np.random.default_rng(RANDOM_SEED)
    extreme = 0
    for _ in range(repeats):
        shuffled = rng.permutation(binary_label)
        auc = roc_auc_score(shuffled, score)
        if max(auc, 1 - auc) >= max(observed_auc, 1 - observed_auc):
            extreme += 1
    return float((1 + extreme) / (repeats + 1))


def main() -> None:
    official = pd.read_csv(OFFICIAL_SAMPLES)
    tumor_mask = (
        official["title"].astype(str).str.contains(
            "Adenomas",
            case=False,
            na=False,
        )
        | official["title"].astype(str).str.startswith("CNFPA")
    )
    tumor = official[
        tumor_mask
    ].copy()
    tumor["group"] = np.where(
        tumor["title"].astype(str).str.startswith("GH"),
        "GH",
        np.where(
            tumor["title"].astype(str).str.startswith("CNFPA"),
            "NFPA",
            "Other_lineage",
        ),
    )
    group_counts = tumor["group"].value_counts().to_dict()

    signature = pd.read_csv(SIGNATURE_GENES)
    external_space = set(pd.read_csv(EXTERNAL_GENES)["gene"])
    overlap = sorted(
        set(signature["gene"]).intersection(external_space)
    )
    scores = pd.read_csv(EXTERNAL_SCORES)
    scores = scores[scores["lineage"].isin(["GH", "NFPA"])].copy()
    binary = scores["lineage"].map({"GH": 1, "NFPA": 0}).to_numpy()
    observed_auc = float(roc_auc_score(binary, scores["score"]))
    permutation = permutation_p(
        scores["score"].to_numpy(),
        binary,
        observed_auc,
    )

    top_positive = (
        signature[signature["direction"].eq("positive")]
        .sort_values("discovery_logFC", ascending=False)
        .head(10)["gene"]
        .tolist()
    )
    top_negative = (
        signature[signature["direction"].eq("negative")]
        .sort_values("discovery_logFC", ascending=True)
        .head(10)["gene"]
        .tolist()
    )
    marker_panel = [
        "GH1",
        "PRL",
        "POU1F1",
        "NR5A1",
        "TBX19",
        "DLK1",
        "SLIT1",
        "CACNA2D4",
        "EPHA4",
    ]
    marker_presence = {
        marker: marker in set(signature["gene"])
        for marker in marker_panel
    }

    official_tissue_counts = official["characteristics"].value_counts().to_dict()
    payload = {
        "series_accession": "GSE147786",
        "platform": "GPL23126",
        "official_series_title": "Transcriptome and methylome analysis reveal three cellular origins of pituitary tumors",
        "total_samples": int(len(official)),
        "official_tissue_counts": official_tissue_counts,
        "tumor_group_counts": {
            "GH": int(group_counts.get("GH", 0)),
            "NFPA": int(group_counts.get("NFPA", 0)),
            "Other_lineage_tumors": int(group_counts.get("Other_lineage", 0)),
        },
        "external_score_n": int(len(scores)),
        "external_auc": observed_auc,
        "external_auc_ci_note": (
            "AUC is 1.0 with no discordant pair; a numeric bootstrap CI is "
            "degenerate at the boundary."
        ),
        "label_permutation_p": permutation,
        "exact_perfect_separation_p": (
            1 / math.comb(len(scores), int((scores["lineage"] == "GH").sum()))
            if observed_auc == 1.0
            else float("nan")
        ),
        "signature_genes": int(len(signature)),
        "external_gene_space": int(len(external_space)),
        "signature_genes_present_external": int(len(overlap)),
        "signature_gene_coverage": float(len(overlap) / len(signature)),
        "missing_signature_genes": sorted(
            set(signature["gene"]) - external_space
        ),
        "top_positive_genes": top_positive,
        "top_negative_genes": top_negative,
        "known_marker_presence_in_signature": marker_presence,
        "negative_control_notes": {
            "sex": "not available in external metadata",
            "age": "not available in external metadata",
            "batch": "single platform GPL23126; explicit batch variable unavailable",
            "label_permutation": (
                "10,000 label permutations; p-value tests whether AUC 1.0 "
                "is compatible with random phenotype labels."
            ),
        },
    }
    (RESULTS / "RATA_v5_pituitary_positive_control_provenance.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    pd.DataFrame(
        [
            {
                "series_accession": payload["series_accession"],
                "platform": payload["platform"],
                "GH_n": payload["tumor_group_counts"]["GH"],
                "NFPA_n": payload["tumor_group_counts"]["NFPA"],
                "other_tumor_n": payload["tumor_group_counts"]["Other_lineage_tumors"],
                "external_auc": observed_auc,
                "permutation_p": permutation,
                "signature_gene_coverage": payload["signature_gene_coverage"],
            }
        ]
    ).to_csv(
        RESULTS / "RATA_v5_pituitary_positive_control_provenance.csv",
        index=False,
    )
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
