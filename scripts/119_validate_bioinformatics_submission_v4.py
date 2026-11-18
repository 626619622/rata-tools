"""Validate the final Bioinformatics submission package with author-year style."""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "submission_package_bioinformatics_v4"
SOURCE = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v8.md"
REPORT_JSON = PACKAGE / "Submission_Check_Final.json"
REPORT_MD = PACKAGE / "Submission_Check_Final.md"


def pdf_pages(path: Path) -> int:
    counts = [int(value) for value in re.findall(rb"/Count\s+(\d+)", path.read_bytes())]
    if not counts:
        raise ValueError(f"No PDF page count found in {path}")
    return max(counts)


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    abstract = text.split("## Abstract", 1)[1].split("**Keywords:**", 1)[0]
    body, references = text.split("## References", 1)
    abstract_words = len(re.findall(r"\b[\w]+\b", abstract))
    body_words = len(re.findall(r"\b[\w]+\b", body))

    manuscript = Document(PACKAGE / "RATA_Bioinformatics_Manuscript.docx")
    full_text = "\n".join(p.text for p in manuscript.paragraphs)
    title_page = "\n".join(p.text for p in Document(PACKAGE / "RATA_Bioinformatics_TitlePage.docx").paragraphs)
    cover = "\n".join(p.text for p in Document(PACKAGE / "RATA_Bioinformatics_CoverLetter.docx").paragraphs)
    availability = "\n".join(
        p.text for p in Document(PACKAGE / "RATA_Bioinformatics_SoftwareAvailability.docx").paragraphs
    )

    main_pages = pdf_pages(PACKAGE / "RATA_Bioinformatics_Manuscript.pdf")
    supplement_pages = pdf_pages(PACKAGE / "RATA_Bioinformatics_Supplementary.pdf")

    with zipfile.ZipFile(PACKAGE / "RATA_Bioinformatics_Supplementary_Code.zip") as archive:
        code_bad = archive.testzip()
        code_names = archive.namelist()
    with zipfile.ZipFile(PACKAGE / "RATA_ACC_registry_v1.0.0.zip") as archive:
        registry_bad = archive.testzip()
        registry_names = archive.namelist()

    expected_files = {
        "RATA_Bioinformatics_Manuscript.docx",
        "RATA_Bioinformatics_Manuscript.pdf",
        "RATA_Bioinformatics_TitlePage.docx",
        "RATA_Bioinformatics_TitlePage.pdf",
        "RATA_Bioinformatics_CoverLetter.docx",
        "RATA_Bioinformatics_CoverLetter.pdf",
        "RATA_Bioinformatics_SoftwareAvailability.docx",
        "RATA_Bioinformatics_SoftwareAvailability.pdf",
        "RATA_Bioinformatics_Supplementary.pdf",
        "RATA_Bioinformatics_Supplementary_Code.zip",
        "RATA_Bioinformatics_Submission_Package.zip",
        "RATA_ACC_registry_v1.0.0.zip",
        "Figure_ContactSheet.png",
        "README_SUBMISSION.md",
        "Release_Action_Required.md",
        "SHA256SUMS_Final.txt",
    }
    package_files = {path.name for path in PACKAGE.iterdir() if path.is_file()}

    reference_entries = [
        line
        for line in references.splitlines()
        if line.strip() and not line.startswith("#")
    ]
    checks = {
        "title_framework_first": text.startswith("# RATA: a role-aware three-gate framework and software"),
        "abstract_245_to_270_words": 245 <= abstract_words <= 270,
        "body_4500_to_5200_words": 4500 <= body_words <= 5200,
        "author_year_no_numeric_citations": not re.search(r"\[[0-9][0-9,\s–-]*\]", body),
        "author_year_reference_count_22": len(reference_entries) == 22,
        "implementation_validation_availability_sections": all(
            heading in text for heading in ["## Implementation", "## Validation", "## Availability"]
        ),
        "acc_case_study_present": "ACC case study" in text,
        "software_architecture_figure_legended": "software architecture and audit data flow" in text.lower(),
        "four_main_tables": all(f"### Table {n}." in text for n in range(1, 5)),
        "six_figure_legends": all(f"**Figure {number}." in text for number in range(1, 7)),
        "runtime_has_20k_benchmark": "20,000 features" in text,
        "runtime_has_5fold_k3": "5 folds, k=3" in text,
        "no_latex_render_artifacts": "\\mathrm" not in text and "\\[" not in text,
        "docx_opens": len(manuscript.paragraphs) > 100,
        "docx_has_four_tables": len(manuscript.tables) == 4,
        "docx_table_titles_present": all(f"Table {n}." in full_text for n in range(1, 5)),
        "title_page_original_paper": "Original Paper" in title_page,
        "cover_letter_bioinformatics": "Bioinformatics" in cover and "Original Paper" in cover,
        "availability_mentions_wheel": "wheel" in availability.lower(),
        "main_pdf_at_least_20_pages": main_pages >= 20,
        "supplementary_pdf_at_least_20_pages": supplement_pages >= 20,
        "code_zip_integrity": code_bad is None,
        "code_zip_has_wheel": any(name.endswith("rata_tools-0.2.0-py3-none-any.whl") for name in code_names),
        "code_zip_has_source_archive": any(name.endswith("rata_tools-0.2.0-source-final.zip") for name in code_names),
        "code_zip_has_git_bundle": any(name.endswith("rata-tools-v0.2.0-final.bundle") for name in code_names),
        "code_zip_has_core": any(name.endswith("/src/rata_tools/core.py") for name in code_names),
        "code_zip_has_tests": any(name.endswith("/tests/test_core.py") for name in code_names),
        "code_zip_has_ci": any(name.endswith("/.github/workflows/ci.yml") for name in code_names),
        "code_zip_has_zenodo": any(name.endswith("/.zenodo.json") for name in code_names),
        "code_zip_has_manuscript": any(name.endswith("RATA_Paper_Bioinformatics_v8.md") for name in code_names),
        "code_zip_has_v2_benchmark": any(
            name.endswith("/results/Bioinformatics_RuntimeBenchmark_v2.csv") for name in code_names
        ),
        "registry_zip_integrity": registry_bad is None,
        "registry_zip_has_pair_registry": "data/ACC_Provenance_Pairs_v3.csv" in registry_names,
        "registry_zip_has_metadata": ".zenodo.json" in registry_names,
        "package_files_complete": expected_files.issubset(package_files),
        "six_figure_pdfs": len(list((PACKAGE / "Figures").glob("*.pdf"))) == 6,
        "six_figure_pngs": len(list((PACKAGE / "Figures").glob("*.png"))) == 6,
        "six_figure_legends": len(list((PACKAGE / "Figures").glob("*.md"))) == 6,
    }
    report = {
        "all_checks_pass": all(checks.values()),
        "abstract_words": abstract_words,
        "body_words": body_words,
        "reference_entries": len(reference_entries),
        "main_docx_tables": len(manuscript.tables),
        "main_pdf_pages": main_pages,
        "supplementary_pdf_pages": supplement_pages,
        "supplementary_code_files": len(code_names),
        "registry_files": len(registry_names),
        "checks": checks,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# RATA Bioinformatics submission check",
        "",
        f"Overall: **{'PASS' if report['all_checks_pass'] else 'FAIL'}**",
        "",
        f"- Abstract: {abstract_words} words.",
        f"- Main body: {body_words} words.",
        f"- Reference entries: {len(reference_entries)}.",
        f"- Main PDF: {main_pages} pages.",
        f"- Supplementary PDF: {supplement_pages} pages.",
        f"- Main DOCX tables: {len(manuscript.tables)}.",
        f"- Supplementary code archive: {len(code_names)} files.",
        f"- Registry archive: {len(registry_names)} files.",
        "",
        "## Checks",
        "",
    ]
    lines.extend(f"- {'PASS' if value else 'FAIL'} | `{key}`" for key, value in checks.items())
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(REPORT_MD)
    print(json.dumps(report, indent=2))
    if not report["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
