# generate_figures.py
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "numpy>=1.24",
#   "matplotlib>=3.7",
# ]
# ///
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

plt.rcParams.update({'font.size': 11, 'figure.dpi': 150})

# --- Load data ---
with open('v3_results.json') as f:
    d = json.load(f)
with open('stats_results.json') as f:
    s = json.load(f)
with open('sensitivity_analysis_results.json') as f:
    sa = json.load(f)
with open('difficulty_validation_results.json') as f:
    dv = json.load(f)

# --- Figure 1: Per-condition comparison with bootstrap CI error bars ---
conditions = ['Isolated\nDebate', 'Multiround', 'Ensemble', 'Baseline']
means = [
    s['bootstrap_cis']['isolated_debate_mean']['point'],
    s['bootstrap_cis']['multiround_mean']['point'],
    s['bootstrap_cis']['ensemble_mean']['point'],
    s['bootstrap_cis']['baseline_mean']['point'],
]
cis = [s['bootstrap_cis'][k]['ci'] for k in [
    'isolated_debate_mean', 'multiround_mean', 'ensemble_mean', 'baseline_mean'
]]
yerr_lo = [m - ci[0] for m, ci in zip(means, cis)]
yerr_hi = [ci[1] - m for m, ci in zip(means, cis)]
colors = ['#2196F3', '#4CAF50', '#FF9800', '#9E9E9E']

fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(conditions, means, color=colors, width=0.5, zorder=3)
ax.errorbar(range(len(conditions)), means,
            yerr=[yerr_lo, yerr_hi],
            fmt='none', color='black', capsize=5, linewidth=1.5, zorder=4)
ax.set_ylim(0.5, 1.05)
ax.set_ylabel('Mean Score (0–1)')
ax.set_title('V3 Benchmark: Per-Condition Mean Scores\n(95% Bootstrap CI, n=49 cases)')
ax.axhline(0.65, color='red', linestyle='--', linewidth=1, label='Pass threshold (0.65)', zorder=2)
ax.legend(fontsize=9)
ax.grid(axis='y', alpha=0.3, zorder=1)
for bar, mean in zip(bars, means):
    ax.text(bar.get_x() + bar.get_width() / 2, mean + 0.005,
            f'{mean:.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
plt.tight_layout()
plt.savefig('per_condition_comparison.png')
plt.close()
print('Saved per_condition_comparison.png')

# --- Figure 2: Dimension heatmap ---
dims = ['IDR', 'IDP', 'DC', 'DRQ', 'ETD', 'FVC']
cond_labels = ['Isolated\nDebate', 'Multiround', 'Ensemble', 'Baseline']
dim_agg = s['dimension_aggregates']
data = np.array([
    [dim_agg['isolated_debate'].get(d) or 0 for d in dims],
    [dim_agg['multiround'].get(d) or 0 for d in dims],
    [dim_agg['ensemble'].get(d) or 0 for d in dims],
    [dim_agg['baseline'].get(d) or 0 for d in dims],
])

fig, ax = plt.subplots(figsize=(9, 4))
im = ax.imshow(data, aspect='auto', cmap='RdYlGn', vmin=0, vmax=1)
ax.set_xticks(range(len(dims)))
ax.set_xticklabels(dims, fontsize=12)
ax.set_yticks(range(len(cond_labels)))
ax.set_yticklabels(cond_labels, fontsize=11)
ax.set_title('Rubric Dimension Aggregates by Condition\n(DC†=structural override for baseline)')
cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.04)
cbar.set_label('Mean score')
for i in range(len(cond_labels)):
    for j in range(len(dims)):
        val = data[i, j]
        txt_color = 'black' if 0.3 < val < 0.85 else 'white'
        ax.text(j, i, f'{val:.3f}', ha='center', va='center',
                fontsize=10, color=txt_color, fontweight='bold')
# Add DC/DRQ note for baseline
ax.text(2, 3.6, '†DC=0.0: structural override', ha='center', fontsize=8, color='gray', style='italic')
plt.tight_layout()
plt.savefig('dimension_heatmap.png')
plt.close()
print('Saved dimension_heatmap.png')

