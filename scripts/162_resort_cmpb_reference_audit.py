"""Run the reference-table resort while restricting rows to the 42-entry section."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "161_resort_cmpb_reference_audit.py"


def main() -> None:
    code = SOURCE.read_text(encoding="utf-8")
    code = code.replace(
        "for line in audit.splitlines():",
        'for line in audit.split("## 四、全部 42 条核验明细", 1)[1].split("## 五、", 1)[0].splitlines():',
        1,
    )
    namespace = {"__file__": str(SOURCE), "__name__": "rata_reference_resort"}
    exec(compile(code, str(SOURCE), "exec"), namespace)
    namespace["main"]()


if __name__ == "__main__":
    main()
