from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
OUT = ROOT / "figures" / "paper1"

plt.rcParams.update({
    "font.family": "Arial",
    "font.size": 7.5,
    "axes.labelsize": 8,
    "axes.titlesize": 9,
    "axes.linewidth": 0.6,
})

BLUE = "#4477AA"
ORANGE = "#EE6677"
TEAL = "#228833"
GREY = "#777777"


invasion = json.loads(
    (RESULTS / "RATA_v5_pituitary_invasion_transport.json").read_text(
        encoding="utf-8"
    )
)
j = pd.read_csv(
    RESULTS / "RATA_v5_joint_gate_operating_characteristics.csv"
)

fig = plt.figure(figsize=(11, 8))
gs = fig.add_gridspec(2, 2, width_ratios=[1, 1.2], height_ratios=[1, 1])

ax = fig.add_subplot(gs[0, 0])
values = [
    invasion["development_auc"],
    invasion["selection_cv_auc"],
    invasion["selection_cv_null_q95"],
]
labels = ["Apparent\nAUC", "Selection-CV\nAUC", "Selection-null\nq95"]
ax.bar(labels, values, color=[ORANGE, BLUE, GREY], width=0.65)
for i, value in enumerate(values):
    ax.text(i, value + 0.02, f"{value:.3f}", ha="center", fontsize=7)
ax.set_ylim(0, 1.04)
ax.set_ylabel("AUC")
ax.set_title("Pituitary invasion: selection gate")
ax.spines[["top", "right"]].set_visible(False)

ax = fig.add_subplot(gs[0, 1])
cohort = pd.read_csv(
    RESULTS / "RATA_v5_pituitary_invasion_cohort_auc.csv"
).set_index("cohort")
external = cohort.loc[["GSE136781", "GSE260487"]]
x = np.arange(len(external))
ax.errorbar(
    x,
    external["auc"],
    yerr=[
        external["auc"] - external["auc_ci_low"],
        external["auc_ci_high"] - external["auc"],
    ],
    fmt="o",
    color=BLUE,
    ecolor=GREY,
    capsize=3,
    ms=5,
    lw=0.7,
)
ax.axhline(0.60, color="black", linestyle="--", lw=0.7)
ax.axhline(0.50, color=GREY, linestyle=":", lw=0.7)
ax.set_xticks(x, ["GSE136781\n(23/19)", "GSE260487\n(15/17)"])
ax.set_ylim(0.25, 1.02)
ax.set_ylabel("External AUC")
ax.set_title("Pituitary invasion: transport and lineage confounding")
ax.text(
    1.02,
    0.48,
    "GSE260487\nACTH-silent 15/0\nGonadotroph 0/17\nCramér's V=1",
    transform=ax.transAxes,
    fontsize=6.8,
    va="center",
)
ax.spines[["top", "right"]].set_visible(False)

ax = fig.add_subplot(gs[1, :])
scenarios = [
    "pure_null",
    "confounded_only",
    "true_non_transport",
    "true_portable",
    "attenuated_true_effect",
]
scenario_labels = ["Null", "Confounded", "Non-transport", "Portable", "Attenuated"]
combos = [
    "Gate1_only",
    "Gate1_plus_Gate2",
    "Gate1_plus_Gate2_plus_Gate3",
]
colors = [GREY, BLUE, TEAL]
x = np.arange(len(scenarios))
width = 0.25
for index, (combo, color) in enumerate(zip(combos, colors)):
    row = j[j["gate_combination"] == combo].iloc[0]
    ax.bar(
        x + (index - 1) * width,
        [row[s] for s in scenarios],
        width,
        color=color,
        label=combo.replace("_", " "),
    )
ax.set_xticks(x, scenario_labels)
ax.set_ylim(0, 1.05)
ax.set_ylabel("Joint pass rate")
ax.set_title("Known-truth three-gate operating characteristics")
ax.legend(frameon=False, ncol=3, loc="upper left")
ax.spines[["top", "right"]].set_visible(False)

fig.tight_layout()
stem = OUT / "Figure5_invasion_and_operating_characteristics_v2"
fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
fig.savefig(stem.with_suffix(".png"), dpi=300, bbox_inches="tight")
plt.close(fig)
print(stem)
