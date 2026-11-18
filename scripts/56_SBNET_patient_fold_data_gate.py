"""Patient/lesion folding data gate for the SBNET third-disease pilot."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "registry" / "samples"
RESULTS = ROOT / "results"


def infer_lesion(source: str) -> str:
    source = str(source).lower()
    if "primary" in source:
        return "primary"
    if "metast" in source:
        return "metastasis"
    return "other"


def main() -> None:
    gse27162 = pd.read_csv(SAMPLES / "GSE27162-samples.csv")
    gse27162["lesion"] = gse27162["source"].map(infer_lesion)
    gse27162["patient_id"] = gse27162["title"].str.extract(r"(\d+)")[0]
    lesions = gse27162[gse27162["lesion"].isin(["primary", "metastasis"])].copy()

    patient_rows = []
    for patient_id, frame in lesions.groupby("patient_id"):
        patient_rows.append(
            {
                "cohort": "GSE27162",
                "patient_id": patient_id,
                "has_primary": int(frame["lesion"].eq("primary").any()),
                "has_metastasis": int(frame["lesion"].eq("metastasis").any()),
                "metastasis_patient_label": int(
                    frame["lesion"].eq("metastasis").any()
                ),
                "lesion_count": len(frame),
            }
        )
    patient_table = pd.DataFrame(patient_rows)
    patient_table.to_csv(
        RESULTS / "RATA_v5_SBNET_GSE27162_patient_fold.csv",
        index=False,
    )

    gse9576 = pd.read_csv(SAMPLES / "GSE9576-samples.csv")
    gse9576["lesion"] = gse9576["source"].map(infer_lesion)
    tumor_9576 = gse9576[gse9576["lesion"].isin(["primary", "metastasis"])]

    gse27162_summary = {
        "lesion_samples": lesions["lesion"].value_counts().to_dict(),
        "patients": int(patient_table["patient_id"].nunique()),
        "paired_patients": int(
            (
                patient_table["has_primary"].eq(1)
                & patient_table["has_metastasis"].eq(1)
            ).sum()
        ),
        "patient_level_primary_only": int(
            patient_table["metastasis_patient_label"].eq(0).sum()
        ),
        "patient_level_metastatic": int(
            patient_table["metastasis_patient_label"].eq(1).sum()
        ),
        "data_gate": (
            "fail_patient_level_primary_class_too_small"
        ),
    }
    gse9576_summary = {
        "lesion_samples": tumor_9576["lesion"].value_counts().to_dict(),
        "patient_ids_available": False,
        "paired_status_recoverable": False,
        "data_gate": "fail_no_patient_mapping_and_small_classes",
    }

    payload = {
        "GSE27162": gse27162_summary,
        "GSE9576": gse9576_summary,
        "third_disease_full_gate2": False,
        "decision": (
            "Stop patient-level SBNET metastasis prediction; GSE27162 "
            "lesion-type comparison may be reported only as descriptive "
            "single-cohort biology, not as a primary-vs-metastasis prediction."
        ),
    }
    (RESULTS / "RATA_v5_SBNET_data_gate.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
