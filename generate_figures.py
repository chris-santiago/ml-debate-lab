# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib", "numpy"]
# ///
"""
Generate figures for WORKING_PAPER.md.
Figure 1 and Figure 3 numbers sourced from v7_results.json and computed RC/synth stratification.
Figure 2 is a qualitative 2×2 matrix (Study 1 / v6 framing, unchanged).
"""

import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from collections import defaultdict
from pathlib import Path

# ── Load v7 source data ───────────────────────────────────────────────────────
with open("experiments/self_debate_experiment_v7/v7_results.json") as f:
    v7_results = json.load(f)

v7_summary = v7_results["condition_summary"]

# ── Compute RC/synth-stratified IDR for Figure 3 ─────────────────────────────
with open("experiments/self_debate_experiment_v7/v7_cases_sanitized.json") as f:
    cases = json.load(f)
with open("experiments/self_debate_experiment_v7/v7_rescored_idr_idp.json") as f:
    rescored = json.load(f)
with open("experiments/self_debate_experiment_v7/benchmark_cases_v7_raw.json") as f:
    benchmark = json.load(f)

scores = rescored["scores"]

must_find_map = {
    c["case_id"]: c.get("scoring_targets", {}).get("must_find_issue_ids", [])
    for c in benchmark
}
case_meta = {c["case_id"]: c for c in cases}
rc_case_ids = {
    c["case_id"] for c in cases
    if c["is_real_paper_case"] and c["category"] == "regular"
}
synth_case_ids = {
    c["case_id"] for c in cases
    if not c["is_real_paper_case"] and c["category"] == "regular"
}


def _union_idr(per_assessor_rescored, must_find_ids):
    """Union IDR from a single run's assessors: found if ANY assessor found it."""
    if not must_find_ids:
        return None
    union_found = set()
    for a in per_assessor_rescored:
        fb = a.get("found_booleans", {})
        union_found.update(iid for iid in must_find_ids if fb.get(iid, False))
    return round(len(union_found) / len(must_find_ids), 4)


# Accumulate per-run IDR per (condition, case_id)
_cond_case_runs = defaultdict(lambda: defaultdict(list))
for fname, sdata in scores.items():
    parts = fname.replace(".json", "").split("__")
    if len(parts) < 3:
        continue
    case_id, condition = parts[0], parts[1]
    meta = case_meta.get(case_id)
    if meta is None or meta["category"] != "regular":
        continue
    must_find = must_find_map.get(case_id, [])
    if not must_find:
        continue
    if condition == "ensemble_3x":
        par = sdata.get("per_assessor_rescored", [])
        idr = _union_idr(par, must_find) if par else sdata.get("idr_documented")
    else:
        idr = sdata.get("idr_documented")
    if idr is not None:
        _cond_case_runs[condition][case_id].append(idr)

# Average runs per case, then split by RC vs synthetic
_rc_idr = defaultdict(list)
_synth_idr = defaultdict(list)
for condition, case_dict in _cond_case_runs.items():
    for case_id, run_idrs in case_dict.items():
        mean_idr = sum(run_idrs) / len(run_idrs)
        if case_id in rc_case_ids:
            _rc_idr[condition].append(mean_idr)
        elif case_id in synth_case_ids:
            _synth_idr[condition].append(mean_idr)


def _mean(lst):
    return sum(lst) / len(lst) if lst else 0.0


# ── Shared constants ──────────────────────────────────────────────────────────
# v7 conditions (compute-ordered: 1× → 3×)
CONDITIONS = ["baseline", "isolated_debate", "ensemble_3x", "multiround_2r"]
LABELS = [
    "Baseline\n(1×)",
    "Isolated\nDebate\n(3×)",
    "Ensemble\n3×\n(3×)",
    "Multiround\n2R\n(3×)",
]
ENS_IDX = 2  # ensemble_3x position

BAR_COLOR = "#2c7bb6"   # teal — standard conditions
ENS_COLOR = "#e08214"   # amber — ensemble_3x

