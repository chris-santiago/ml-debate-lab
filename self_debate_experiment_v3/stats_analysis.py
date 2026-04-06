# stats_analysis.py
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "numpy>=1.24",
#   "scipy>=1.11",
# ]
# ///
import json
import numpy as np
from scipy import stats as scipy_stats

with open('v3_results.json') as f:
    d = json.load(f)
results = d['cases']

isolated_means = [r['isolated_debate']['mean'] for r in results]
multiround_means = [r['multiround']['mean'] for r in results]
ensemble_means = [r['ensemble']['mean'] for r in results]
baseline_means = [r['baseline']['mean'] for r in results]

def bootstrap_ci(data, n=10000, ci=0.95):
    rng = np.random.default_rng(42)
    boot = [np.mean(rng.choice(data, len(data))) for _ in range(n)]
    alpha = (1 - ci) / 2
    return list(np.percentile(boot, [alpha * 100, (1 - alpha) * 100]))

ivb = [i - b for i, b in zip(isolated_means, baseline_means)]
ive = [i - e for i, e in zip(isolated_means, ensemble_means)]
mvb = [m - b for m, b in zip(multiround_means, baseline_means)]
mvi = [m - i for m, i in zip(multiround_means, isolated_means)]

def wilcoxon_test(diffs):
    w, p = scipy_stats.wilcoxon(diffs, alternative='greater', correction=True)
    n = len([x for x in diffs if x != 0])
    r = float(1 - (2 * w) / (n * (n + 1))) if n > 0 else 0.0
    return float(w), float(p), r

w1, p1, r1 = wilcoxon_test(ivb)
w2, p2, r2 = wilcoxon_test(ive)
w3, p3, r3 = wilcoxon_test(mvb)
w4, p4, r4 = wilcoxon_test(mvi)

mixed = [r for r in results if r['correct_position'] == 'mixed']
dw_cases = [r for r in results if r['correct_position'] == 'defense']

dims = ['IDR', 'IDP', 'DC', 'DRQ', 'ETD', 'FVC']
dim_agg = {}
for cond in ['isolated_debate', 'multiround', 'ensemble', 'baseline']:
    dim_agg[cond] = {}
    for dim in dims:
        vals = [run['scores'].get(dim) for r in results for run in r[cond]['runs']
                if run['scores'].get(dim) is not None]
        dim_agg[cond][dim] = round(sum(vals) / len(vals), 4) if vals else None

failure_counts = {}
for r in results:
    for run in r['isolated_debate']['runs']:
        fa = run.get('failure_attribution', 'none')
        failure_counts[fa] = failure_counts.get(fa, 0) + 1

output = {
    'bootstrap_cis': {
        'isolated_debate_mean': {'point': float(np.mean(isolated_means)), 'ci': bootstrap_ci(isolated_means)},
        'multiround_mean': {'point': float(np.mean(multiround_means)), 'ci': bootstrap_ci(multiround_means)},
        'ensemble_mean': {'point': float(np.mean(ensemble_means)), 'ci': bootstrap_ci(ensemble_means)},
        'baseline_mean': {'point': float(np.mean(baseline_means)), 'ci': bootstrap_ci(baseline_means)},
        'lift_isolated_vs_baseline': {'point': float(np.mean(ivb)), 'ci': bootstrap_ci(ivb)},
        'lift_isolated_vs_ensemble': {'point': float(np.mean(ive)), 'ci': bootstrap_ci(ive)},
        'lift_multiround_vs_baseline': {'point': float(np.mean(mvb)), 'ci': bootstrap_ci(mvb)},
        'lift_multiround_vs_isolated': {'point': float(np.mean(mvi)), 'ci': bootstrap_ci(mvi)},
    },
    'wilcoxon': {
        'isolated_vs_baseline': {'W': w1, 'p': p1, 'r': r1},
        'isolated_vs_ensemble': {'W': w2, 'p': p2, 'r': r2},
        'multiround_vs_baseline': {'W': w3, 'p': p3, 'r': r3},
        'multiround_vs_isolated': {'W': w4, 'p': p4, 'r': r4},
    },
    'mixed_position': {
        'n': len(mixed),
        'isolated_debate_mean': float(np.mean([r['isolated_debate']['mean'] for r in mixed])) if mixed else None,
        'multiround_mean': float(np.mean([r['multiround']['mean'] for r in mixed])) if mixed else None,
        'ensemble_mean': float(np.mean([r['ensemble']['mean'] for r in mixed])) if mixed else None,
    },
    'defense_wins': {
        'n': len(dw_cases),
        'ensemble_dc_mean': float(np.mean([r['ensemble']['runs'][0]['scores'].get('DC', 0)
                                           for r in dw_cases if r['ensemble']['runs']])) if dw_cases else None,
        'multiround_dc_mean': float(np.mean([r['multiround']['runs'][0]['scores'].get('DC', 0)
                                             for r in dw_cases if r['multiround']['runs']])) if dw_cases else None,
        'pre_specified_criterion_met': None,  # fill after computing
    },
    'dimension_aggregates': dim_agg,
    'within_case_variance': {
        'isolated_debate_std_mean': float(np.mean([r['isolated_debate']['std'] for r in results])),
        'multiround_std_mean': float(np.mean([r['multiround']['std'] for r in results])),
        'ensemble_std_mean': float(np.mean([r['ensemble']['std'] for r in results])),
        'baseline_std_mean': float(np.mean([r['baseline']['std'] for r in results])),
    },
    'failure_attribution': failure_counts,
}

