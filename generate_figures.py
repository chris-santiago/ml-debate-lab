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
with open("self_debate_experiment_v6/v6_hypothesis_results.json") as f:
    results = json.load(f)

desc = results["descriptive"]

# Conditions for main figures (conditional_fm excluded — n_regular=8, not comparable)
CONDITIONS = ["baseline", "isolated_debate", "ensemble_3x", "biased_debate", "multiround"]
LABELS = ["Baseline\n(1×)", "Isolated\nDebate\n(3×)", "Ensemble\n3×\n(3×)", "Biased\nDebate\n(3×)", "Multiround\n(~5×)"]
COLORS = ["#6baed6", "#fd8d3c", "#31a354", "#e6550d", "#756bb1"]
HIGHLIGHT = [False, False, True, False, False]  # ensemble_3x highlighted

out_dir = Path("figures")
out_dir.mkdir(exist_ok=True)

# ── Figure 1: IDR bar chart ───────────────────────────────────────────────────
idr_vals = [desc[c]["dim_means_regular"]["IDR"] for c in CONDITIONS]

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(range(len(CONDITIONS)), idr_vals, color=COLORS, width=0.6,
              edgecolor="white", linewidth=1.2)

# Highlight ensemble_3x with bold edge
bars[2].set_edgecolor("#1a7a2e")
bars[2].set_linewidth(2.5)

# Value labels on bars
for i, (bar, val) in enumerate(zip(bars, idr_vals)):
    ax.text(bar.get_x() + bar.get_width() / 2, val + 0.008,
            f"{val:.3f}", ha="center", va="bottom",
            fontsize=9, fontweight="bold" if i == 2 else "normal")

ax.set_xticks(range(len(CONDITIONS)))
ax.set_xticklabels(LABELS, fontsize=9)
ax.set_ylabel("Issue Detection Recall (IDR)", fontsize=11)
ax.set_title("Figure 1. IDR by Condition — Regular Cases (n = 80)\n"
             "Paired bootstrap; all conditions use 3× compute except Baseline (1×) and Multiround (~5×)",
             fontsize=10)
ax.set_ylim(0, 0.88)
ax.axhline(idr_vals[0], color="#6baed6", linestyle="--", linewidth=0.8, alpha=0.6,
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
rc_idr    = [0.2828, 0.2702, 0.4545, 0.3460, 0.3005]
synth_idr = [0.8961, 0.8861, 0.9553, 0.8978, 0.8560]
labels_fig3 = ["Baseline\n(1×)", "Isolated\nDebate\n(3×)", "Ensemble\n3×\n(3×)",
               "Biased\nDebate\n(3×)", "Multiround\n(~5×)"]

x = np.arange(len(CONDITIONS))
width = 0.35

fig, ax = plt.subplots(figsize=(9, 5))
b1 = ax.bar(x - width / 2, rc_idr,    width, label="Real papers (RC, n=25)",
            color="#2171b5", edgecolor="white")
b2 = ax.bar(x + width / 2, synth_idr, width, label="Synthetic (n=55)",
            color="#6baed6", edgecolor="white", alpha=0.85)

# Highlight ensemble bars
b1[2].set_edgecolor("#084594"); b1[2].set_linewidth(2.2)
b2[2].set_edgecolor("#084594"); b2[2].set_linewidth(2.2)

# Value labels
for bars in [b1, b2]:
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.012,
                f"{bar.get_height():.3f}", ha="center", va="bottom", fontsize=7.5)

ax.set_xticks(x)
ax.set_xticklabels(labels_fig3, fontsize=9)
ax.set_ylabel("Issue Detection Recall (IDR)", fontsize=11)
ax.set_title("Figure 3. IDR by Condition, Stratified by Case Source (n = 80 regular cases)\n"
             "RC = real ReScience C papers (2020–2021); Synthetic = planted-corruption cases.\n"
             "Ensemble IDR advantage: +0.172 on real papers vs +0.059 on synthetic (n=25 — underpowered for formal testing).",
             fontsize=9)
ax.set_ylim(0, 1.08)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.legend(fontsize=9, loc="upper left")

plt.tight_layout()
plt.savefig(out_dir / "figure3_rc_stratified_idr.pdf", bbox_inches="tight")
plt.savefig(out_dir / "figure3_rc_stratified_idr.png", dpi=150, bbox_inches="tight")
plt.close()
print("Figure 3 saved.")

print("\nAll figures written to figures/")
