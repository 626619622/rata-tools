"""Create the final downloadable package after public-release validation."""

from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "submission_package_bioinformatics_public"
OUT = PACKAGE / "RATA_Bioinformatics_Submission_Final.zip"
MANIFEST = PACKAGE / "SHA256SUMS_Submission_Final.txt"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    if OUT.exists():
        raise FileExistsError(OUT)
    excluded = {
        OUT.name,
        "RATA_Bioinformatics_Submission_Package.zip",
        "SHA256SUMS_Final.txt",
        MANIFEST.name,
    }
    files = [
        path
        for path in PACKAGE.rglob("*")
        if path.is_file() and path.name not in excluded
    ]
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(files):
            archive.write(path, path.relative_to(PACKAGE))
    lines = [f"{sha256(path)}  {path.relative_to(PACKAGE)}" for path in sorted(files + [OUT])]
    MANIFEST.write_text("\n".join(lines) + "\n", encoding="ascii")
    print(OUT)
    print(MANIFEST)
    print(f"files={len(files)}")


if __name__ == "__main__":
    main()
