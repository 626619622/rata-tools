"""Update CMPB reference audit and checklist for the v3 final files."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
IN_DIR = ROOT / "cmpb_submission_20261118"


def main() -> None:
    audit = (IN_DIR / "references_verified.md").read_text(encoding="utf-8")
    old_34 = (
        "| 34 | Sagawa S, Koh PW, Hashimoto TB, Liang P. Distributionally robust neural "
        "networks for group shifts. *Proceedings of ICLR* 2020. | arXiv API | ✅ |"
    )
    new_34 = (
        "| 34 | Sagawa S, Koh PW, Hashimoto TB, Liang P. Distributionally robust neural "
        "networks for group shifts. *Proceedings of ICLR* 2020. arXiv:1911.08731. | "
        "arXiv 1911.08731 | ✅ |"
    )
    old_36 = (
        "| 36 | Steyerberg EW. *Clinical Prediction Models: A Practical Approach to "
        "Development, Validation, and Updating*. 2nd ed. Cham: Springer; 2019. | 专著 | ✅ |"
    )
    new_36 = (
        "| 36 | Steyerberg EW. *Clinical Prediction Models: A Practical Approach to "
        "Development, Validation, and Updating*. 2nd ed. Cham: Springer; 2019. "
        "doi:10.1007/978-3-030-16399-0. | DOI 10.1007/978-3-030-16399-0 | ✅ |"
    )
    for old, new in [(old_34, new_34), (old_36, new_36)]:
        if old not in audit:
            raise ValueError(f"Expected reference audit row not found: {old[:80]}")
        audit = audit.replace(old, new, 1)
    (IN_DIR / "references_verified_v3.md").write_text(audit, encoding="utf-8")

    checklist = (IN_DIR / "SUBMISSION_CHECKLIST_v2.md").read_text(encoding="utf-8")
    item2_old = (
        "- [ ] **2. GSE76201 措辞与再确认**：正文目前写的是可核查的事实陈述"
        "（*Mus musculus*、GPL6246、n=4）。请再通读被引论文原文，确认它确实把该 "
        "accession 列为外部验证队列。**不要**使用\"错误\"\"造假\"等评价性措辞。"
    )
    item2_new = (
        "- [x] **2. GSE76201 措辞与再确认**：已核对被引论文原文与 GEO 记录。"
        "原文确实把 GSE76201 指定为 external validation；GEO 记录为 *Mus musculus*、"
        "GPL6246、4 个样本的 ILC3 数据。正文已改为“论文声明与 GEO 记录不一致”的事实陈述。"
    )
    if item2_old not in checklist:
        raise ValueError("Checklist item 2 text not found")
    checklist = checklist.replace(item2_old, item2_new, 1)
    (IN_DIR / "SUBMISSION_CHECKLIST_v3.md").write_text(checklist, encoding="utf-8")
    print(IN_DIR / "references_verified_v3.md")
    print(IN_DIR / "SUBMISSION_CHECKLIST_v3.md")


if __name__ == "__main__":
    main()
