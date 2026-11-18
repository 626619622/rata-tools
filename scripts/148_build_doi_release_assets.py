"""Build final DOI-aware manuscript, admin DOCX and architecture figure."""

from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def docx_builder():
    path = ROOT / "scripts" / "64_build_submission_docx_v3.py"
    spec = importlib.util.spec_from_file_location("rata_docx_builder_doi", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load DOCX builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_manuscript():
    source_script = ROOT / "scripts" / "121_build_bioinformatics_docx_final.py"
    code = source_script.read_text(encoding="utf-8")
    code = code.replace(
        'SOURCE = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v8.md"',
        'SOURCE = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v12.md"',
        1,
    ).replace(
        'OUTPUT = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v5.docx"',
        'OUTPUT = ROOT / "manuscript" / "RATA_Paper_Bioinformatics_v8.docx"',
        1,
    )
    namespace = {"__file__": str(source_script), "__name__": "rata_docx_doi"}
    exec(compile(code, str(source_script), "exec"), namespace)
    namespace["main"]()


def build_admin():
    builder = docx_builder()
    manuscript = ROOT / "manuscript"
    for name in [
        "RATA_Bioinformatics_TitlePage_v3",
        "RATA_Bioinformatics_CoverLetter_v3",
        "RATA_Bioinformatics_SoftwareAvailability_v3",
    ]:
        builder.add_markdown_docx(
            manuscript / f"{name}.md",
            manuscript / f"{name}.docx",
            manuscript=False,
        )


def build_figure():
    source_script = ROOT / "scripts" / "81_make_software_architecture_figure.py"
    code = source_script.read_text(encoding="utf-8")
    code = code.replace(
        'OUT = ROOT / "figures" / "bioinformatics"',
        'OUT = ROOT / "figures" / "bioinformatics_v4"',
        1,
    ).replace(
        '"Python package | CLI | dataclasses | JSON-ready records"',
        '"github.com/626619622/rata-tools"',
        1,
    ).replace(
        '"pip install <included-wheel> | tests | CI | MIT license"',
        '"DOI 10.5281/zenodo.24156617 | tests | CI | MIT license"',
        1,
    )
    namespace = {"__file__": str(source_script), "__name__": "rata_arch_v4"}
    exec(compile(code, str(source_script), "exec"), namespace)
    namespace["main"]()


if __name__ == "__main__":
    build_manuscript()
    build_admin()
    build_figure()
