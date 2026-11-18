"""Finalize CMPB v3: Gate 1 lock, cautious GSE76201 wording and identifiers."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = Path(r"C:\Users\赵佳康\Documents\deepseek-harness\default-workspace\rata_final")
IN_DIR = ROOT / "cmpb_submission_20261118"
SOURCE_MD = IN_DIR / "RATA_CMPB_Manuscript_v2.md"
OUT_MD = IN_DIR / "RATA_CMPB_Manuscript_v3.md"
OUT_DOCX = IN_DIR / "RATA_CMPB_Manuscript_v3.docx"
BUILDER = SOURCE_DIR / "build_docx.py"
PYTHON = ROOT.parent / "pituitary-env" / "python311" / "python.exe"


def main() -> None:
    text = SOURCE_MD.read_text(encoding="utf-8")

    old_gse = (
        "The four non-verifiable declarations were a signature whose cited accession "
        "(GSE76201) is a murine ILC3 dataset (*Mus musculus*, GPL6246, four samples; "
        "GEO series GSE76201), a signature citing an accession that could not be traced, "
        "a signature with no ACC-specific external cohort, and the signature just described."
    )
    new_gse = (
        "The four non-verifiable declarations were a signature whose publication "
        "explicitly designated GSE76201 as its external validation set, whereas the GEO "
        "record for that accession describes a *Mus musculus* mesenteric-lymph-node ILC3 "
        "study (GPL6246; four samples); a signature citing an accession that could not be "
        "traced; a signature with no ACC-specific external cohort; and the signature just described."
    )
    if old_gse not in text:
        raise ValueError("Expected GSE76201 paragraph not found")
    text = text.replace(old_gse, new_gse, 1)
    text = text.replace(
        "**Invalid accession (murine ILC3)**",
        "**Accession incompatible with claim (murine ILC3)**",
        1,
    )

    old_sagawa = (
        "Sagawa S, Koh PW, Hashimoto TB, Liang P. Distributionally robust neural "
        "networks for group shifts. *Proceedings of ICLR* 2020."
    )
    new_sagawa = (
        "Sagawa S, Koh PW, Hashimoto TB, Liang P. Distributionally robust neural "
        "networks for group shifts. *Proceedings of ICLR* 2020. arXiv:1911.08731."
    )
    old_steyerberg = (
        "Steyerberg EW. *Clinical Prediction Models: A Practical Approach to Development, "
        "Validation, and Updating*. 2nd ed. Cham: Springer; 2019."
    )
    new_steyerberg = (
        "Steyerberg EW. *Clinical Prediction Models: A Practical Approach to Development, "
        "Validation, and Updating*. 2nd ed. Cham: Springer; 2019. "
        "doi:10.1007/978-3-030-16399-0."
    )
    for old, new in [(old_sagawa, new_sagawa), (old_steyerberg, new_steyerberg)]:
        if old not in text:
            raise ValueError(f"Expected reference not found: {old[:60]}")
        text = text.replace(old, new, 1)

    OUT_MD.write_text(text, encoding="utf-8")
    subprocess.run(
        [str(PYTHON), str(BUILDER), str(OUT_MD), str(OUT_DOCX)],
        check=True,
        cwd=str(IN_DIR),
    )

    audit_path = IN_DIR / "references_verified.md"
    audit = audit_path.read_text(encoding="utf-8")
    audit = audit.replace(
        "| 34 | Sagawa S, et al. ICLR 2020. arXiv:1911.08731. | arXiv API | ✅ |",
        "| 34 | Sagawa S, et al. ICLR 2020. arXiv:1911.08731. | arXiv 1911.08731 | ✅ |",
        1,
    )
    audit = audit.replace(
        "| 36 | Steyerberg EW. *Clinical Prediction Models*, 2nd ed. Springer, 2019. | 专著 | ✅ |",
        "| 36 | Steyerberg EW. *Clinical Prediction Models*, 2nd ed. Springer, 2019. | DOI 10.1007/978-3-030-16399-0 | ✅ |",
        1,
    )
    if "arXiv 1911.08731" not in audit or "10.1007/978-3-030-16399-0" not in audit:
        raise ValueError("Failed to update reference identifier audit")
    (IN_DIR / "references_verified_v3.md").write_text(audit, encoding="utf-8")

    checklist_path = IN_DIR / "SUBMISSION_CHECKLIST_v2.md"
    checklist = checklist_path.read_text(encoding="utf-8")
    checklist = checklist.replace(
        "- [ ] **2. GSE76201 措辞与再确认**：正文目前写的是可核查的事实陈述（*Mus musculus*、GPL6246、n=4）。请再通读被引论文原文，确认它确实把该 accession 列为外部验证队列。**不要**使用\"错误\"\"造假\"等评价性措辞。",
        "- [x] **2. GSE76201 措辞与再确认**：已核对被引论文原文与 GEO 记录。原文确实把 GSE76201 指定为 external validation；GEO 记录为 *Mus musculus*、GPL6246、4 个样本的 ILC3 数据。正文已改为“论文声明与 GEO 记录不一致”的事实陈述。",
        1,
    )
    (IN_DIR / "SUBMISSION_CHECKLIST_v3.md").write_text(checklist, encoding="utf-8")

    print(OUT_MD)
    print(OUT_DOCX)
    print(IN_DIR / "references_verified_v3.md")
    print(IN_DIR / "SUBMISSION_CHECKLIST_v3.md")


if __name__ == "__main__":
    main()
