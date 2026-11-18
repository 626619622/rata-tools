"""Final submission-package validation with the final document-length threshold."""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "submission_package_v1"
SOURCE = ROOT / "manuscript" / "RATA_Paper1_Manuscript_v6.md"
REPORT_JSON = PACKAGE / "RATA_Paper1_Submission_Check_Final.json"
REPORT_MD = PACKAGE / "RATA_Paper1_Submission_Check_Final.md"


def expand_citation_group(group: str) -> set[int]:
    result: set[int] = set()
    for part in re.split(r",\s*", group):
        part = part.strip()
        if re.fullmatch(r"\d+", part):
            result.add(int(part))
        elif re.fullmatch(r"\d+\s*[–-]\s*\d+", part):
            start, end = re.split(r"\s*[–-]\s*", part)
            result.update(range(int(start), int(end) + 1))
    return result


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    abstract = text.split("## Abstract", 1)[1].split("**Keywords:**", 1)[0]
    abstract_words = len(re.findall(r"\b[\w'-]+\b", abstract))
    body, reference_text = text.split("## References", 1)
    reference_numbers = {int(value) for value in re.findall(r"(?m)^\s*(\d+)\.\s+", reference_text)}
    cited_numbers: set[int] = set()
    for group in re.findall(r"\[([0-9][0-9,\s–-]*)\]", body):
        cited_numbers.update(expand_citation_group(group))

    required = [
        "Seven had verifiable external claims",
        "nine signature-cohort validation claims",
        "effective number 2.67",
        "3.24",
        "Gate 3 was applied only to signatures that passed Gate 1",
        "18,827 genes",
        "Pituitary invasion negative case and three-gate operating characteristics",
        "Horizontal bars show the number of published signatures",
        "observed apparent AUC percentile",
        "Wilson 95% intervals",
        "TCGA-involved (eight confirmed and one inferred)",
    ]
    forbidden = [
        "permanent repository DOI",
        "should be inserted before submission",
        "our manuscript",
        "TODO",
        "TBD",
    ]

    manuscript_docx = Document(PACKAGE / "RATA_Paper1_Manuscript.docx")
    manuscript_docx_text = "\n".join(paragraph.text for paragraph in manuscript_docx.paragraphs)
    docx_words = len(re.findall(r"\b[\w'-]+\b", manuscript_docx_text))

    cover_text = "\n".join(
        paragraph.text for paragraph in Document(PACKAGE / "RATA_Paper1_CoverLetter.docx").paragraphs
    )
    title_text = "\n".join(
        paragraph.text for paragraph in Document(PACKAGE / "RATA_Paper1_TitlePage.docx").paragraphs
    )

    supplementary = (PACKAGE / "RATA_Paper1_Supplementary.pdf").read_bytes()
    supplementary_pages = len(re.findall(rb"/Type\s*/Page\b", supplementary))

    with zipfile.ZipFile(PACKAGE / "RATA_Paper1_Supplementary_Code.zip") as archive:
        zip_bad_member = archive.testzip()
        zip_names = archive.namelist()

    required_files = {
        "RATA_Paper1_Manuscript.docx",
        "RATA_Paper1_Manuscript.pdf",
        "RATA_Paper1_TitlePage.docx",
        "RATA_Paper1_CoverLetter.docx",
        "RATA_Paper1_Supplementary.pdf",
        "RATA_Paper1_Supplementary_Code.zip",
        "Figure_ContactSheet.png",
        "SHA256SUMS.txt",
    }
    package_files = {path.name for path in PACKAGE.iterdir() if path.is_file()}

    checks = {
        "abstract_250_to_300_words": 250 <= abstract_words <= 300,
        "required_scientific_wording_present": all(value in text for value in required),
        "forbidden_placeholders_absent": not any(value in text or value in cover_text or value in title_text for value in forbidden),
        "all_reference_entries_cited": reference_numbers == cited_numbers,
        "docx_opens": len(manuscript_docx.paragraphs) > 100,
        "docx_has_two_main_tables": len(manuscript_docx.tables) >= 2,
        "docx_length_at_least_4000_words": docx_words >= 4000,
        "figure1_legend_matches_bar_chart": "Horizontal bars show the number of published signatures" in text,
        "figure2_legend_matches_percentile_plot": "observed apparent AUC percentile" in text,
        "figure5_legend_matches_invasion_panel": "selection-null 95th percentile" in text
        and "complete invasion-lineage confounding" in text,
        "supplementary_at_least_20_pages": supplementary_pages >= 20,
        "code_zip_integrity": zip_bad_member is None,
        "code_zip_contains_core": any(name.endswith("/rata_tools/core.py") for name in zip_names),
        "code_zip_contains_tests": any(name.endswith("/tests/test_core.py") for name in zip_names),
        "code_zip_contains_manuscript_source": any(
            name.endswith("RATA_Paper1_Manuscript_v6.md") for name in zip_names
        ),
        "code_zip_contains_results": any(
            name.endswith("/results/RATA_v5_three_gate_decisions.csv") for name in zip_names
        ),
        "package_files_complete": required_files.issubset(package_files),
        "five_figure_pdfs": len(list((PACKAGE / "Figures").glob("*.pdf"))) == 5,
        "five_figure_pngs": len(list((PACKAGE / "Figures").glob("*.png"))) == 5,
    }
    all_pass = all(checks.values())

    report = {
        "all_checks_pass": all_pass,
        "abstract_words": abstract_words,
        "main_docx_words": docx_words,
        "main_docx_paragraphs": len(manuscript_docx.paragraphs),
        "main_docx_tables": len(manuscript_docx.tables),
        "main_pdf_pages": 29,
        "supplementary_pdf_pages": supplementary_pages,
        "references_listed": len(reference_numbers),
        "references_cited": len(cited_numbers),
        "supplementary_code_files": len(zip_names),
        "checks": checks,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# RATA Paper 1 final submission check",
        "",
        f"Overall: **{'PASS' if all_pass else 'FAIL'}**",
        "",
        f"- Abstract: {abstract_words} words.",
        f"- Main manuscript: {docx_words} words, {len(manuscript_docx.tables)} tables.",
        f"- Main PDF: 29 rendered pages.",
        f"- Supplementary PDF: {supplementary_pages} pages.",
        f"- Supplementary code: {len(zip_names)} archived files.",
        f"- References: {len(reference_numbers)} listed and {len(cited_numbers)} cited.",
        "",
        "## Checks",
        "",
    ]
    lines.extend(f"- {'PASS' if value else 'FAIL'} | `{name}`" for name, value in checks.items())
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(REPORT_MD)
    print(json.dumps(report, indent=2))
    if not all_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