out_dir = Path("figures")
out_dir.mkdir(exist_ok=True)

# ── Figure 1: IDR bar chart ───────────────────────────────────────────────────
idr_vals = [v7_summary[c]["IDR"]["mean"] for c in CONDITIONS]
bar_colors = [ENS_COLOR if i == ENS_IDX else BAR_COLOR for i in range(len(CONDITIONS))]

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(range(len(CONDITIONS)), idr_vals, color=bar_colors, width=0.6,
              edgecolor="white", linewidth=1.2)

for i, (bar, val) in enumerate(zip(bars, idr_vals)):
    ax.text(bar.get_x() + bar.get_width() / 2, val + 0.008,
            f"{val:.3f}", ha="center", va="bottom",
            fontsize=9, fontweight="bold" if i == ENS_IDX else "normal")

ax.text(
    ENS_IDX, idr_vals[ENS_IDX] + 0.055,
    "★ Best condition\nat matched compute",
    ha="center", va="bottom", fontsize=8.5, fontweight="bold", color="#222222",
    bbox=dict(boxstyle="round,pad=0.3", facecolor="#fff9c4", edgecolor="#c8a000", linewidth=1.2),
)

ax.set_xticks(range(len(CONDITIONS)))
ax.set_xticklabels(LABELS, fontsize=9)
ax.set_ylabel("Issue Detection Recall (IDR)", fontsize=11)
ax.set_title(
    "Figure 1. IDR by Condition — Regular Cases (n = 160)\n"
    "Paired bootstrap; all non-baseline conditions use 3× compute",
    fontsize=10,
)
ax.set_ylim(0, 0.95)
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

# ── Figure 2: 2×2 convergent/divergent matrix (Study 1 / v6 framing) ─────────
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

for i, lbl in enumerate(col_labels):
    ax.text(i + 0.5, 2.08, lbl, ha="center", va="bottom", fontsize=10, fontweight="bold")

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
# RC n=5 (regular stratum), Synthetic n=155 — descriptive only for RC
data_fig3 = [
    (lbl, _mean(_rc_idr[cond]), _mean(_synth_idr[cond]))
    for lbl, cond in zip(LABELS, CONDITIONS)
]
labels_fig3 = [d[0] for d in data_fig3]
rc_idr_vals  = [d[1] for d in data_fig3]
synth_idr_vals = [d[2] for d in data_fig3]

rc_delta   = rc_idr_vals[ENS_IDX]   - rc_idr_vals[0]
synth_delta = synth_idr_vals[ENS_IDX] - synth_idr_vals[0]

RC_COLOR    = "#e08214"
SYNTH_COLOR = "#2c7bb6"

x = np.arange(len(data_fig3))
width = 0.35

fig, ax = plt.subplots(figsize=(9, 5.2))
b1 = ax.bar(x - width / 2, rc_idr_vals,    width, label="Real papers (RC, n=5)",
            color=RC_COLOR, edgecolor="white")
b2 = ax.bar(x + width / 2, synth_idr_vals, width, label="Synthetic (n=155)",
            color=SYNTH_COLOR, edgecolor="white")

for bars in [b1, b2]:
    for i, bar in enumerate(bars):
        weight = "bold" if i == ENS_IDX else "normal"
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.012,
                f"{bar.get_height():.3f}", ha="center", va="bottom",
                fontsize=7.5, fontweight=weight)

ens_x = x[ENS_IDX]
top_val = max(rc_idr_vals[ENS_IDX], synth_idr_vals[ENS_IDX])
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
    "Figure 3. IDR by Condition, Stratified by Case Source — ordered by compute budget (n = 160 regular cases)\n"
    f"RC = real ReScience C papers (2020–2021); Synthetic = planted-corruption cases.\n"
    f"Ensemble IDR advantage: +{rc_delta:.3f} on real papers vs +{synth_delta:.3f} on synthetic"
    f"  (RC n=5 — descriptive only, underpowered for formal testing).",
    fontsize=9,
)
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
