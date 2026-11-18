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
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.family": "Arial",
    "font.size": 8,
    "axes.labelsize": 8,
    "axes.titlesize": 9,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7,
    "legend.fontsize": 7,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
})

COLORS = {
    "blue": "#4477AA",
    "orange": "#EE6677",
    "teal": "#228833",
    "purple": "#AA3377",
    "grey": "#777777",
    "gold": "#CCBB44",
}


def save(fig, stem):
    fig.tight_layout()
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight")
    fig.savefig(OUT / f"{stem}.png", dpi=300, bbox_inches="tight")
    plt.close(fig)


def fig1():
    clusters = ["ASU\nGSE19750/19776", "Michigan\nGSE10927/33371", "ENSAT\nGSE49278/49280", "Paediatric\nGSE76021"]
    counts = [4, 2, 2, 1]
    platforms = ["GPL570", "GPL570", "GPL16686", "GPL96"]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.barh(clusters[::-1], counts[::-1], color=[COLORS["grey"], COLORS["blue"], COLORS["blue"], COLORS["teal"]])
    ax.set_xlabel("Number of published signatures using the cohort cluster")
    ax.set_title("ACC external expression evidence capacity")
    ax.set_xlim(0, 4.7)
    for bar, platform in zip(bars, platforms[::-1]):
        ax.text(bar.get_width() + 0.08, bar.get_y() + bar.get_height()/2, platform, va="center", fontsize=7)
    ax.text(0.01, -0.19, "9 TCGA-involved signatures | 7 verifiable external claims | effective adult clusters 2.67", transform=ax.transAxes, fontsize=7)
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "Figure1_evidence_capacity")


def fig2():
    d = pd.read_csv(RESULTS / "RATA_v5_double_null_selection_gate.csv")
    d = d.sort_values("realistic_null_percentile")
    fig, ax = plt.subplots(figsize=(8, 4.2))
    y = np.arange(len(d))
    colors = [COLORS["blue"] if x == "pass" else COLORS["orange"] for x in d["selection_gate_decision"]]
    ax.hlines(y, 0, d["realistic_null_percentile"], color="#CCCCCC", lw=0.8)
    ax.scatter(d["realistic_null_percentile"], y, c=colors, s=32, zorder=3)
    ax.axvline(95, color="black", linestyle="--", lw=0.7)
    ax.set_yticks(y)
    ax.set_yticklabels([x.replace("_", " ") for x in d["signature"]])
    ax.set_xlim(0, 102)
    ax.set_xlabel("Observed apparent AUC percentile under realistic selection null")
    ax.set_title("Gate 1 selection robustness")
    ax.text(95.5, -0.7, "gate q95", fontsize=7)
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "Figure2_selection_gate")


def fig3():
    pairs = pd.read_csv(RESULTS / "RATA_v3_pair_registry_and_transport.csv")
    pairs = pairs[pairs["external_cohort"].isin(["TCGA", "GSE33371", "GSE19750"])].copy()
    pairs["label"] = pairs["signature"].str.replace("_", " ", regex=False) + " / " + pairs["external_cohort"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5), gridspec_kw={"width_ratios": [1.25, 1]})
    ax = axes[0]
    y = np.arange(len(pairs))
    ax.errorbar(
        pairs["cindex_did"], y,
        xerr=[pairs["cindex_did"] - pairs["cindex_did_ci_low"],
              pairs["cindex_did_ci_high"] - pairs["cindex_did"]],
        fmt="o", color=COLORS["blue"], ecolor=COLORS["grey"], capsize=2, lw=0.7, ms=4,
    )
    ax.axvline(0, color="black", lw=0.7)
    ax.set_yticks(y)
    ax.set_yticklabels(pairs["label"], fontsize=6.5)
    ax.set_xlabel("C-index difference-in-differences vs positive control")
    ax.set_title("Independent transport contrast")
    ax.spines[["top", "right"]].set_visible(False)

    role = pd.read_csv(RESULTS / "RATA_v5_ssgsea_role_aware_adjustment.csv")
    role = role.iloc[::-1]
    ax = axes[1]
    y = np.arange(len(role))
    ax.errorbar(
        role["signature_hr"], y,
        xerr=[role["signature_hr"] - role["signature_ci_low"],
              role["signature_ci_high"] - role["signature_hr"]],
        fmt="o", color=COLORS["teal"], ecolor=COLORS["grey"], capsize=2, lw=0.7, ms=4,
    )
    ax.axvline(1, color="black", lw=0.7)
    ax.set_yticks(y)
    ax.set_yticklabels([x.replace("_", " ") for x in role["model"]], fontsize=6.8)
    ax.set_xlabel("Hazard ratio (95% CI)")
    ax.set_title("ssGSEA role-aware adjustment")
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "Figure3_transport_and_role_adjustment")


