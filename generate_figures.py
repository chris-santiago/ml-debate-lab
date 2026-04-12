# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib", "numpy"]
# ///
"""
Generate figures for WORKING_PAPER.md.
All numbers sourced directly from v6_hypothesis_results.json and ENSEMBLE_ANALYSIS.md §8.
"""

import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from pathlib import Path

# ── Load source data ──────────────────────────────────────────────────────────
with open("experiments/self_debate_experiment_v6/v6_hypothesis_results.json") as f:
    results = json.load(f)

desc = results["descriptive"]

# Conditions for main figures — compute-ordered: 1× → 3× (debate variants then ensemble) → ~5×
# (conditional_fm excluded — n_regular=8, not comparable)
CONDITIONS = ["baseline", "isolated_debate", "biased_debate", "ensemble_3x", "multiround"]
LABELS = ["Baseline\n(1×)", "Isolated\nDebate\n(3×)", "Biased\nDebate\n(3×)", "Ensemble\n3×\n(3×)", "Multiround\n(~5×)"]

out_dir = Path("figures")
out_dir.mkdir(exist_ok=True)

# Shared color constants (mirrors Figure 3 palette)
BAR_COLOR   = "#2c7bb6"   # teal — standard conditions
ENS_COLOR   = "#e08214"   # amber — ensemble_3x (same as RC series in Figure 3)
ENS_IDX     = 3           # ensemble_3x position in compute-ordered list

# ── Figure 1: IDR bar chart ───────────────────────────────────────────────────
idr_vals = [desc[c]["dim_means_regular"]["IDR"] for c in CONDITIONS]
bar_colors = [ENS_COLOR if i == ENS_IDX else BAR_COLOR for i in range(len(CONDITIONS))]

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(range(len(CONDITIONS)), idr_vals, color=bar_colors, width=0.6,
              edgecolor="white", linewidth=1.2)

# Value labels on bars
for i, (bar, val) in enumerate(zip(bars, idr_vals)):
    ax.text(bar.get_x() + bar.get_width() / 2, val + 0.008,
            f"{val:.3f}", ha="center", va="bottom",
            fontsize=9, fontweight="bold" if i == ENS_IDX else "normal")

# Ensemble annotation box (matches Figure 3 style)
ens_x = ENS_IDX
ax.text(
    ens_x, idr_vals[ENS_IDX] + 0.055,
    "★ Best condition\nat matched compute",
    ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#222222",
    bbox=dict(boxstyle="round,pad=0.3", facecolor="#fff9c4", edgecolor="#c8a000", linewidth=1.2),
)

ax.set_xticks(range(len(CONDITIONS)))
ax.set_xticklabels(LABELS, fontsize=9)
ax.set_ylabel("Issue Detection Recall (IDR)", fontsize=11)
ax.set_title("Figure 1. IDR by Condition — Regular Cases (n = 80)\n"
             "Paired bootstrap; all conditions use 3× compute except Baseline (1×) and Multiround (~5×)",
             fontsize=10)
ax.set_ylim(0, 0.96)
ax.axhline(idr_vals[0], color="#888888", linestyle="--", linewidth=0.8, alpha=0.6,
           label=f"Baseline IDR = {idr_vals[0]:.4f}")
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend(fontsize=8, framealpha=0.5)

plt.tight_layout()
plt.savefig(out_dir / "figure1_idr_by_condition.pdf", bbox_inches="tight")
plt.savefig(out_dir / "figure1_idr_by_condition.png", dpi=150, bbox_inches="tight")
plt.close()
print("Figure 1 saved.")

# ── Figure 2: 2×2 convergent/divergent matrix ────────────────────────────────
# Cells: (task type) × (method)
# Primary metric per cell sourced from paper
#   Divergent/Ensemble: IDR ensemble=0.7717, debate=0.6603 (H2 regular FAIL, ensemble superior)
#   Divergent/Debate:   IDR debate=0.6603 (not significantly diff from baseline 0.6712)
#   Convergent/Ensemble: FVC_mixed=0.025 (near-floor; structurally bounded)
#   Convergent/Debate:  FVC_mixed multiround=0.3667

fig, ax = plt.subplots(figsize=(7, 5))
ax.set_xlim(0, 2)
ax.set_ylim(0, 2)
ax.axis("off")

cell_data = [
    # (col, row, title, metric_line, verdict, bg_color)
    (0, 1, "Divergent detection\n(find all flaws)",
     "Ensemble 3×", "IDR = 0.7717", "H2: ensemble > debate\nCI [−0.0434, −0.0154]",
     "#e5f5e0"),
    (1, 1, "Divergent detection\n(find all flaws)",
     "Isolated Debate (3×)", "IDR = 0.6603", "≈ baseline (CI spans zero)\n3× compute, no recall gain",
     "#fee0d2"),
    (0, 0, "Convergent judgment\n(assess testability)",
     "Ensemble 3×", "FVC_mixed = 0.025", "Near-floor;\nbinary verdicts cannot\nproduce ambiguity resolution",
     "#fee0d2"),
    (1, 0, "Convergent judgment\n(assess testability)",
     "Multiround (~5×)", "FVC_mixed = 0.3667", "Best condition;\niterative exchange required\nfor empirical_test_agreed",
     "#e5f5e0"),
]

