# self_debate_poc.py
# /// script
# requires-python = ">=3.10"
# ///
"""
Self-Debate Protocol v3 — Scoring Engine

Key improvements over v2:
- IDR is fractional (issues_found / total_must_find_issue_ids)
- FVC uses scoring_targets.acceptable_resolutions (list), not just ideal_resolution
- IDP uses scoring_targets.must_not_claim for explicit false-positive detection
- failure_attribution on every scored case
- Within-case variance: 3 runs per case per condition
"""

import json
from pathlib import Path

import argparse

OUTPUT_DIR = Path(__file__).parent

parser = argparse.ArgumentParser()
parser.add_argument('--cases', default='benchmark_cases_verified.json',
                    help='Case file to score (default: benchmark_cases_verified.json)')
parser.add_argument('--output', default='v3_results.json',
                    help='Results output file (default: v3_results.json)')
args, _ = parser.parse_known_args()

CASES_FILE = OUTPUT_DIR / args.cases
RESULTS_FILE = OUTPUT_DIR / args.output
EVAL_RESULTS_FILE = OUTPUT_DIR / args.output.replace('.json', '_eval.json')


def load_cases():
    with open(CASES_FILE) as f:
        return json.load(f)


def compute_idr(must_find_ids, issues_found):
    if not must_find_ids:
        return None
    found = [i for i in must_find_ids if i in issues_found]
    return round(len(found) / len(must_find_ids), 4)


def compute_idp(all_issues_raised, must_find_ids, must_not_claim):
    """
    IDP uses must_not_claim for explicit false-positive detection.
    - Issues in must_not_claim: explicit false positives
    - Issues in must_find_ids: valid
    - Other issues: neutral (don't affect precision)
    """
    if not all_issues_raised:
        return 1.0
    invalid = [i for i in all_issues_raised if i in must_not_claim]
    valid = [i for i in all_issues_raised if i in must_find_ids]
    denominator = len(valid) + len(invalid)
    if denominator == 0:
        return 1.0  # Only neutral issues raised
    frac = len(valid) / denominator
    if frac >= 0.9:
        return 1.0
    elif frac >= 0.5:
        return 0.5
    return 0.0


def compute_fvc(verdict, acceptable_resolutions, ideal_resolution):
    """FVC uses acceptable_resolutions list — multiple correct answers allowed."""
    if verdict in acceptable_resolutions:
        return 1.0
    adjacents = {
        ('critique_wins', 'empirical_test_agreed'),
        ('empirical_test_agreed', 'critique_wins'),
        ('defense_wins', 'empirical_test_agreed'),
        ('empirical_test_agreed', 'defense_wins'),
    }
    if (verdict, ideal_resolution) in adjacents:
        return 0.5
    return 0.0


def compute_dc(verdict, acceptable_resolutions, ideal_resolution, condition):
    """
    DC measures verdict correctness via defense function.
    NOTE: In isolated_debate and ensemble conditions, DC is structurally identical
    to FVC — the Defender never sees the Critique, so v1's rich concession/contestation
    metric is inapplicable. In multiround condition, DC reflects the verdict after
    adversarial exchange. See dc_note in PREREGISTRATION.json.
    Baseline hardcoded 0.0 — structural, pre-registered.
    """
    if condition == 'baseline':
        return 0.0  # Structural override — pre-registered
    return compute_fvc(verdict, acceptable_resolutions, ideal_resolution)


def compute_drq(verdict, acceptable_resolutions, ideal_resolution, condition):
    """
    DRQ distinguishes ideal match (1.0) from other acceptable matches (0.5).
    Preserves v1 tiered scoring: ideal=1.0 > other-acceptable=0.5 > adjacent=0.5 > wrong=0.0.
    Baseline capped at 0.5 — structural, pre-registered.
    """
    adjacents = {
        ('critique_wins', 'empirical_test_agreed'),
        ('empirical_test_agreed', 'critique_wins'),
        ('defense_wins', 'empirical_test_agreed'),
        ('empirical_test_agreed', 'defense_wins'),
    }
    if verdict == ideal_resolution:
        score = 1.0
    elif verdict in acceptable_resolutions:
        score = 0.5
    elif (verdict, ideal_resolution) in adjacents:
        score = 0.5
    else:
        score = 0.0
    if condition == 'baseline':
        return min(score, 0.5)  # Cap at 0.5 — pre-registered
    return score


