"""Build Supplementary v3, fixing continuation labels on first pages."""

from __future__ import annotations

import importlib.util
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
BASE_SCRIPT = ROOT / "scripts" / "73_build_supplementary_v2.py"


def load_base():
    spec = importlib.util.spec_from_file_location("rata_supplementary_base", BASE_SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load supplementary builder")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def continuation(chunk_index: int, total: int) -> str:
    return f" (continued {chunk_index + 1})" if chunk_index > 0 else ""


def patched_add_text_page(base, pdf, title, text, page_counter, fontsize=7.4):
    wrapped_lines = []
    for paragraph in textwrap.dedent(text).strip().splitlines():
        if not paragraph:
            wrapped_lines.append("")
            continue
        wrapped_lines.extend(
            textwrap.wrap(
                paragraph,
                width=150,
                replace_whitespace=False,
                drop_whitespace=True,
            )
            or [""]
        )

    chunks = [wrapped_lines[i : i + 72] for i in range(0, len(wrapped_lines), 72)] or [[""]]
    for chunk_index, chunk in enumerate(chunks):
        fig, ax = plt.subplots(figsize=(11, 8.5))
        ax.axis("off")
        ax.text(
            0.045,
            0.955,
            title + continuation(chunk_index, len(chunks)),
            fontsize=13,
            fontweight="bold",
            va="top",
        )
        ax.text(
            0.045,
            0.905,
            "\n".join(chunk),
            fontsize=fontsize,
            va="top",
            family="DejaVu Sans Mono",
            linespacing=1.28,
        )
        page_counter[0] += 1
        base.footer(fig, page_counter[0])
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)


def patched_add_table_pages(
    base,
    pdf,
    title,
    frame,
    columns,
    page_counter,
    rows_per_page,
    max_colwidth=24,
    fontsize=6.2,
):
    subset = frame.loc[:, columns].copy()
    chunks = [subset.iloc[i : i + rows_per_page] for i in range(0, len(subset), rows_per_page)] or [subset]
    for chunk_index, chunk in enumerate(chunks):
        fig, ax = plt.subplots(figsize=(11, 8.5))
        ax.axis("off")
        ax.text(
            0.035,
            0.955,
            title + continuation(chunk_index, len(chunks)),
            fontsize=12.5,
            fontweight="bold",
            va="top",
        )
        ax.text(
            0.035,
            0.905,
            chunk.to_string(index=False, max_colwidth=max_colwidth),
            fontsize=fontsize,
            va="top",
            family="DejaVu Sans Mono",
            linespacing=1.18,
        )
        page_counter[0] += 1
        base.footer(fig, page_counter[0])
        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)


def main():
    base = load_base()
    base.OUT = ROOT / "manuscript" / "RATA_Paper1_Supplementary_v3.pdf"
    base.add_text_page = lambda pdf, title, text, page_counter, fontsize=7.4: patched_add_text_page(
        base, pdf, title, text, page_counter, fontsize
    )
    base.add_table_pages = (
        lambda pdf, title, frame, columns, page_counter, rows_per_page, max_colwidth=24, fontsize=6.2: patched_add_table_pages(
            base,
            pdf,
            title,
            frame,
            columns,
            page_counter,
            rows_per_page,
            max_colwidth,
            fontsize,
        )
    )
    base.main()


if __name__ == "__main__":
    main()
