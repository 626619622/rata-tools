"""Build CMPB manuscript v2 with locked Gate 1 value and corrected reference order."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = Path(r"C:\Users\赵佳康\Documents\deepseek-harness\default-workspace\rata_final")
SOURCE_MD = SOURCE_DIR / "RATA_CMPB_Manuscript_v1.md"
OUT = ROOT / "cmpb_submission_20261118"
OUT.mkdir(parents=True, exist_ok=True)

PYTHON = ROOT.parent / "pituitary-env" / "python311" / "python.exe"
BUILDER = SOURCE_DIR / "build_docx.py"
RECHECK_DIR = ROOT / "revisions" / "cmpb_20261118"


def main() -> None:
    text = SOURCE_MD.read_text(encoding="utf-8")

    old_result = (
        "Three of the six rescorable signatures exceeded the 95th percentile of the "
        "matched realistic null: ATF/CREB (percentile 100.0, p = 0.002), the "
        "13-gene ssGSEA signature (99.0, p = 0.012) and the metabolic signature "
        "(99.0, p = 0.012). Two fell just below the threshold — hypoxia (89.8, "
        "p = 0.106) and immune IRG (88.8, p = 0.120)."
    )
    new_result = (
        "In the final seeded calibration (seed 20261110; 500 simulations per null), "
        "three of the six rescorable signatures exceeded the 95th percentile of the "
        "matched realistic null: ATF/CREB (percentile 100.0, p = 0.002), the "
        "13-gene ssGSEA signature (99.0, p = 0.012) and the metabolic signature "
        "(99.0, p = 0.012). Two fell just below the threshold — hypoxia (89.8, "
        "p = 0.106) and immune IRG (88.8, p = 0.120)."
    )
    if old_result not in text:
        raise ValueError("Expected Gate 1 Results sentence not found")
    text = text.replace(old_result, new_result, 1)

    old_note = (
        "Gate 1 threshold: 95th percentile of the matched realistic selection null."
    )
    new_note = (
        "Gate 1 threshold: 95th percentile of the matched realistic selection null. "
        "Values are from the final seeded calibration (seed 20261110; "
        "500 simulations per null)."
    )
    if old_note not in text:
        raise ValueError("Expected Table 5 note not found")
    text = text.replace(old_note, new_note, 1)

    robertson = (
        "Robertson SE, Steingrimsson JA, Joyce NR, Stuart EA, Dahabreh IJ. "
        "Estimating subgroup effects in generalizability and transportability "
        "analyses. *Am J Epidemiol* 2024;193:149–158.\n\n"
    )
    riley = (
        "Riley RD, Ensor J, Snell KIE, et al. Calculating the sample size required "
        "for developing a clinical prediction model. *BMJ* 2020;368:m441.\n\n"
    )
    if text.count(robertson) != 1 or text.count(riley) != 1:
        raise ValueError("Could not uniquely locate Robertson or Riley reference")
    text = text.replace(robertson, "", 1)
    text = text.replace(riley, riley + robertson, 1)

    md_out = OUT / "RATA_CMPB_Manuscript_v2.md"
    md_out.write_text(text, encoding="utf-8")

    docx_out = OUT / "RATA_CMPB_Manuscript_v2.docx"
    subprocess.run(
        [str(PYTHON), str(BUILDER), str(md_out), str(docx_out)],
        check=True,
        cwd=str(OUT),
    )

    shutil.copy2(SOURCE_DIR / "references_verified.md", OUT / "references_verified.md")
    checklist = (SOURCE_DIR / "SUBMISSION_CHECKLIST.md").read_text(encoding="utf-8")
    checklist = checklist.replace(
        "- [ ] **3. 数字一致性**：稿件中 Gate 1 分位数（100.0 / 99.0 / 99.0 / 89.8 / 88.8 / 0.2）来自 `RATA_v5_double_null_selection_gate.csv`。A3 重跑显示 hypoxia 为 90.0（差 0.2 pp）。**用最终脚本重跑一次，把 CSV 与正文统一到同一次运行。**",
        "- [x] **3. 数字一致性**：固定种子 20261110、每个 null 500 次模拟的最终重算得到 hypoxia = 89.8，与正文和 Table 5 完全一致；以 `RATA_v5_double_null_selection_gate_final.csv` 为锁定值。",
        1,
    )
    (OUT / "SUBMISSION_CHECKLIST_v2.md").write_text(checklist, encoding="utf-8")

    recheck_csv = RECHECK_DIR / "RATA_v5_double_null_selection_gate_recheck_20261118.csv"
    recheck_json = RECHECK_DIR / "RATA_v5_double_null_selection_gate_recheck_20261118.json"
    shutil.copy2(recheck_csv, OUT / "RATA_v5_double_null_selection_gate_final.csv")
    shutil.copy2(recheck_json, OUT / "RATA_v5_double_null_selection_gate_final.json")

    lock_note = """# Gate 1 final value lock

- Final seed: 20261110
- Simulations per null: 500
- Hypoxia realistic-null percentile: 89.8
- Difference from manuscript/Table 5: 0.0 percentage points
- The previously observed 90.0 was not reproduced by the final fixed-seed run.
- Canonical result file: `RATA_v5_double_null_selection_gate_final.csv`

The final result reproduces the six reported values exactly:

| Signature | Percentile |
|---|---:|
| ATF/CREB | 100.0 |
| ssGSEA | 99.0 |
| Metabolic | 99.0 |
| Hypoxia | 89.8 |
| Immune IRG | 88.8 |
| Prognostic | 0.2 |
"""
    (OUT / "Gate1_Final_Lock.md").write_text(lock_note, encoding="utf-8")

    print(md_out)
    print(docx_out)
    print(OUT / "Gate1_Final_Lock.md")
    print(OUT / "SUBMISSION_CHECKLIST_v2.md")


if __name__ == "__main__":
    main()