def compute_etd(empirical_test, ideal_resolution):
    if ideal_resolution in ('critique_wins', 'defense_wins'):
        return None
    if not empirical_test or not isinstance(empirical_test, dict):
        return 0.0
    # Old schema: measure/success_criterion/failure_criterion
    if 'measure' in empirical_test:
        has_m = bool(empirical_test.get('measure'))
        has_s = bool(empirical_test.get('success_criterion'))
        has_f = bool(empirical_test.get('failure_criterion'))
    # New schema: condition/supports_critique_if/supports_defense_if
    elif 'condition' in empirical_test:
        has_m = bool(empirical_test.get('condition'))
        has_s = bool(empirical_test.get('supports_critique_if'))
        has_f = bool(empirical_test.get('supports_defense_if'))
    else:
        return 0.0
    if has_m and has_s and has_f:
        return 1.0
    elif has_m and (has_s or has_f):
        return 0.5
    return 0.0


def attribute_failure(scores, condition, passes):
    if passes:
        return 'none'
    if condition == 'baseline':
        return 'protocol'
    failed = [k for k, v in scores.items() if v is not None and v < 0.5]
    if 'DC' in failed:
        return 'agent'  # Defender reasoning/label disconnect
    if 'IDR' in failed:
        return 'agent'  # Critic missed must-find issues
    if 'DRQ' in failed or 'FVC' in failed:
        return 'protocol'
    return 'ambiguous'


def score_run(case, output, condition):
    gt = case['ground_truth']
    st = case['scoring_targets']
    idr_obj = case['ideal_debate_resolution']

    correct_position = gt['correct_position']
    ideal_resolution = idr_obj['type']
    acceptable_resolutions = st.get('acceptable_resolutions', [ideal_resolution])
    must_find_ids = st.get('must_find_issue_ids', [])
    must_not_claim = st.get('must_not_claim', [])

    verdict = output.get('verdict')
    issues_found = output.get('issues_found', [])
    all_issues_raised = output.get('all_issues_raised', [])
    empirical_test = output.get('empirical_test')

    scores = {}
    if correct_position == 'defense':
        scores['IDR'] = None
        scores['IDP'] = None
    else:
        scores['IDR'] = compute_idr(must_find_ids, issues_found)
        scores['IDP'] = compute_idp(all_issues_raised, must_find_ids, must_not_claim)

    scores['DC'] = compute_dc(verdict, acceptable_resolutions, ideal_resolution, condition)
    scores['DRQ'] = compute_drq(verdict, acceptable_resolutions, ideal_resolution, condition)
    scores['ETD'] = compute_etd(empirical_test, ideal_resolution)
    scores['FVC'] = compute_fvc(verdict, acceptable_resolutions, ideal_resolution)

    non_null = [v for v in scores.values() if v is not None]
    mean = round(sum(non_null) / len(non_null), 4) if non_null else 0.0
    passes = mean >= 0.65 and all(v >= 0.5 for v in non_null)

    return {
        'scores': scores,
        'mean': mean,
        'passes': passes,
        'verdict': verdict,
        'failure_attribution': attribute_failure(scores, condition, passes),
        'issues_found': issues_found,
        'missed_issues': [i for i in must_find_ids if i not in issues_found],
        'false_positive_issues': [i for i in all_issues_raised if i in must_not_claim],
    }


def aggregate_runs(run_results):
    means = [r['mean'] for r in run_results]
    avg = round(sum(means) / len(means), 4) if means else 0.0
    std = round((sum((m - avg)**2 for m in means) / len(means))**0.5, 4) if means else 0.0
    return {'mean': avg, 'std': std, 'passes': sum(1 for r in run_results if r['passes']), 'runs': run_results}


