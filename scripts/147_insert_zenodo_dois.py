"""Insert the published software and registry DOIs into final documents."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANUSCRIPT = ROOT / "manuscript"
SOFTWARE_DOI = "10.5281/zenodo.24156617"
REGISTRY_DOI = "10.5281/zenodo.24156715"


def main() -> None:
    text = (MANUSCRIPT / "RATA_Paper_Bioinformatics_v11.md").read_text(encoding="utf-8")
    start = text.index("## Availability")
    end = text.index("## Tables", start)
    availability = (
        "`rata-tools` 0.2.0 is publicly available at "
        "https://github.com/626619622/rata-tools, with versioned release assets at "
        "https://github.com/626619622/rata-tools/releases/tag/v0.2.0. "
        f"The archived software is available at https://doi.org/{SOFTWARE_DOI}. "
        f"The ACC provenance registry is archived at https://doi.org/{REGISTRY_DOI}. "
        "The release provides a Python API, command-line interface, examples, tests, "
        "MIT license and continuous-integration configuration. The wheel can be installed "
        "from https://github.com/626619622/rata-tools/releases/download/v0.2.0/"
        "rata_tools-0.2.0-py3-none-any.whl. Public expression and clinical data are "
        "available from TCGA and NCBI GEO under the accessions listed in the manuscript "
        "and pair-level registry. No controlled-access data were used."
    )
    text = text[:start] + "## Availability\n\n" + availability + "\n\n" + text[end:]
    (MANUSCRIPT / "RATA_Paper_Bioinformatics_v12.md").write_text(text, encoding="utf-8")

    title = (MANUSCRIPT / "RATA_Bioinformatics_TitlePage_v2.md").read_text(encoding="utf-8")
    title = title.replace(
        "Release assets are at https://github.com/626619622/rata-tools/releases/tag/v0.2.0.",
        (
            "Release assets are at https://github.com/626619622/rata-tools/releases/tag/v0.2.0. "
            f"Software DOI: {SOFTWARE_DOI}. Registry DOI: {REGISTRY_DOI}."
        ),
        1,
    )
    (MANUSCRIPT / "RATA_Bioinformatics_TitlePage_v3.md").write_text(title, encoding="utf-8")

    software = (MANUSCRIPT / "RATA_Bioinformatics_SoftwareAvailability_v2.md").read_text(encoding="utf-8")
    software = software.replace(
        "The GitHub release is public and versioned. A Zenodo DOI has not yet been issued; it should be inserted only after the Zenodo archive is created.",
        (
            "The GitHub release is public and versioned. "
            f"The software archive DOI is {SOFTWARE_DOI}. "
            f"The ACC registry DOI is {REGISTRY_DOI}."
        ),
        1,
    )
    (MANUSCRIPT / "RATA_Bioinformatics_SoftwareAvailability_v3.md").write_text(
        software, encoding="utf-8"
    )

    cover = (MANUSCRIPT / "RATA_Bioinformatics_CoverLetter_v2.md").read_text(encoding="utf-8")
    cover = cover.replace(
        "The release includes the wheel, source archive, tests, documentation and CI evidence.",
        (
            "The release includes the wheel, source archive, tests, documentation and CI evidence. "
            f"The software archive has DOI {SOFTWARE_DOI}; the ACC registry has DOI {REGISTRY_DOI}."
        ),
        1,
    )
    (MANUSCRIPT / "RATA_Bioinformatics_CoverLetter_v3.md").write_text(cover, encoding="utf-8")

    citation = f"""cff-version: 1.2.0
message: "Cite this software using the metadata below."
title: "rata-tools: Role-Aware Transportability Audit primitives"
type: software
authors:
  - family-names: Zhao
    given-names: Jiakang
    affiliation: "Zhongda Hospital, Southeast University"
    orcid: "https://orcid.org/0009-0006-4878-0626"
version: 0.2.0
date-released: "2026-11-12"
license: MIT
doi: "{SOFTWARE_DOI}"
url: "https://github.com/626619622/rata-tools/releases/tag/v0.2.0"
abstract: >-
  Reusable primitives for selection-aware, transportability and role-aware
  auditing of transcriptomic signatures.
"""
    (ROOT / "release_artifacts" / "CITATION_v0.2.0_with_doi.cff").write_text(
        citation, encoding="utf-8"
    )


if __name__ == "__main__":
    main()
