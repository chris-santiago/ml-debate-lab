# extract_within_case_variance.py
# /// script
# requires-python = ">=3.10"
# ///
# Extracts within-case variance from v3_results.json into the required format.
import json

with open('v3_results.json') as f:
    d = json.load(f)

variance_output = {
    'experiment': 'within_case_variance_v3',
    'n_runs_per_case': 3,
    'cases': {}
}

high_variance = []
for r in d['cases']:
    cid = r['case_id']
    isolated_std = r['isolated_debate']['std']
    multiround_std = r['multiround']['std']
    ensemble_std = r['ensemble']['std']
    baseline_std = r['baseline']['std']
    variance_output['cases'][cid] = {
        'isolated_debate_std': isolated_std,
        'multiround_std': multiround_std,
        'ensemble_std': ensemble_std,
        'baseline_std': baseline_std,
        'isolated_debate_mean': r['isolated_debate']['mean'],
        'multiround_mean': r['multiround']['mean'],
        'converging': r.get('convergence_rate', None)
    }
    if isolated_std > 0.1:
        high_variance.append({'case_id': cid, 'isolated_debate_std': isolated_std})

variance_output['high_variance_cases'] = high_variance
variance_output['summary'] = {
    'isolated_debate_std_mean': round(sum(r['isolated_debate']['std'] for r in d['cases']) / len(d['cases']), 4),
    'multiround_std_mean': round(sum(r['multiround']['std'] for r in d['cases']) / len(d['cases']), 4),
    'ensemble_std_mean': round(sum(r['ensemble']['std'] for r in d['cases']) / len(d['cases']), 4),
    'baseline_std_mean': round(sum(r['baseline']['std'] for r in d['cases']) / len(d['cases']), 4),
    'cases_with_high_isolated_variance': len(high_variance),
}

with open('within_case_variance_results.json', 'w') as f:
    json.dump(variance_output, f, indent=2)

print(f"Within-case variance written.")
print(f"Isolated debate std mean: {variance_output['summary']['isolated_debate_std_mean']}")
print(f"Multiround std mean: {variance_output['summary']['multiround_std_mean']}")
print(f"High variance cases (isolated_debate_std > 0.1): {len(high_variance)}")
if high_variance:
    for c in high_variance:
        print(f"  {c['case_id']}: std={c['isolated_debate_std']}")
