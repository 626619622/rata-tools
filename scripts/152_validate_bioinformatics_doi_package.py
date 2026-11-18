"""Validate the DOI-complete Bioinformatics submission package."""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "submission_package_bioinformatics_final_doi"
SOURCE = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v12.md"
SOFTWARE_DOI = "10.5281/zenodo.24156617"
REGISTRY_DOI = "10.5281/zenodo.24156715"
REPORT_JSON = PACKAGE / "Submission_Check_Final.json"
REPORT_MD = PACKAGE / "Submission_Check_Final.md"


def words(text: str) -> int:
    return len(re.findall(r"\b[\w]+\b", text))


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    abstract = text.split("## Abstract", 1)[1].split("**Keywords:**", 1)[0]
    body, references = text.split("## References", 1)
    reference_entries = [
        line for line in references.splitlines() if line.strip() and not line.startswith("#")
    ]

    manuscript = Document(PACKAGE / "RATA_Bioinformatics_Manuscript.docx")
    title_page = "\n".join(p.text for p in Document(PACKAGE / "RATA_Bioinformatics_TitlePage.docx").paragraphs)
    cover = "\n".join(p.text for p in Document(PACKAGE / "RATA_Bioinformatics_CoverLetter.docx").paragraphs)
    availability = "\n".join(
        p.text for p in Document(PACKAGE / "RATA_Bioinformatics_SoftwareAvailability.docx").paragraphs
    )

    with zipfile.ZipFile(PACKAGE / "RATA_Bioinformatics_Supplementary_Code.zip") as archive:
        code_bad = archive.testzip()
        code_names = archive.namelist()
        citation = archive.read("Supplementary_Code/software/CITATION.cff").decode("utf-8")
    with zipfile.ZipFile(PACKAGE / "RATA_ACC_registry_v1.0.0.zip") as archive:
        registry_bad = archive.testzip()
        registry_names = archive.namelist()
    with zipfile.ZipFile(PACKAGE / "RATA_Bioinformatics_Submission_Package.zip") as archive:
        submission_bad = archive.testzip()

    checks = {
        "abstract_245_to_270_words": 245 <= words(abstract) <= 270,
        "author_year_style": not re.search(r"\[[0-9][0-9,\s–-]*\]", body),
        "reference_count_22": len(reference_entries) == 22,
        "software_doi_in_manuscript": SOFTWARE_DOI in text,
        "registry_doi_in_manuscript": REGISTRY_DOI in text,
        "software_doi_in_title_page": SOFTWARE_DOI in title_page,
        "registry_doi_in_title_page": REGISTRY_DOI in title_page,
        "software_doi_in_cover_letter": SOFTWARE_DOI in cover,
        "registry_doi_in_cover_letter": REGISTRY_DOI in cover,
        "software_doi_in_availability": SOFTWARE_DOI in availability,
        "registry_doi_in_availability": REGISTRY_DOI in availability,
        "doi_in_citation_cff": SOFTWARE_DOI in citation,
        "github_repository_url_present": "https://github.com/626619622/rata-tools" in text,
        "github_release_url_present": "https://github.com/626619622/rata-tools/releases/tag/v0.2.0" in text,
        "four_main_tables": all(f"### Table {n}." in text for n in range(1, 5)),
        "six_figure_legends": all(f"**Figure {number}." in text for number in range(1, 7)),
        "runtime_20k_and_5fold_k3": "20,000 features" in text and "5 folds, k=3" in text,
        "docx_has_four_tables": len(manuscript.tables) == 4,
        "main_pdf_rendered_17_pages": len(list((ROOT / "manuscript" / "render_bioinformatics_v6").glob("page-*.png"))) == 17,
        "supplementary_rendered_25_pages": len(list((ROOT / "manuscript" / "render_bioinformatics_supp").glob("page-*.png"))) == 25,
        "code_zip_integrity": code_bad is None,
        "code_zip_has_wheel": any(name.endswith("rata_tools-0.2.0-py3-none-any.whl") for name in code_names),
        "code_zip_has_tests": any(name.endswith("/tests/test_core.py") for name in code_names),
        "code_zip_has_ci": any(name.endswith("/.github/workflows/ci.yml") for name in code_names),
        "code_zip_has_doi_manifest": any(name.endswith("/RATA_Zenodo_DOIs.json") for name in code_names),
        "code_zip_has_final_source": any(name.endswith("RATA_Paper_Bioinformatics_v12.md") for name in code_names),
        "registry_zip_integrity": registry_bad is None,
        "registry_zip_has_pair_registry": "data/ACC_Provenance_Pairs_v3.csv" in registry_names,
        "submission_zip_integrity": submission_bad is None,
        "six_figure_pdfs": len(list((PACKAGE / "Figures").glob("*.pdf"))) == 6,
        "six_figure_pngs": len(list((PACKAGE / "Figures").glob("*.png"))) == 6,
    }
    report = {
        "all_checks_pass": all(checks.values()),
        "software_doi": SOFTWARE_DOI,
        "registry_doi": REGISTRY_DOI,
        "github_release": "https://github.com/626619622/rata-tools/releases/tag/v0.2.0",
        "abstract_words": words(abstract),
        "references": len(reference_entries),
        "checks": checks,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# RATA Bioinformatics final submission check",
        "",
        f"Overall: **{'PASS' if report['all_checks_pass'] else 'FAIL'}**",
        "",
        f"- Software DOI: `{SOFTWARE_DOI}`",
        f"- Registry DOI: `{REGISTRY_DOI}`",
        "- GitHub release: https://github.com/626619622/rata-tools/releases/tag/v0.2.0",
        f"- Abstract: {report['abstract_words']} words.",
        f"- Author-year references: {report['references']}.",
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
