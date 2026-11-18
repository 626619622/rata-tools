"""Check that every CMPB reference is cited in the author-year text."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "cmpb_submission_20261118" / "RATA_CMPB_Manuscript_v3.md"
OUT_JSON = ROOT / "cmpb_submission_20261118" / "citation_coverage.json"
OUT_MD = ROOT / "cmpb_submission_20261118" / "citation_coverage.md"


def main() -> None:
    text = MANUSCRIPT.read_text(encoding="utf-8")
    body = text.split("## References", 1)[0]
    refs_text = text.split("## References", 1)[1].split("## Tables", 1)[0]
    references = [
        line.strip()
        for line in refs_text.splitlines()
        if line.strip() and line.strip() != "---"
    ]
    rows = []
    for index, reference in enumerate(references, start=1):
        surname_match = re.match(r"([^\s,]+)", reference)
        year_matches = re.findall(r"\b(?:19|20)\d{2}\b", reference)
        if not surname_match or not year_matches:
            rows.append(
                {
                    "number": index,
                    "reference": reference,
                    "surname": "",
                    "year": "",
                    "cited": False,
                }
            )
            continue
        surname = surname_match.group(1)
        year = year_matches[0]
        pattern = re.compile(
            rf"\b{re.escape(surname)}\b[^.;()]{{0,60}}\b{year}\b",
            re.IGNORECASE,
        )
        rows.append(
            {
                "number": index,
                "reference": reference,
                "surname": surname,
                "year": year,
                "cited": bool(pattern.search(body)),
            }
        )

    missing = [row for row in rows if not row["cited"]]
    payload = {
        "total": len(rows),
        "cited": len(rows) - len(missing),
        "missing_count": len(missing),
        "missing": missing,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# CMPB citation coverage",
        "",
        f"- References: {len(rows)}",
        f"- Cited: {len(rows) - len(missing)}",
        f"- Missing: {len(missing)}",
        "",
        "| # | First author | Year | Cited |",
        "|---:|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['number']} | {row['surname']} | {row['year']} | {row['cited']} |")
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(OUT_MD)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    if missing:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
