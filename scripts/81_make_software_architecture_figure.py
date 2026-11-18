"""Create the RATA software architecture figure in vector and raster formats."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "figures" / "bioinformatics"
OUT.mkdir(parents=True, exist_ok=True)


COLORS = {
    "input": "#D9EAF7",
    "module": "#E6F2E6",
    "decision": "#F5E6CC",
    "software": "#EEE4F2",
    "edge": "#3C3C3C",
}


def box(ax, x, y, w, h, title, body, color, title_size=8.5, body_size=7.2):
    patch = FancyBboxPatch(
        (x, y),
        w,
        h,
        boxstyle="round,pad=0.012,rounding_size=0.02",
        linewidth=0.7,
        edgecolor=COLORS["edge"],
        facecolor=color,
    )
    ax.add_patch(patch)
    ax.text(x + 0.015, y + h - 0.045, title, fontsize=title_size, fontweight="bold", va="top")
    ax.text(x + 0.015, y + h - 0.105, body, fontsize=body_size, va="top", linespacing=1.25)


def arrow(ax, start, end):
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=10,
            linewidth=0.7,
            color=COLORS["edge"],
            shrinkA=2,
            shrinkB=2,
        )
    )


def main() -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 8,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )
    fig, ax = plt.subplots(figsize=(9, 5.6))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.015, 0.965, "Inputs", fontsize=9, fontweight="bold", va="top")
    box(
        ax,
        0.02,
        0.69,
        0.20,
        0.20,
        "Provenance registry",
        "signature x cohort\nreuse family, platform,\nendpoint, events, grade",
        COLORS["input"],
    )
    box(
        ax,
        0.02,
        0.43,
        0.20,
        0.20,
        "Expression and outcomes",
        "matrix, score, binary label,\ntime, event, cohort",
        COLORS["input"],
    )
    box(
        ax,
        0.02,
        0.17,
        0.20,
        0.20,
        "Role specification",
        "target, confounder,\nmediator, no-adjust axes",
        COLORS["input"],
    )

    ax.text(0.285, 0.965, "Audit primitives", fontsize=9, fontweight="bold", va="top")
    box(
        ax,
        0.27,
        0.70,
        0.29,
        0.18,
        "Evidence capacity",
        "effective cluster number\nevent capacity, platform diversity",
        COLORS["module"],
    )
    box(
        ax,
        0.27,
        0.47,
        0.29,
        0.18,
        "Gate 1 | Selection",
        "selection-CV AUC\nmatched pure/realistic null decision",
        COLORS["module"],
    )
    box(
        ax,
        0.27,
        0.24,
        0.29,
        0.18,
        "Gate 2 | Transport",
        "binary or cohort-stratified Cox\nHR, Q, I-squared, instability",
        COLORS["module"],
    )
    box(
        ax,
        0.27,
        0.02,
        0.29,
        0.17,
        "Gate 3 | Role-aware audit",
        "target, confounder and mediator\nmust be specified before adjustment",
        COLORS["module"],
    )

    ax.text(0.61, 0.965, "Structured outputs", fontsize=9, fontweight="bold", va="top")
    box(
        ax,
        0.60,
        0.70,
        0.36,
        0.18,
        "Capacity vector",
        "claims, independent clusters,\neffective number, total/independent events,\nplatform count",
        COLORS["decision"],
    )
    box(
        ax,
        0.60,
        0.44,
        0.36,
        0.20,
        "Gate decisions",
        "SelectionDecision\nbinary/multi-cohort transport record\nsurvival transport record",
        COLORS["decision"],
    )
    box(
        ax,
        0.60,
        0.18,
        0.36,
        0.20,
        "GateDecision",
        "separate gate1, gate2 and gate3 fields\nprovisional and indeterminate are not\ncollapsed into failure",
        COLORS["decision"],
    )

    arrow(ax, (0.22, 0.79), (0.27, 0.79))
    arrow(ax, (0.22, 0.53), (0.27, 0.56))
    arrow(ax, (0.22, 0.27), (0.27, 0.32))
    arrow(ax, (0.56, 0.57), (0.60, 0.53))
    arrow(ax, (0.56, 0.34), (0.60, 0.29))
    arrow(ax, (0.56, 0.79), (0.60, 0.79))

    ax.text(0.60, 0.115, "Python package | CLI | dataclasses | JSON-ready records", fontsize=8, fontweight="bold")
    ax.text(
        0.60,
        0.085,
        "pip install rata-tools | tests | CI | MIT license",
        fontsize=7.2,
    )

    fig.tight_layout(pad=0.2)
    fig.savefig(OUT / "Figure1_software_architecture.pdf", bbox_inches="tight")
    fig.savefig(OUT / "Figure1_software_architecture.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(OUT / "Figure1_software_architecture.pdf")
    print(OUT / "Figure1_software_architecture.png")


if __name__ == "__main__":
    main()