col_labels = ["Ensemble / Independent", "Debate / Adversarial"]
row_labels = ["Divergent\nDetection", "Convergent\nJudgment"]

# Draw cells
for col, row, _, method, metric, verdict, bg in cell_data:
    rect = mpatches.FancyBboxPatch((col + 0.04, row + 0.04), 0.92, 0.92,
                                    boxstyle="round,pad=0.02",
                                    facecolor=bg, edgecolor="#aaaaaa", linewidth=1.2)
    ax.add_patch(rect)
    cx, cy = col + 0.5, row + 0.5
    ax.text(cx, cy + 0.30, method, ha="center", va="center", fontsize=9, fontweight="bold")
    ax.text(cx, cy + 0.10, metric, ha="center", va="center", fontsize=10,
            color="#1a1a1a", fontweight="bold")
    ax.text(cx, cy - 0.18, verdict, ha="center", va="center", fontsize=7.5,
            color="#444444", linespacing=1.4)

# Column headers
for i, lbl in enumerate(col_labels):
    ax.text(i + 0.5, 2.08, lbl, ha="center", va="bottom", fontsize=10, fontweight="bold")

# Row headers (left side)
for i, lbl in enumerate(reversed(row_labels)):
    ax.text(-0.04, i + 0.5, lbl, ha="right", va="center", fontsize=9,
            fontweight="bold", rotation=0)

ax.set_title("Figure 2. Convergent/Divergent Task-Type Interaction\n"
             "Green = method wins; Red = method fails. Post-hoc framework — not pre-registered.",
             fontsize=9, pad=14)

plt.tight_layout()
plt.savefig(out_dir / "figure2_task_type_matrix.pdf", bbox_inches="tight")
plt.savefig(out_dir / "figure2_task_type_matrix.png", dpi=150, bbox_inches="tight")
plt.close()
print("Figure 2 saved.")

# ── Figure 3: RC-stratified IDR ───────────────────────────────────────────────
# Data from ENSEMBLE_ANALYSIS.md §8 (verified against session read)
# Sorted by compute budget: 1× → 3× (debate variants, then ensemble) → ~5×
# Within 3×: debate conditions first, ensemble last — tells the "ensemble wins at matched compute" story
data_fig3 = [
    # (condition_label, rc_idr, synth_idr)
    ("Baseline\n(1×)",         0.2828, 0.8961),
    ("Isolated\nDebate (3×)",  0.2702, 0.8861),
    ("Biased\nDebate (3×)",    0.3460, 0.8978),
    ("Ensemble 3×\n(3×)",      0.4545, 0.9553),  # 3× winner — rightmost among 3× group
    ("Multiround\n(~5×)",      0.3005, 0.8560),
]
labels_fig3 = [d[0] for d in data_fig3]
rc_idr     = [d[1] for d in data_fig3]
synth_idr  = [d[2] for d in data_fig3]
ens_idx    = 3  # ensemble_3x position in compute-ordered list

# Distinct colors: amber for RC, teal for synthetic
RC_COLOR    = "#e08214"   # amber/orange — clearly different from teal
SYNTH_COLOR = "#2c7bb6"   # teal/medium blue

x = np.arange(len(data_fig3))
width = 0.35

fig, ax = plt.subplots(figsize=(9, 5.2))
b1 = ax.bar(x - width / 2, rc_idr,    width, label="Real papers (RC, n=25)",
            color=RC_COLOR, edgecolor="white")
b2 = ax.bar(x + width / 2, synth_idr, width, label="Synthetic (n=55)",
            color=SYNTH_COLOR, edgecolor="white")

# Value labels — all conditions
for bars in [b1, b2]:
    for i, bar in enumerate(bars):
        weight = "bold" if i == ens_idx else "normal"
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.012,
                f"{bar.get_height():.3f}", ha="center", va="bottom",
                fontsize=7.5, fontweight=weight)

# Ensemble annotation: text box above the two ensemble bars
ens_x = x[ens_idx]
top_val = max(rc_idr[ens_idx], synth_idr[ens_idx])
ax.text(
    ens_x, top_val + 0.09,
    "★ Highest IDR\nboth subsets",
    ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#222222",
    bbox=dict(boxstyle="round,pad=0.3", facecolor="#fff9c4", edgecolor="#c8a000", linewidth=1.2),
)

ax.set_xticks(x)
ax.set_xticklabels(labels_fig3, fontsize=9)
ax.set_ylabel("Issue Detection Recall (IDR)", fontsize=11)
ax.set_title(
    "Figure 3. IDR by Condition, Stratified by Case Source — ordered by compute budget (n = 80 regular cases)\n"
    "RC = real ReScience C papers (2020–2021); Synthetic = planted-corruption cases.\n"
    "Ensemble IDR advantage: +0.172 on real papers vs +0.059 on synthetic  (RC n=25 — descriptive only, underpowered for formal testing).",
    fontsize=9)
ax.set_ylim(0, 1.12)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend(fontsize=9, loc="upper left")

plt.tight_layout()
plt.savefig(out_dir / "figure3_rc_stratified_idr.pdf", bbox_inches="tight")
plt.savefig(out_dir / "figure3_rc_stratified_idr.png", dpi=150, bbox_inches="tight")
plt.close()
print("Figure 3 saved.")

print("\nAll figures written to figures/")
