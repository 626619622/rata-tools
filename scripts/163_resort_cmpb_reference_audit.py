"""Apply the verified Robertson reorder to the 42-row reference audit table."""

from __future__ import annotations

import csv
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = Path(r"C:\Users\赵佳康\Documents\deepseek-harness\default-workspace\rata_final")
MANUSCRIPT = ROOT / "cmpb_submission_20261118" / "RATA_CMPB_Manuscript_v2.md"
AUDIT_MD = SOURCE_DIR / "references_verified.md"
OUT = ROOT / "cmpb_submission_20261118"


def main() -> None:
    manuscript = MANUSCRIPT.read_text(encoding="utf-8")
    refs_text = manuscript.split("## References", 1)[1].split("## Tables", 1)[0]
    references = [
        line.strip()
        for line in refs_text.splitlines()
        if line.strip() and line.strip() != "---"
    ]
    if len(references) != 42:
        raise ValueError(f"Expected 42 references, found {len(references)}")

    audit = AUDIT_MD.read_text(encoding="utf-8")
    rows_text = audit.split("## 四、全部 42 条核验明细", 1)[1].split("## 五、", 1)[0]
    rows_by_number = {}
    for line in rows_text.splitlines():
        match = re.match(r"^\|\s*(\d+)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$", line)
        if match:
            number = int(match.group(1))
            rows_by_number[number] = {
                "old_number": number,
                "short_citation": match.group(2),
                "identifier": match.group(3),
                "check": match.group(4),
            }
    if sorted(rows_by_number) != list(range(1, 43)):
        raise ValueError("Reference audit table does not contain numbers 1-42")

    mapping = list(range(1, 10)) + list(range(11, 33)) + [10] + list(range(33, 43))
    if len(mapping) != 42 or len(set(mapping)) != 42:
        raise ValueError("Reference reorder mapping is invalid")

    output_rows = []
    for new_number, old_number in enumerate(mapping, start=1):
        row = rows_by_number[old_number]
        output_rows.append(
            {
                "new_number": new_number,
                "old_number": old_number,
                "reference": references[new_number - 1],
                "identifier": row["identifier"],
                "check": row["check"],
            }
        )

    mapping_path = OUT / "reference_number_mapping_v2.csv"
    with mapping_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output_rows[0]))
        writer.writeheader()
        writer.writerows(output_rows)

    table_lines = ["| # | 引用 | 标识符 | 核验 |", "|---|---|---|---|"]
    for row in output_rows:
        citation = row["reference"].replace("|", "/")
        table_lines.append(
            f"| {row['new_number']} | {citation} | {row['identifier']} | {row['check']} |"
        )
    replacement = "\n".join(table_lines) + "\n"
    start = audit.index("| # | 引用 | 标识符 | 核验 |")
    end = audit.index("\n## 五、一致性检查", start)
    audit_v2 = audit[:start] + replacement + audit[end:]
    audit_v2 = audit_v2.replace(
        "核验日期：2026-11-18",
        "核验日期：2026-11-18；排序复核：2026-11-18",
        1,
    )
    (OUT / "references_verified.md").write_text(audit_v2, encoding="utf-8")
    print(mapping_path)
    print(OUT / "references_verified.md")


if __name__ == "__main__":
    main()
