"""Build a clean ACC registry deposit archive."""

from __future__ import annotations

from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "release_artifacts"
OUT = OUT_DIR / "RATA_ACC_registry_v1.0.0.zip"

FILES = {
    ROOT / "registry" / "ACC_Provenance_Pairs_v3.csv": "data/ACC_Provenance_Pairs_v3.csv",
    ROOT / "registry" / "ACC_Signature_Registry_v2.csv": "data/ACC_Signature_Registry_v2.csv",
    ROOT / "results" / "RATA_v3_evidence_capacity.json": "data/RATA_v3_evidence_capacity.json",
    ROOT / "results" / "RATA_v5_evidence_capacity_metrics.json": "data/RATA_v5_evidence_capacity_metrics.json",
    ROOT / "results" / "RATA_v5_adult_cluster_counts.csv": "data/RATA_v5_adult_cluster_counts.csv",
    ROOT / "results" / "RATA_v5_reported_cluster_counts.csv": "data/RATA_v5_reported_cluster_counts.csv",
    ROOT / "results" / "known_nonindependent_dataset_pairs.csv": "data/known_nonindependent_dataset_pairs.csv",
    ROOT / "RATA_Registry_README.md": "README.md",
    ROOT / "RATA_Registry_Codebook.md": "CODEBOOK.md",
    ROOT / "RATA_registry_zenodo.json": ".zenodo.json",
}


def main() -> None:
    if OUT.exists():
        raise FileExistsError(OUT)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source, target in FILES.items():
            if not source.exists():
                raise FileNotFoundError(source)
            archive.write(source, target)
    print(OUT)
    print(f"files={len(FILES)}")


if __name__ == "__main__":
    main()