def main():
    cases = load_cases()
    raw_dir = OUTPUT_DIR / 'v3_raw_outputs'
    all_results = []
    eval_results = []

    for case in cases:
        cid = case['case_id']
        ideal = case['ideal_debate_resolution']['type']
        acceptable = case['scoring_targets'].get('acceptable_resolutions', [ideal])

        case_result = {
            'case_id': cid,
            'category': case['category'],
            'difficulty': case['difficulty'],
            'correct_position': case['ground_truth']['correct_position'],
            'ideal_resolution': ideal,
            'acceptable_resolutions': acceptable,
            'must_find': case['scoring_targets'].get('must_find_issue_ids', []),
        }

        for condition in ['isolated_debate', 'multiround', 'ensemble', 'baseline']:
            run_results = []
            for run_idx in range(1, 4):
                path = raw_dir / f"{cid}_{condition}_run{run_idx}.json"
                if not path.exists():
                    print(f"WARNING: Missing {path}")
                    continue
                with open(path) as f:
                    output = json.load(f)
                run_results.append(score_run(case, output, condition))
            case_result[condition] = aggregate_runs(run_results)

        all_results.append(case_result)

        first = case_result['isolated_debate']['runs'][0] if case_result['isolated_debate']['runs'] else {}
        eval_results.append({
            'case_id': cid,
            'scores': first.get('scores', {}),
            'pass_fail': 'pass' if case_result['isolated_debate']['passes'] >= 2 else 'fail',
            'found_planted_issues': first.get('issues_found', []),
            'missed_planted_issues': first.get('missed_issues', []),
            'false_positive_issues': first.get('false_positive_issues', []),
            'was_resolution_valid': first.get('verdict') in acceptable if first else False,
            'did_final_verdict_match_ground_truth': first.get('verdict') in acceptable if first else False,
            'failure_attribution': first.get('failure_attribution', 'none'),
        })

    n = len(all_results)
    isolated_means = [r['isolated_debate']['mean'] for r in all_results]
    multiround_means = [r['multiround']['mean'] for r in all_results]
    ensemble_means = [r['ensemble']['mean'] for r in all_results]
    baseline_means = [r['baseline']['mean'] for r in all_results]
    bm_isolated = round(sum(isolated_means) / n, 4)
    bm_multiround = round(sum(multiround_means) / n, 4)
    bm_ensemble = round(sum(ensemble_means) / n, 4)
    bm_baseline = round(sum(baseline_means) / n, 4)
    lift = round(bm_isolated - bm_baseline, 4)
    d_pass_count = sum(1 for r in all_results if r['isolated_debate']['passes'] >= 2)
    d_pass_frac = round(d_pass_count / n, 4)
    benchmark_passes = bm_isolated >= 0.65 and d_pass_frac >= 0.75 and lift >= 0.10

    summary = {
        'benchmark_isolated_debate_mean': bm_isolated,
        'benchmark_multiround_mean': bm_multiround,
        'benchmark_ensemble_mean': bm_ensemble,
        'benchmark_baseline_mean': bm_baseline,
        'lift_isolated_vs_baseline': lift,
        'lift_multiround_vs_isolated': round(bm_multiround - bm_isolated, 4),
        'debate_pass_count': d_pass_count,
        'debate_pass_fraction': d_pass_frac,
        'benchmark_passes': benchmark_passes,
        'protocol': 'v3_four_conditions',
        'cases': all_results
    }

    with open(RESULTS_FILE, 'w') as f:
        json.dump(summary, f, indent=2)
    with open(EVAL_RESULTS_FILE, 'w') as f:
        json.dump(eval_results, f, indent=2)

    print("=" * 80)
    print("V3 BENCHMARK SUMMARY")
    print("=" * 80)
    print(f"{'Case':<32} {'Iso':>5} {'MR':>5} {'Ens':>5} {'Base':>5} {'Delta':>6} Pass")
    print("-" * 80)
    for r in all_results:
        delta = r['isolated_debate']['mean'] - r['baseline']['mean']
        passed = 'YES' if r['isolated_debate']['passes'] >= 2 else 'NO'
        print(f"{r['case_id']:<32} {r['isolated_debate']['mean']:>5.3f} {r['multiround']['mean']:>5.3f} {r['ensemble']['mean']:>5.3f} {r['baseline']['mean']:>5.3f} {delta:>+6.3f} {passed}")
    print("-" * 80)
    print(f"{'BENCHMARK':<32} {bm_isolated:>5.3f} {bm_multiround:>5.3f} {bm_ensemble:>5.3f} {bm_baseline:>5.3f} {lift:>+6.3f} {'PASS' if benchmark_passes else 'FAIL'}")
    print(f"\nIsolated debate pass rate: {d_pass_count}/{n} ({d_pass_frac:.1%})")
    print(f"Benchmark mean >= 0.65:    {'PASS' if bm_isolated >= 0.65 else 'FAIL'}")
    print(f"Case pass rate >= 75%:     {'PASS' if d_pass_frac >= 0.75 else 'FAIL'}")
    print(f"Lift >= +0.10:             {'PASS' if lift >= 0.10 else 'FAIL'}")
    print(f"Multiround vs isolated:    {bm_multiround - bm_isolated:+.4f}")
    print(f"\nBENCHMARK OVERALL: {'PASSES' if benchmark_passes else 'FAILS'}")


if __name__ == '__main__':
    main()
