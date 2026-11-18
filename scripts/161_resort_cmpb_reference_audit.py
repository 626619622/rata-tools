"""Reorder the 42-reference verification table to match manuscript author-year order."""

from __future__ import annotations

import csv
import difflib
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = Path(r"C:\Users\赵佳康\Documents\deepseek-harness\default-workspace\rata_final")
MANUSCRIPT = ROOT / "cmpb_submission_20261118" / "RATA_CMPB_Manuscript_v2.md"
AUDIT_MD = SOURCE_DIR / "references_verified.md"
OUT = ROOT / "cmpb_submission_20261118"


def normalize(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"[*_`]", "", value)
    value = re.sub(r"[^A-Za-z0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip().lower()


def main() -> None:
    manuscript = MANUSCRIPT.read_text(encoding="utf-8")
    refs_text = manuscript.split("## References", 1)[1].split("## Tables", 1)[0]
    references = [
        line.strip()
        for line in refs_text.splitlines()
        if line.strip() and line.strip() != "---"
    ]
    if len(references) != 42:
        raise ValueError(f"Expected 42 manuscript references, found {len(references)}")

    audit = AUDIT_MD.read_text(encoding="utf-8")
    rows = []
    for line in audit.splitlines():
        match = re.match(r"^\|\s*(\d+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$", line)
        if match:
            rows.append(
                {
                    "old_number": int(match.group(1)),
                    "citation": match.group(2),
                    "identifier": match.group(3),
                    "check": match.group(4),
                }
            )
    if len(rows) != 42:
        raise ValueError(f"Expected 42 manually checked rows, found {len(rows)}")

    used: set[int] = set()
    mapping = []
    for new_number, reference in enumerate(references, start=1):
        scored = []
        ref_norm = normalize(reference)
        for index, row in enumerate(rows):
            if index in used:
                continue
            row_norm = normalize(row["citation"])
            score = difflib.SequenceMatcher(None, ref_norm, row_norm).ratio()
            scored.append((score, index, row))
        score, index, row = max(scored, key=lambda item: item[0])
        if score < 0.45:
            raise ValueError(
                f"Low-confidence match for reference {new_number}: {reference} -> {row}"
            )
        used.add(index)
        mapping.append(
            {
                "new_number": new_number,
                "old_number": row["old_number"],
                "score": round(score, 4),
                "reference": reference,
                "identifier": row["identifier"],
                "check": row["check"],
            }
        )

    mapping_path = OUT / "reference_number_mapping_v2.csv"
    with mapping_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(mapping[0]))
        writer.writeheader()
        writer.writerows(mapping)

    table_lines = [
        "| # | 引用 | 标识符 | 核验 |",
        "|---|---|---|---|",
    ]
    for item in mapping:
        # Keep the complete manuscript reference as the Editorial Manager source.
        citation = item["reference"].replace("|", "/")
        table_lines.append(
            f"| {item['new_number']} | {citation} | {item['identifier']} | {item['check']} |"
        )
    new_table = "\n".join(table_lines) + "\n"

    start = audit.index("| # | 引用 | 标识符 | 核验 |")
    end = audit.index("\n## 五、一致性检查", start)
    audit_v2 = audit[:start] + new_table + audit[end:]
    audit_v2 = audit_v2.replace("核验日期：2026-11-18", "核验日期：2026-11-18；排序复核：2026-11-18")
    (OUT / "references_verified.md").write_text(audit_v2, encoding="utf-8")

    print(mapping_path)
    print(OUT / "references_verified.md")
    print(f"mapped={len(mapping)} min_score={min(item['score'] for item in mapping)}")


if __name__ == "__main__":
    main()
