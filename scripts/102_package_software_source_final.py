"""Create the final source archive including Zenodo metadata."""

from __future__ import annotations

from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "rata_tools_release_0.2.0"
OUT = SOURCE / "dist" / "rata_tools-0.2.0-source-final.zip"

EXCLUDED_PARTS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "build",
    "dist",
}


def main() -> None:
    if OUT.exists():
        raise FileExistsError(OUT)
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(SOURCE.rglob("*")):
            if not path.is_file():
                continue
            if any(part in EXCLUDED_PARTS for part in path.relative_to(SOURCE).parts):
                continue
            if path.suffix in {".pyc", ".pyo"}:
                continue
            archive.write(path, Path("rata_tools-0.2.0") / path.relative_to(SOURCE))
    print(OUT)
    print(f"files={len(zipfile.ZipFile(OUT).namelist())}")


if __name__ == "__main__":
    main()