# Pre-specified defense_wins criterion
if dw_cases:
    dc_pass = sum(1 for r in dw_cases
                  if r['ensemble']['runs'] and r['ensemble']['runs'][0]['scores'].get('DC', 0) >= 0.5)
    output['defense_wins']['pre_specified_criterion_met'] = dc_pass >= 0.6 * len(dw_cases)

with open('stats_results.json', 'w') as f:
    json.dump(output, f, indent=2)

print("Stats written.")
for k, v in output['bootstrap_cis'].items():
    print(f"  {k}: {v['point']:.4f} CI={v['ci']}")
print(f"\nWilcoxon isolated vs baseline:  W={w1}, p={p1:.6f}, r={r1:.3f}")
print(f"Wilcoxon isolated vs ensemble:  W={w2}, p={p2:.6f}, r={r2:.3f}")
print(f"Wilcoxon multiround vs baseline: W={w3}, p={p3:.6f}, r={r3:.3f}")
print(f"Wilcoxon multiround vs isolated: W={w4}, p={p4:.6f}, r={r4:.3f}")

# External benchmark stratum (separate from main benchmark CIs)
import os
if os.path.exists('v3_external_results.json'):
    with open('v3_external_results.json') as f:
        ext_d = json.load(f)
    ext_results = ext_d['cases']
    # Load provenance to split published vs synthetic
    with open('external_cases_v3.json') as f:
        ext_cases = json.load(f)
    provenance_map = {c['case_id']: c['provenance']['source_type'] for c in ext_cases}
    published = [r for r in ext_results if provenance_map.get(r['case_id']) == 'published_paper']
    synthetic = [r for r in ext_results if provenance_map.get(r['case_id']) == 'synthetic_grounded']
    def stratum_summary(cases_list, label):
        if not cases_list:
            return
        n = len(cases_list)
        iso_m = round(np.mean([r['isolated_debate']['mean'] for r in cases_list]), 4)
        mr_m = round(np.mean([r['multiround']['mean'] for r in cases_list]), 4)
        ens_m = round(np.mean([r['ensemble']['mean'] for r in cases_list]), 4)
        base_m = round(np.mean([r['baseline']['mean'] for r in cases_list]), 4)
        passes = sum(1 for r in cases_list if r['isolated_debate']['passes'] >= 2)
        print(f"\nExternal stratum [{label}] n={n}:")
        print(f"  isolated={iso_m:.4f}  multiround={mr_m:.4f}  ensemble={ens_m:.4f}  baseline={base_m:.4f}")
        print(f"  pass count (isolated, 2/3 rule): {passes}/{n}")
    stratum_summary(published, 'published_paper')
    stratum_summary(synthetic, 'synthetic_grounded')
    stratum_summary(ext_results, 'all_external')
    ext_summary = {
        'published_paper': {'n': len(published), 'isolated_mean': float(np.mean([r['isolated_debate']['mean'] for r in published])) if published else None},
        'synthetic_grounded': {'n': len(synthetic), 'isolated_mean': float(np.mean([r['isolated_debate']['mean'] for r in synthetic])) if synthetic else None},
    }
    with open('external_stats_summary.json', 'w') as f:
        json.dump(ext_summary, f, indent=2)