def fig4():
    scores = pd.read_csv(ROOT.parent / "pituitary-project" / "results" / "GSE147786-lineage-signature-scores.csv")
    marker = pd.read_csv(RESULTS / "RATA_v5_pituitary_marker_robustness.csv")
    proxy = pd.read_csv(RESULTS / "RATA_v5_pituitary_proxy_sensitivity_models.csv")
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2), gridspec_kw={"width_ratios": [1.2, 1]})
    ax = axes[0]
    for i, group in enumerate(["GH", "NFPA"]):
        values = scores.loc[scores["lineage"] == group, "score"].to_numpy()
        x = np.full(len(values), i) + np.random.default_rng(42 + i).normal(0, 0.035, len(values))
        ax.scatter(x, values, s=17, color=COLORS["orange"] if group == "GH" else COLORS["blue"], alpha=0.85)
        ax.boxplot(values, positions=[i], widths=0.42, showfliers=False, patch_artist=True,
                   boxprops={"facecolor": "white", "linewidth": 0.6},
                   medianprops={"color": "black", "linewidth": 0.7},
                   whiskerprops={"linewidth": 0.6}, capprops={"linewidth": 0.6})
    ax.set_xticks([0, 1], ["GH", "NFPA"])
    ax.set_ylabel("Discovery-derived lineage score")
    ax.set_title("GH vs CNFPA external control (AUC 1.000)")
    ax.spines[["top", "right"]].set_visible(False)

    ax = axes[1]
    names = ["200-gene\nscore", "7-marker\nscore", "sex-residual", "PC2–PC5\nresidual"]
    vals = [1.0, float(marker["marker_external_auc"].iloc[0]), float(proxy["sex_residual_auc"].iloc[0]), float(proxy["pc234_residual_auc"].iloc[0])]
    colors = [COLORS["blue"], COLORS["teal"], COLORS["blue"], COLORS["gold"]]
    ax.bar(names, vals, color=colors, width=0.68)
    ax.axhline(0.5, color="black", linestyle="--", lw=0.6)
    ax.set_ylim(0.4, 1.03)
    ax.set_ylabel("External AUC")
    ax.set_title("Positive-control robustness")
    ax.tick_params(axis="x", rotation=25)
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "Figure4_pituitary_positive_control")


def fig5():
    d = pd.read_csv(RESULTS / "RATA_v5_joint_gate_operating_characteristics.csv")
    scenarios = ["pure_null", "confounded_only", "true_non_transport", "true_portable", "attenuated_true_effect"]
    labels = ["Null", "Confounded", "Non-transport", "Portable", "Attenuated"]
    combos = ["Gate1_only", "Gate1_plus_Gate2", "Gate1_plus_Gate2_plus_Gate3"]
    x = np.arange(len(scenarios))
    width = 0.25
    fig, ax = plt.subplots(figsize=(9, 4.3))
    palette = [COLORS["grey"], COLORS["blue"], COLORS["teal"]]
    for i, combo in enumerate(combos):
        row = d[d["gate_combination"] == combo].iloc[0]
        ax.bar(x + (i - 1) * width, [row[s] for s in scenarios], width, label=combo.replace("_", " "), color=palette[i])
    ax.set_xticks(x, labels, rotation=15)
    ax.set_ylabel("Joint pass rate")
    ax.set_ylim(0, 1.05)
    ax.set_title("Known-truth operating characteristics")
    ax.legend(frameon=False)
    ax.spines[["top", "right"]].set_visible(False)
    save(fig, "Figure5_three_gate_operating_characteristics")


if __name__ == "__main__":
    fig1()
    fig2()
    fig3()
    fig4()
    fig5()
    print("saved", OUT)