# --- Figure 3: Sensitivity analysis chart (raw vs corrected lift) ---
cl = sa['corrected_lift']
labels = ['Isolated vs.\nBaseline', 'Multiround vs.\nBaseline']
raw_lifts = [cl['raw_lift_isolated_vs_baseline'], cl['raw_lift_multiround_vs_baseline']]
corr_lifts = [cl['corrected_lift_isolated_DC05_DRQ_uncapped'], cl['corrected_lift_multiround_DC05_DRQ_uncapped']]

x = np.arange(len(labels))
width = 0.35
fig, ax = plt.subplots(figsize=(7, 5))
bars1 = ax.bar(x - width/2, raw_lifts, width, label='Raw lift\n(structural overrides applied)', color='#F44336', alpha=0.85)
bars2 = ax.bar(x + width/2, corr_lifts, width, label='Corrected lift\n(DC=0.5, DRQ uncapped)', color='#2196F3', alpha=0.85)
ax.axhline(0.10, color='black', linestyle='--', linewidth=1, label='Pre-registered threshold (+0.10)')
ax.set_ylabel('Lift (debate − baseline)')
ax.set_title('Sensitivity Analysis: Raw vs. Corrected Lift\n(Corrected = DC=0.5, DRQ uncapped for baseline)')
ax.set_xticks(x)
ax.set_xticklabels(labels)
ax.set_ylim(0, 0.45)
ax.legend(fontsize=9)
ax.grid(axis='y', alpha=0.3)
for bar in bars1:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
            f'+{bar.get_height():.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold', color='#F44336')
for bar in bars2:
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
            f'+{bar.get_height():.3f}', ha='center', va='bottom', fontsize=10, fontweight='bold', color='#2196F3')
plt.tight_layout()
plt.savefig('sensitivity_analysis_chart.png')
plt.close()
print('Saved sensitivity_analysis_chart.png')

# --- Figure 4: Difficulty scatter ---
results = d['cases']
non_dw = [r for r in results if r['correct_position'] != 'defense']
diff_map = {'easy': 0, 'medium': 1, 'hard': 2}
jitter = np.random.default_rng(42).uniform(-0.12, 0.12, len(non_dw))
xs = [diff_map[r['difficulty']] + jitter[i] for i, r in enumerate(non_dw)]
ys = [r['baseline']['mean'] for r in non_dw]
cats = [r['category'] for r in non_dw]
cat_colors = {
    'broken_baseline': '#E91E63',
    'metric_mismatch': '#9C27B0',
    'hidden_confounding': '#FF9800',
    'scope_intent': '#4CAF50',
    'real_world_framing': '#2196F3',
}
cat_labels = list(cat_colors.keys())

fig, ax = plt.subplots(figsize=(7, 5))
for cat in cat_labels:
    cx = [xs[i] for i, r in enumerate(non_dw) if r['category'] == cat]
    cy = [ys[i] for i, r in enumerate(non_dw) if r['category'] == cat]
    ax.scatter(cx, cy, c=cat_colors[cat], label=cat.replace('_', ' '), s=60, alpha=0.8, edgecolors='white', linewidths=0.5)

# Means by difficulty
for diff, label in diff_map.items():
    vals = [r['baseline']['mean'] for r in non_dw if r['difficulty'] == diff]
    if vals:
        ax.hlines(np.mean(vals), label - 0.3, label + 0.3, colors='black', linewidths=2, linestyles='--')

ax.set_xticks([0, 1, 2])
ax.set_xticklabels(['Easy', 'Medium', 'Hard'])
ax.set_ylabel('Baseline mean score')
ax.set_xlabel('Difficulty label')
ax.set_title(f'Difficulty Label vs. Baseline Score\n(Spearman ρ = {dv["spearman_rho"]:.3f}, p = {dv["p_value"]:.3f}, n={dv["non_defense_wins_n"]})')
ax.set_ylim(0.4, 0.85)
legend_patches = [mpatches.Patch(color=cat_colors[c], label=c.replace('_', ' ')) for c in cat_labels]
legend_patches.append(mpatches.Patch(color='black', label='Difficulty mean'))
ax.legend(handles=legend_patches, fontsize=8, loc='lower right')
ax.grid(alpha=0.3)
ax.text(0.02, 0.98, 'Dashed lines = mean per difficulty level', transform=ax.transAxes,
        fontsize=8, color='gray', va='top', style='italic')
plt.tight_layout()
plt.savefig('difficulty_scatter.png')
plt.close()
print('Saved difficulty_scatter.png')

print('\nAll 4 figures generated.')
