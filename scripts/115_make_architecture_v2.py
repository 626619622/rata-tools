"""Render the corrected architecture figure without an unverified registry install command."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "81_make_software_architecture_figure.py"


def main() -> None:
    code = SOURCE.read_text(encoding="utf-8")
    code = code.replace(
        'OUT = ROOT / "figures" / "bioinformatics"',
        'OUT = ROOT / "figures" / "bioinformatics_v2"',
        1,
    ).replace(
        '"pip install rata-tools | tests | CI | MIT license"',
        '"pip install <included-wheel> | tests | CI | MIT license"',
        1,
    )
    namespace = {
        "__file__": str(SOURCE),
        "__name__": "rata_architecture_v2",
    }
    exec(compile(code, str(SOURCE), "exec"), namespace)
    namespace["main"]()


if __name__ == "__main__":
    main()
