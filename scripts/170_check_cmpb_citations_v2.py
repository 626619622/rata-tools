"""Check reference coverage using parenthetical author-year citation groups."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "cmpb_submission_20261118" / "RATA_CMPB_Manuscript_v3.md"
OUT_JSON = ROOT / "cmpb_submission_20261118" / "citation_coverage_v2.json"
OUT_MD = ROOT / "cmpb_submission_20261118" / "citation_coverage_v2.md"


def main() -> None:
    text = MANUSCRIPT.read_text(encoding="utf-8")
    body = text.split("## References", 1)[0]
    refs_text = text.split("## References", 1)[1].split("## Tables", 1)[0]
    references = [
        line.strip()
        for line in refs_text.splitlines()
        if line.strip() and line.strip() != "---"
    ]
    groups = re.findall(r"\(([^()]*\b(?:19|20)\d{2}\b[^()]*)\)", body)
    rows = []
    for index, reference in enumerate(references, start=1):
        surname = re.match(r"([^\s,]+)", reference).group(1)
        year = re.findall(r"\b(?:19|20)\d{2}\b", reference)[0]
        cited = any(
            re.search(rf"\b{re.escape(surname)}\b", group, re.IGNORECASE)
            and re.search(rf"\b{year}\b", group)
            for group in groups
        )
        rows.append(
            {
                "number": index,
                "surname": surname,
                "year": year,
                "cited": cited,
                "reference": reference,
            }
        )
    missing = [row for row in rows if not row["cited"]]
    payload = {
        "total": len(rows),
        "citation_groups": len(groups),
        "cited": len(rows) - len(missing),
        "missing_count": len(missing),
        "missing": missing,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = [
        "# CMPB citation coverage",
        "",
        f"- References: {len(rows)}",
        f"- Citation groups detected: {len(groups)}",
        f"- Cited: {len(rows) - len(missing)}",
        f"- Missing: {len(missing)}",
        "",
        "| # | First author | Year | Cited |",
        "|---:|---|---|---|",
    ]
    lines.extend(
        f"| {row['number']} | {row['surname']} | {row['year']} | {row['cited']} |"
        for row in rows
    )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(OUT_MD)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    if missing:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
