"""Validate the final Bioinformatics v2 submission package."""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "submission_package_bioinformatics_v2"
SOURCE = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v6.md"
REPORT_JSON = PACKAGE / "Submission_Check_Final.json"
REPORT_MD = PACKAGE / "Submission_Check_Final.md"


def citation_numbers(text: str) -> set[int]:
    cited: set[int] = set()
    for group in re.findall(r"\[([0-9][0-9,\s–-]*)\]", text):
        for part in re.split(r",\s*", group):
            part = part.strip()
            if re.fullmatch(r"\d+", part):
                cited.add(int(part))
            elif re.fullmatch(r"\d+\s*[–-]\s*\d+", part):
                start, end = re.split(r"\s*[–-]\s*", part)
                cited.update(range(int(start), int(end) + 1))
    return cited


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    abstract = text.split("## Abstract", 1)[1].split("**Keywords:**", 1)[0]
    body, references = text.split("## References", 1)
    abstract_words = len(re.findall(r"\b[\w]+\b", abstract))
    body_words = len(re.findall(r"\b[\w]+\b", body))
    reference_numbers = {int(value) for value in re.findall(r"(?m)^\s*(\d+)\.\s+", references)}
    cited = citation_numbers(body)

    manuscript = Document(PACKAGE / "RATA_Bioinformatics_Manuscript.docx")
    full_text = "\n".join(p.text for p in manuscript.paragraphs)
    title_page = "\n".join(p.text for p in Document(PACKAGE / "RATA_Bioinformatics_TitlePage.docx").paragraphs)
    cover = "\n".join(p.text for p in Document(PACKAGE / "RATA_Bioinformatics_CoverLetter.docx").paragraphs)
    availability = "\n".join(
        p.text for p in Document(PACKAGE / "RATA_Bioinformatics_SoftwareAvailability.docx").paragraphs
    )

    supplement_bytes = (PACKAGE / "RATA_Bioinformatics_Supplementary.pdf").read_bytes()
    supplement_pages = len(re.findall(rb"/Type\s*/Page\b", supplement_bytes))
    main_bytes = (PACKAGE / "RATA_Bioinformatics_Manuscript.pdf").read_bytes()
    main_pages = len(re.findall(rb"/Type\s*/Page\b", main_bytes))

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
        "RATA_Bioinformatics_CoverLetter.docx",
        "RATA_Bioinformatics_SoftwareAvailability.docx",
        "RATA_Bioinformatics_Supplementary.pdf",
        "RATA_Bioinformatics_Supplementary_Code.zip",
        "RATA_ACC_registry_v1.0.0.zip",
        "Figure_ContactSheet.png",
        "README_SUBMISSION.md",
        "Release_Action_Required.md",
        "SHA256SUMS.txt",
    }
    package_files = {path.name for path in PACKAGE.iterdir() if path.is_file()}

    checks = {
        "title_framework_first": text.startswith("# RATA: a role-aware three-gate framework and software"),
        "abstract_245_to_270_words": 245 <= abstract_words <= 270,
        "body_4500_to_5200_words": 4500 <= body_words <= 5200,
        "implementation_validation_availability_sections": all(
            heading in text for heading in ["## Implementation", "## Validation", "## Availability"]
        ),
        "acc_explicitly_case_study": "ACC case study" in text,
        "software_architecture_figure_legended": "software architecture and audit data flow" in text.lower(),
        "four_main_tables_in_source": all(
            marker in text
            for marker in [
                "### Table 1.",
                "### Table 2.",
                "### Table 3.",
                "### Table 4.",
            ]
        ),
        "six_figure_legends": all(f"**Figure {number}." in text for number in range(1, 7)),
        "references_all_cited": reference_numbers == cited,
        "no_latex_render_artifacts": "\\mathrm" not in text and "\\[" not in text,
        "docx_opens": len(manuscript.paragraphs) > 100,
        "docx_has_four_tables": len(manuscript.tables) == 4,
        "docx_table_titles_present": all(f"Table {n}." in full_text for n in range(1, 5)),
        "title_page_original_paper": "Original Paper" in title_page,
        "cover_letter_original_paper": "Original Paper" in cover,
        "cover_letter_bioinformatics": "Bioinformatics" in cover,
        "availability_mentions_wheel": "wheel" in availability.lower(),
        "supplementary_references_s1_to_s4": all(
            f"Supplementary Table S{table}" in text for table in range(1, 5)
        ),
        "supplementary_pdf_at_least_20_pages": supplement_pages >= 20,
        "main_pdf_at_least_20_pages": main_pages >= 20,
        "code_zip_integrity": code_bad is None,
        "code_zip_has_wheel": any(name.endswith("rata_tools-0.2.0-py3-none-any.whl") for name in code_names),
        "code_zip_has_source_archive": any(name.endswith("rata_tools-0.2.0-source-final.zip") for name in code_names),
        "code_zip_has_git_bundle": any(name.endswith("rata-tools-v0.2.0-final.bundle") for name in code_names),
        "code_zip_has_core": any(name.endswith("/src/rata_tools/core.py") for name in code_names),
        "code_zip_has_tests": any(name.endswith("/tests/test_core.py") for name in code_names),
        "code_zip_has_ci": any(name.endswith("/.github/workflows/ci.yml") for name in code_names),
        "code_zip_has_zenodo": any(name.endswith("/.zenodo.json") for name in code_names),
        "code_zip_has_manuscript": any(name.endswith("RATA_Paper_Bioinformatics_v6.md") for name in code_names),
        "code_zip_has_benchmark": any(name.endswith("/results/Bioinformatics_RuntimeBenchmark.csv") for name in code_names),
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
        "main_docx_tables": len(manuscript.tables),
        "main_pdf_pages": main_pages,
        "supplementary_pdf_pages": supplement_pages,
        "references_listed": len(reference_numbers),
        "references_cited": len(cited),
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
        f"- Main PDF: {main_pages} pages.",
        f"- Supplementary PDF: {supplement_pages} pages.",
        f"- Main DOCX tables: {len(manuscript.tables)}.",
        f"- References: {len(reference_numbers)} listed and {len(cited)} cited.",
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
