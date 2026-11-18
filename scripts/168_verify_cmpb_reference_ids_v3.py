"""Resolve reference identifiers from the corrected v3 audit table."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "scripts" / "165_verify_cmpb_reference_ids.py"


def main() -> None:
    code = SOURCE.read_text(encoding="utf-8")
    code = code.replace(
        'AUDIT_MD = ROOT / "cmpb_submission_20261118" / "references_verified.md"',
        'AUDIT_MD = ROOT / "cmpb_submission_20261118" / "references_verified_v3.md"',
        1,
    ).replace(
        'OUT_JSON = ROOT / "cmpb_submission_20261118" / "reference_identifier_resolution.json"',
        'OUT_JSON = ROOT / "cmpb_submission_20261118" / "reference_identifier_resolution_v3.json"',
        1,
    ).replace(
        'OUT_MD = ROOT / "cmpb_submission_20261118" / "reference_identifier_resolution.md"',
        'OUT_MD = ROOT / "cmpb_submission_20261118" / "reference_identifier_resolution_v3.md"',
        1,
    )
    namespace = {"__file__": str(SOURCE), "__name__": "rata_reference_ids_v3"}
    exec(compile(code, str(SOURCE), "exec"), namespace)
    namespace["main"]()


if __name__ == "__main__":
    main()
