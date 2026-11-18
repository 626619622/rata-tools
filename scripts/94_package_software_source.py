"""Create a clean source archive for rata-tools 0.2.0."""

from __future__ import annotations

from pathlib import Path
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "rata_tools_release_0.2.0"
OUT = SOURCE / "dist" / "rata_tools-0.2.0-source.zip"

EXCLUDED_PARTS = {
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "build",
}


def main() -> None:
    if OUT.exists():
        raise FileExistsError(OUT)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUT, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(SOURCE.rglob("*")):
            if not path.is_file():
                continue
            if path == OUT or any(part in EXCLUDED_PARTS for part in path.parts):
                continue
            if path.suffix in {".pyc", ".pyo"}:
                continue
            archive.write(path, Path("rata_tools-0.2.0") / path.relative_to(SOURCE))
    print(OUT)
    print(f"files={len(zipfile.ZipFile(OUT).namelist())}")


if __name__ == "__main__":
    main()
