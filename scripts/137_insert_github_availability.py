"""Insert the public GitHub and release URLs into submission documents."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript"
REPO_URL = "https://github.com/626619622/rata-tools"
RELEASE_URL = "https://github.com/626619622/rata-tools/releases/tag/v0.2.0"
WHEEL_URL = (
    "https://github.com/626619622/rata-tools/releases/download/v0.2.0/"
    "rata_tools-0.2.0-py3-none-any.whl"
)


def main() -> None:
    text = (MANUSCRIPT / "RATA_Paper_Bioinformatics_v10.md").read_text(encoding="utf-8")
    availability = (
        f"`rata-tools` 0.2.0 is publicly available at {REPO_URL}, with versioned "
        f"release assets at {RELEASE_URL}. The release provides a Python API, "
        "command-line interface, examples, tests, MIT license and "
        "continuous-integration configuration. The included wheel can be "
        f"installed directly from {WHEEL_URL}. The manuscript's Supplementary "
        "Code contains the package source, API documentation, vignette, analysis "
        "scripts and result tables. Public expression and clinical data are "
        "available from TCGA and NCBI GEO under the accessions listed in the "
        "manuscript and pair-level registry. No controlled-access data were used."
    )
    start = text.index("## Availability")
    end = text.index("## Tables", start)
    text = text[:start] + "## Availability\n\n" + availability + "\n\n" + text[end:]
    (MANUSCRIPT / "RATA_Paper_Bioinformatics_v11.md").write_text(text, encoding="utf-8")

    title = (MANUSCRIPT / "RATA_Bioinformatics_TitlePage_v1.md").read_text(encoding="utf-8")
    title = title.replace(
        "**Data and code:** `rata-tools` 0.2.0, source code, wheel, examples, tests, CI configuration and analysis scripts are supplied in the Supplementary Code. Public data accessions are listed in the manuscript and pair-level registry.",
        f"**Data and code:** `rata-tools` 0.2.0 is publicly available at {REPO_URL}. Release assets are at {RELEASE_URL}. Source code, wheel, examples, tests, CI configuration and analysis scripts are also supplied in the Supplementary Code. Public data accessions are listed in the manuscript and pair-level registry.",
        1,
    )
    (MANUSCRIPT / "RATA_Bioinformatics_TitlePage_v2.md").write_text(title, encoding="utf-8")

    software = (MANUSCRIPT / "RATA_Bioinformatics_SoftwareAvailability.md").read_text(encoding="utf-8")
    software = software.replace(
        "The Supplementary Code archive is the versioned release candidate for\neditorial and peer review. A permanent repository identifier must be added\nonly after the author creates the GitHub/Zenodo deposit and receives a real\nDOI.",
        f"**Public repository:** {REPO_URL}\n\n**Versioned release:** {RELEASE_URL}\n\n"
        f"**Direct wheel installation:** `pip install {WHEEL_URL}`\n\n"
        "The GitHub release is public and versioned. A Zenodo DOI has not yet been "
        "issued; it should be inserted only after the Zenodo archive is created.",
        1,
    )
    (MANUSCRIPT / "RATA_Bioinformatics_SoftwareAvailability_v2.md").write_text(
        software, encoding="utf-8"
    )

    cover = (MANUSCRIPT / "RATA_Bioinformatics_CoverLetter_v1.md").read_text(encoding="utf-8")
    insertion = (
        f"The software is publicly available at {REPO_URL}, with a versioned "
        f"release at {RELEASE_URL}. The release includes the wheel, source "
        "archive, tests, documentation and CI evidence.\n\n"
    )
    marker = "Computational validation uses three complementary sources."
    if marker not in cover:
        raise ValueError("Cover-letter insertion marker not found")
    cover = cover.replace(marker, insertion + marker, 1)
    (MANUSCRIPT / "RATA_Bioinformatics_CoverLetter_v2.md").write_text(cover, encoding="utf-8")

    print(MANUSCRIPT / "RATA_Paper_Bioinformatics_v11.md")
    print(MANUSCRIPT / "RATA_Bioinformatics_TitlePage_v2.md")
    print(MANUSCRIPT / "RATA_Bioinformatics_CoverLetter_v2.md")
    print(MANUSCRIPT / "RATA_Bioinformatics_SoftwareAvailability_v2.md")


if __name__ == "__main__":
    main()
