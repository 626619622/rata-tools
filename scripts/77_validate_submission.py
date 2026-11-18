"""Validate the final Paper 1 submission package."""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "submission_package_v1"
MANUSCRIPT_MD = ROOT / "manuscript" / "RATA_Paper1_Manuscript_v6.md"
REPORT_JSON = PACKAGE / "RATA_Paper1_Submission_Check.json"
REPORT_MD = PACKAGE / "RATA_Paper1_Submission_Check.md"


def parse_citations(text: str) -> set[int]:
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
    text = MANUSCRIPT_MD.read_text(encoding="utf-8")
    abstract = text.split("## Abstract", 1)[1].split("**Keywords:**", 1)[0]
    abstract_words = len(re.findall(r"\b[\w'-]+\b", abstract))
    body, references = text.split("## References", 1)
    reference_numbers = {
        int(number)
        for number in re.findall(r"(?m)^\s*(\d+)\.\s+", references)
    }
    cited = parse_citations(body)

    required_phrases = {
        "seven_signatures_nine_claims": "Seven had verifiable external claims",
        "adult_effective_number": "effective number 2.67",
        "all_reported_effective_number": "3.24",
        "gate3_scope": "Gate 3 was applied only to signatures that passed Gate 1",
        "invasion_candidate_pool": "18,827 genes",
        "figure5_invasion": "Pituitary invasion negative case and three-gate operating characteristics",
        "figure1_bar_chart": "Horizontal bars show the number of published signatures",
        "figure2_percentile": "observed apparent AUC percentile",
        "table2_wilson": "Wilson 95% intervals",
    }

    checks = {
        "abstract_word_count_250_to_300": 250 <= abstract_words <= 300,
        "all_required_phrases_present": all(phrase in text for phrase in required_phrases.values()),
        "no_repository_placeholder": not any(
            phrase in text
            for phrase in [
                "permanent repository DOI",
                "should be inserted before submission",
                "TODO",
                "TBD",
            ]
        ),
        "all_references_cited": not (reference_numbers - cited),
        "no_missing_reference_targets": not (cited - reference_numbers),
        "figure1_legend_matches_chart": "[Fig. 1]" if False else "Horizontal bars show the number of published signatures" in text,
        "figure5_legend_matches_v2": "selection-null 95th percentile" in text
        and "complete invasion-lineage confounding" in text,
    }

    docx_path = PACKAGE / "RATA_Paper1_Manuscript.docx"
    document = Document(docx_path)
    docx_text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    docx_words = len(re.findall(r"\b[\w'-]+\b", docx_text))
    checks.update(
        {
            "docx_opens": True,
            "docx_paragraphs_at_least_100": len(document.paragraphs) >= 100,
            "docx_tables_at_least_2": len(document.tables) >= 2,
            "docx_words_at_least_5000": docx_words >= 5000,
        }
    )

    supp = PACKAGE / "RATA_Paper1_Supplementary.pdf"
    supp_bytes = supp.read_bytes()
    supp_pages = len(re.findall(rb"/Type\s*/Page\b", supp_bytes))
    checks["supplementary_pdf_at_least_20_pages"] = supp_pages >= 20

    code_zip = PACKAGE / "RATA_Paper1_Supplementary_Code.zip"
    with zipfile.ZipFile(code_zip) as archive:
        bad_member = archive.testzip()
        names = set(archive.namelist())
    checks.update(
        {
            "code_zip_integrity": bad_member is None,
            "code_zip_has_core": any(name.endswith("/rata_tools/core.py") for name in names),
            "code_zip_has_tests": any(name.endswith("/tests/test_core.py") for name in names),
            "code_zip_has_manuscript": any(name.endswith("RATA_Paper1_Manuscript_v6.md") for name in names),
            "code_zip_has_results": any("/results/RATA_v5_three_gate_decisions.csv" in name for name in names),
        }
    )

    expected_package_files = {
        "RATA_Paper1_Manuscript.docx",
        "RATA_Paper1_Manuscript.pdf",
        "RATA_Paper1_TitlePage.docx",
        "RATA_Paper1_CoverLetter.docx",
        "RATA_Paper1_Supplementary.pdf",
        "RATA_Paper1_Supplementary_Code.zip",
        "Figure_ContactSheet.png",
        "SHA256SUMS.txt",
    }
    actual_package_files = {path.name for path in PACKAGE.iterdir() if path.is_file()}
    checks["package_required_files_present"] = expected_package_files.issubset(actual_package_files)
    checks["package_figure_pdf_count"] = len(list((PACKAGE / "Figures").glob("*.pdf"))) == 5
    checks["package_figure_png_count"] = len(list((PACKAGE / "Figures").glob("*.png"))) == 5

    report = {
        "all_checks_pass": all(value for value in checks.values() if isinstance(value, bool)),
        "abstract_words": abstract_words,
        "reference_numbers": sorted(reference_numbers),
        "cited_numbers": sorted(cited),
        "docx_words": docx_words,
        "docx_paragraphs": len(document.paragraphs),
        "docx_tables": len(document.tables),
        "supplementary_pdf_pages": supp_pages,
        "code_zip_members": len(names),
        "checks": checks,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# RATA Paper 1 submission check",
        "",
        f"- All checks pass: **{report['all_checks_pass']}**",
        f"- Abstract: {abstract_words} words",
        f"- References: {len(reference_numbers)} listed; {len(cited)} cited",
        f"- Main DOCX: {docx_words} words, {len(document.paragraphs)} paragraphs, {len(document.tables)} tables",
        f"- Supplementary PDF: {supp_pages} pages",
        f"- Supplementary code archive: {len(names)} files",
        "",
        "## Check results",
        "",
    ]
    lines.extend(f"- {'PASS' if value else 'FAIL'}: {key}" for key, value in checks.items() if isinstance(value, bool))
    lines.append(f"- Figure PDFs: {checks['package_figure_pdf_count']}/5")
    lines.append(f"- Figure PNGs: {checks['package_figure_png_count']}/5")
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(REPORT_MD)
    print(json.dumps(report, indent=2))
    if not report["all_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
