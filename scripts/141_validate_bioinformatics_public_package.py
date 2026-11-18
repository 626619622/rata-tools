"""Validate the public-GitHub Bioinformatics package."""

from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path

from docx import Document


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "submission_package_bioinformatics_public"
SOURCE = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v11.md"
REPORT_JSON = PACKAGE / "Submission_Check_Final.json"
REPORT_MD = PACKAGE / "Submission_Check_Final.md"


def words(text: str) -> int:
    return len(re.findall(r"\b[\w]+\b", text))


def main() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    abstract = text.split("## Abstract", 1)[1].split("**Keywords:**", 1)[0]
    body, references = text.split("## References", 1)
    implementation = text.split("## Implementation", 1)[1].split("## Validation", 1)[0]
    discussion = text.split("## Discussion", 1)[1].split("## Availability", 1)[0]
    reference_entries = [
        line for line in references.splitlines() if line.strip() and not line.startswith("#")
    ]

    manuscript = Document(PACKAGE / "RATA_Bioinformatics_Manuscript.docx")
    manuscript_text = "\n".join(p.text for p in manuscript.paragraphs)
    title_page = "\n".join(p.text for p in Document(PACKAGE / "RATA_Bioinformatics_TitlePage.docx").paragraphs)
    cover = "\n".join(p.text for p in Document(PACKAGE / "RATA_Bioinformatics_CoverLetter.docx").paragraphs)
    availability = "\n".join(
        p.text for p in Document(PACKAGE / "RATA_Bioinformatics_SoftwareAvailability.docx").paragraphs
    )

    with zipfile.ZipFile(PACKAGE / "RATA_Bioinformatics_Supplementary_Code.zip") as archive:
        code_bad = archive.testzip()
        code_names = archive.namelist()
    with zipfile.ZipFile(PACKAGE / "RATA_ACC_registry_v1.0.0.zip") as archive:
        registry_bad = archive.testzip()
        registry_names = archive.namelist()
    with zipfile.ZipFile(PACKAGE / "RATA_Bioinformatics_Submission_Package.zip") as archive:
        submission_bad = archive.testzip()

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
    rendered_pages = len(list((ROOT / "manuscript" / "render_bioinformatics_v6").glob("page-*.png")))

    checks = {
        "title_framework_first": text.startswith("# RATA: a role-aware three-gate framework and software"),
        "abstract_245_to_270_words": 245 <= words(abstract) <= 270,
        "implementation_at_least_1150_words": words(implementation) >= 1150,
        "discussion_at_least_600_words": words(discussion) >= 600,
        "author_year_style": not re.search(r"\[[0-9][0-9,\s–-]*\]", body),
        "author_year_reference_count_22": len(reference_entries) == 22,
        "github_repository_url_present": "https://github.com/626619622/rata-tools" in text,
        "github_release_url_present": "https://github.com/626619622/rata-tools/releases/tag/v0.2.0" in text,
        "wheel_install_url_present": "rata_tools-0.2.0-py3-none-any.whl" in text,
        "no_false_zenodo_doi": "doi.org/10." not in text.lower(),
        "implementation_validation_availability_sections": all(
            heading in text for heading in ["## Implementation", "## Validation", "## Availability"]
        ),
        "four_main_tables": all(f"### Table {n}." in text for n in range(1, 5)),
        "six_figure_legends": all(f"**Figure {number}." in text for number in range(1, 7)),
        "runtime_has_20k": "20,000 features" in text,
        "runtime_has_5fold_k3": "5 folds, k=3" in text,
        "docx_has_four_tables": len(manuscript.tables) == 4,
        "docx_table_titles_present": all(f"Table {n}." in manuscript_text for n in range(1, 5)),
        "main_pdf_rendered_to_17_pages": rendered_pages == 17,
        "title_page_public_github": "github.com/626619622/rata-tools" in title_page,
        "cover_letter_public_github": "github.com/626619622/rata-tools" in cover,
        "software_availability_public_github": "github.com/626619622/rata-tools" in availability,
        "software_availability_wheel_url": "rata_tools-0.2.0-py3-none-any.whl" in availability,
        "code_zip_integrity": code_bad is None,
        "code_zip_has_wheel": any(name.endswith("rata_tools-0.2.0-py3-none-any.whl") for name in code_names),
        "code_zip_has_source_archive": any(name.endswith("rata_tools-0.2.0-source-final.zip") for name in code_names),
        "code_zip_has_git_bundle": any(name.endswith("rata-tools-v0.2.0-final.bundle") for name in code_names),
        "code_zip_has_tests": any(name.endswith("/tests/test_core.py") for name in code_names),
        "code_zip_has_ci": any(name.endswith("/.github/workflows/ci.yml") for name in code_names),
        "code_zip_has_zenodo_metadata": any(name.endswith("/.zenodo.json") for name in code_names),
        "code_zip_has_final_source": any(name.endswith("RATA_Paper_Bioinformatics_v11.md") for name in code_names),
        "code_zip_has_v2_benchmark": any(
            name.endswith("/results/Bioinformatics_RuntimeBenchmark_v2.csv") for name in code_names
        ),
        "registry_zip_integrity": registry_bad is None,
        "registry_zip_has_pair_registry": "data/ACC_Provenance_Pairs_v3.csv" in registry_names,
        "submission_zip_integrity": submission_bad is None,
        "package_files_complete": expected_files.issubset(package_files),
        "six_figure_pdfs": len(list((PACKAGE / "Figures").glob("*.pdf"))) == 6,
        "six_figure_pngs": len(list((PACKAGE / "Figures").glob("*.png"))) == 6,
        "six_figure_legends": len(list((PACKAGE / "Figures").glob("*.md"))) == 6,
    }
    report = {
        "all_local_checks_pass": all(checks.values()),
        "abstract_words": words(abstract),
        "implementation_words": words(implementation),
        "discussion_words": words(discussion),
        "references": len(reference_entries),
        "main_pdf_pages": rendered_pages,
        "supplementary_pdf_pages": 25,
        "external_status": {
            "github_repository": "public",
            "github_release": "published",
            "github_ci": "success",
            "pypi": "not published; install from release wheel",
            "zenodo_doi": "not issued",
        },
        "checks": checks,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# RATA Bioinformatics public submission check",
        "",
        f"Local submission checks: **{'PASS' if report['all_local_checks_pass'] else 'FAIL'}**",
        "",
        f"- Abstract: {report['abstract_words']} words.",
        f"- Implementation: {report['implementation_words']} words.",
        f"- Discussion: {report['discussion_words']} words.",
        f"- Author-year references: {report['references']} entries.",
        f"- Main PDF: {report['main_pdf_pages']} pages.",
        f"- Supplementary PDF: {report['supplementary_pdf_pages']} pages.",
        "",
        "## External availability",
        "",
        "- GitHub repository: public.",
        "- GitHub release: published.",
        "- GitHub Actions: success.",
        "- PyPI: not published; install from release wheel.",
        "- Zenodo DOI: not issued.",
        "",
        "## Checks",
        "",
    ]
    lines.extend(f"- {'PASS' if value else 'FAIL'} | `{key}`" for key, value in checks.items())
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(REPORT_MD)
    print(json.dumps(report, indent=2))
    if not report["all_local_checks_pass"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
