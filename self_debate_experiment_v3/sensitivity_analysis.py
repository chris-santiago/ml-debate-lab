# sensitivity_analysis.py
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "numpy>=1.24",
# ]
# ///
# Computes corrected lift (DC=0.5, DRQ uncapped) and dimension-stratified analysis.
# These address v2 peer review major issues L3 and L4.
import json
import numpy as np

with open('v3_results.json') as f:
    d = json.load(f)
results = d['cases']

# --- Corrected lift (L3 fix) ---
# Recompute baseline means with DC=0.5 (partial credit) and DRQ uncapped
def corrected_baseline_mean(case_result):
    """Recompute baseline mean with structural overrides removed."""
    runs = case_result['baseline']['runs']
    if not runs:
        return None
    corrected_run_means = []
    for run in runs:
        scores = dict(run['scores'])
        # Override DC: give baseline 0.5 instead of 0.0
        if scores.get('DC') == 0.0:
            scores['DC'] = 0.5
        # DRQ: use natural score (uncapped) — but we only have the capped value stored
        # Approximation: if DRQ was capped at 0.5, natural DRQ is 1.0 if FVC=1.0
        if scores.get('DRQ') == 0.5 and scores.get('FVC') == 1.0:
            scores['DRQ'] = 1.0
        non_null = [v for v in scores.values() if v is not None]
        corrected_run_means.append(sum(non_null) / len(non_null) if non_null else 0.0)
    return round(sum(corrected_run_means) / len(corrected_run_means), 4)

raw_baseline_means = [r['baseline']['mean'] for r in results]
corrected_baseline_means = [corrected_baseline_mean(r) for r in results]
isolated_means = [r['isolated_debate']['mean'] for r in results]
multiround_means = [r['multiround']['mean'] for r in results]

raw_lift_isolated = round(np.mean(isolated_means) - np.mean(raw_baseline_means), 4)
corrected_lift_isolated = round(np.mean(isolated_means) - np.mean([m for m in corrected_baseline_means if m is not None]), 4)
raw_lift_multiround = round(np.mean(multiround_means) - np.mean(raw_baseline_means), 4)
corrected_lift_multiround = round(np.mean(multiround_means) - np.mean([m for m in corrected_baseline_means if m is not None]), 4)

# --- Dimension-stratified analysis (L4 fix) ---
# Fair-comparison: IDR, IDP, ETD, FVC (both systems have agency)
# Protocol-diagnostic: DC, DRQ (baseline structurally penalized)
fair_dims = ['IDR', 'IDP', 'ETD', 'FVC']
protocol_dims = ['DC', 'DRQ']

def dim_mean(results_list, condition, dims):
    vals = []
    for r in results_list:
        for run in r[condition]['runs']:
            for dim in dims:
                v = run['scores'].get(dim)
                if v is not None:
                    vals.append(v)
    return round(sum(vals) / len(vals), 4) if vals else None

sensitivity_output = {
    'corrected_lift': {
        'raw_lift_isolated_vs_baseline': raw_lift_isolated,
        'corrected_lift_isolated_DC05_DRQ_uncapped': corrected_lift_isolated,
        'raw_lift_multiround_vs_baseline': raw_lift_multiround,
        'corrected_lift_multiround_DC05_DRQ_uncapped': corrected_lift_multiround,
        'note': 'Corrected lift gives baseline DC=0.5 and uncaps DRQ. Raw lift inflated by structural overrides.',
        'raw_baseline_mean': round(float(np.mean(raw_baseline_means)), 4),
        'corrected_baseline_mean': round(float(np.mean([m for m in corrected_baseline_means if m is not None])), 4),
    },
    'dimension_stratified': {
        'fair_comparison_dims': fair_dims,
        'protocol_diagnostic_dims': protocol_dims,
        'note': 'Fair-comparison: both systems have equal agency. Protocol-diagnostic: baseline structurally penalized.',
        'isolated_debate': {
            'fair_comparison_mean': dim_mean(results, 'isolated_debate', fair_dims),
            'protocol_diagnostic_mean': dim_mean(results, 'isolated_debate', protocol_dims),
        },
        'multiround': {
            'fair_comparison_mean': dim_mean(results, 'multiround', fair_dims),
            'protocol_diagnostic_mean': dim_mean(results, 'multiround', protocol_dims),
        },
        'ensemble': {
            'fair_comparison_mean': dim_mean(results, 'ensemble', fair_dims),
            'protocol_diagnostic_mean': dim_mean(results, 'ensemble', protocol_dims),
        },
        'baseline': {
            'fair_comparison_mean': dim_mean(results, 'baseline', fair_dims),
            'protocol_diagnostic_mean': dim_mean(results, 'baseline', protocol_dims),
        },
        'lift_on_fair_dims': {
            'isolated_vs_baseline': round((dim_mean(results, 'isolated_debate', fair_dims) or 0) - (dim_mean(results, 'baseline', fair_dims) or 0), 4),
            'isolated_vs_ensemble': round((dim_mean(results, 'isolated_debate', fair_dims) or 0) - (dim_mean(results, 'ensemble', fair_dims) or 0), 4),
            'multiround_vs_baseline': round((dim_mean(results, 'multiround', fair_dims) or 0) - (dim_mean(results, 'baseline', fair_dims) or 0), 4),
            'multiround_vs_isolated': round((dim_mean(results, 'multiround', fair_dims) or 0) - (dim_mean(results, 'isolated_debate', fair_dims) or 0), 4),
        }
    },
    'cases_changing_pass_fail_under_correction': [
        r['case_id'] for r in results
        if r['baseline']['passes'] == 0 and corrected_baseline_mean(r) is not None
        and corrected_baseline_mean(r) >= 0.65
    ]
}

with open('sensitivity_analysis_results.json', 'w') as f:
    json.dump(sensitivity_output, f, indent=2)

print(f"Raw lift isolated vs baseline:   {raw_lift_isolated:+.4f}")
print(f"Corrected lift isolated:         {corrected_lift_isolated:+.4f}")
print(f"Raw lift multiround vs baseline: {raw_lift_multiround:+.4f}")
print(f"Corrected lift multiround:       {corrected_lift_multiround:+.4f}")
print(f"Fair-comparison lift isolated vs baseline:  {sensitivity_output['dimension_stratified']['lift_on_fair_dims']['isolated_vs_baseline']:+.4f}")
print(f"Fair-comparison lift multiround vs isolated: {sensitivity_output['dimension_stratified']['lift_on_fair_dims']['multiround_vs_isolated']:+.4f}")
