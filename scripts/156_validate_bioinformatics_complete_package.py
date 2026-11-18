"""Run final validation while accepting UTF-8 BOM in the DOI manifest."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "155_validate_bioinformatics_complete_package.py"


def main() -> None:
    code = SOURCE.read_text(encoding="utf-8")
    code = code.replace('decode("utf-8")', 'decode("utf-8-sig")')
    namespace = {"__file__": str(SOURCE), "__name__": "rata_final_validator"}
    exec(compile(code, str(SOURCE), "exec"), namespace)
    namespace["main"]()


if __name__ == "__main__":
    main()
