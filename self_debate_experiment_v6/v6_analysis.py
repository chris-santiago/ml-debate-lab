# v6_analysis.py
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""
Phase 7 — Bootstrap CI Hypothesis Tests for v6 Benchmark

Tests H1a, H1b, H2, H3, H4, H6 per hypotheses.md spec.
H5 deferred to Phase 9 (cross-vendor scorer agreement).

Usage:
  uv run v6_analysis.py [--results v6_results.json] [--n-boot 10000] [--seed 42]
"""

import argparse
import json
import math
import random
from collections import defaultdict
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--results', default='v6_results.json')
parser.add_argument('--n-boot', type=int, default=10000)
parser.add_argument('--seed', type=int, default=42)
parser.add_argument('--output', default='v6_hypothesis_results.json')
args = parser.parse_args()

random.seed(args.seed)
BASE_DIR = Path(__file__).parent
RESULTS_FILE = BASE_DIR / args.results
OUTPUT_FILE = BASE_DIR / args.output

# ---------------------------------------------------------------------------
# Bootstrap utilities
# ---------------------------------------------------------------------------

def bootstrap_paired_mean_diff(pairs, n_boot=10000, one_sided=False):
    """
    Paired bootstrap 95% CI for mean(a_i - b_i) across paired observations.
    Resamples case-level differences, preserving within-case pairing.
    one_sided=True: lower bound is 5th percentile; ci_hi is the 95th percentile.
    Returns (observed_diff, ci_lo, ci_hi, p_value_one_sided).
    """
    n = len(pairs)
    if n == 0:
        return None, None, None, None
    case_diffs = [a - b for a, b in pairs]
    obs = sum(case_diffs) / n

    boot_means = []
    for _ in range(n_boot):
        sample = [case_diffs[random.randint(0, n - 1)] for _ in range(n)]
        boot_means.append(sum(sample) / n)
    boot_means.sort()

    if one_sided:
        ci_lo = boot_means[int(0.05 * n_boot)]
        ci_hi = boot_means[int(0.95 * n_boot)]
    else:
        ci_lo = boot_means[int(0.025 * n_boot)]
        ci_hi = boot_means[int(0.975 * n_boot)]

    p_val = sum(1 for d in boot_means if d <= 0) / n_boot
    return round(obs, 4), round(ci_lo, 4), round(ci_hi, 4), round(p_val, 4)


def bootstrap_mean_diff(a, b, n_boot=10000, one_sided=False):
    """
    Unpaired bootstrap 95% CI for (mean(a) - mean(b)).
    Retained for reference; use bootstrap_paired_mean_diff for within-case comparisons.
    """
    n_a, n_b = len(a), len(b)
    obs = sum(a)/n_a - sum(b)/n_b if n_a and n_b else None
    if obs is None:
        return None, None, None, None

    diffs = []
    for _ in range(n_boot):
        s_a = [a[random.randint(0, n_a-1)] for _ in range(n_a)]
        s_b = [b[random.randint(0, n_b-1)] for _ in range(n_b)]
        diffs.append(sum(s_a)/n_a - sum(s_b)/n_b)
    diffs.sort()

    if one_sided:
        ci_lo = diffs[int(0.05 * n_boot)]
        ci_hi = diffs[int(0.95 * n_boot)]
    else:
        ci_lo = diffs[int(0.025 * n_boot)]
        ci_hi = diffs[int(0.975 * n_boot)]

    p_val = sum(1 for d in diffs if d <= 0) / n_boot
    return round(obs, 4), round(ci_lo, 4), round(ci_hi, 4), round(p_val, 4)


def wilcoxon_signed_rank(differences):
    """
    Wilcoxon signed-rank test for H0: median(differences) <= 0.
    Returns (W_statistic, p_value_approx, n_effective).
    Uses normal approximation for n >= 10.
    """
    nonzero = [(i, d) for i, d in enumerate(differences) if d != 0]
    n = len(nonzero)
    if n == 0:
        return 0, 1.0, 0

    # Rank by absolute value
    ranked = sorted(nonzero, key=lambda x: abs(x[1]))
    ranks = {}
    i = 0
    while i < len(ranked):
        j = i
        while j < len(ranked) and abs(ranked[j][1]) == abs(ranked[i][1]):
            j += 1
        avg_rank = (i + j + 1) / 2.0  # average rank (1-indexed)
        for k in range(i, j):
            ranks[ranked[k][0]] = avg_rank
        i = j

    W_plus = sum(ranks[idx] for idx, d in nonzero if d > 0)
    W_minus = sum(ranks[idx] for idx, d in nonzero if d < 0)
    W = min(W_plus, W_minus)

    # Normal approximation
    mu = n * (n + 1) / 4.0
    sigma = math.sqrt(n * (n + 1) * (2 * n + 1) / 24.0)
    if sigma == 0:
        return W, 1.0, n
    z = (W_plus - mu) / sigma  # positive = W_plus > expected
    # One-sided p-value for H1: W_plus large (differences > 0)
    p_approx = 1 - normal_cdf(z)
    return round(W_plus, 2), round(p_approx, 4), n


def normal_cdf(z):
    """Standard normal CDF via error function."""
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


# ---------------------------------------------------------------------------
# Data extraction
# ---------------------------------------------------------------------------

def get_condition_fc(case, condition):
    """Fair-comparison mean for a case × condition (None if not applicable)."""
    cond_data = case.get(condition, {})
    return cond_data.get('fair_comparison_mean')


def get_condition_run_scores(case, condition, dim):
    """List of per-run scores for a dimension."""
    cond_data = case.get(condition, {})
    return [r['scores'].get(dim) for r in cond_data.get('runs', []) if r['scores'].get(dim) is not None]


def get_condition_mean_score(case, condition, dim):
    """Mean of per-run scores for a dimension (None if no valid runs)."""
    vals = get_condition_run_scores(case, condition, dim)
    return sum(vals) / len(vals) if vals else None


def get_case_mean(case, condition):
    """Overall mean score for a case × condition."""
    cond_data = case.get(condition, {})
    return cond_data.get('mean')


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def main():
    print(f"Loading results from {RESULTS_FILE}...")
    raw = json.load(open(RESULTS_FILE))

    # v6_results.json is a list of case dicts OR a dict with 'results' key
    if isinstance(raw, list):
        all_cases = raw
    elif isinstance(raw, dict):
        all_cases = raw.get('cases', raw.get('results', raw.get('all_results', [])))
    else:
        raise ValueError("Unexpected results format")

    print(f"  Loaded {len(all_cases)} cases")

    # Split by category
    regular = [c for c in all_cases if c.get('correct_position') not in ('mixed',)]
    mixed   = [c for c in all_cases if c.get('correct_position') == 'mixed']
    defense = [c for c in all_cases if c.get('correct_position') == 'defense']
    critique = [c for c in all_cases if c.get('correct_position') == 'critique']
    hard    = [c for c in all_cases if c.get('difficulty') == 'hard']

    print(f"  Regular (critique+defense): {len(regular)} | Mixed: {len(mixed)} | Hard: {len(hard)}")

    N = args.n_boot
    results = {}

    # -----------------------------------------------------------------------
    # Descriptive: per-condition FC means and dimension breakdowns
    # -----------------------------------------------------------------------
    print("\n--- Descriptive Statistics ---")
    CONDITIONS = ['baseline', 'isolated_debate', 'biased_debate', 'multiround', 'conditional_fm', 'ensemble_3x']
    DIMS = ['IDR', 'IDP', 'IDP_adj', 'DRQ', 'FVC', 'ETD']

    desc = {}
    for cond in CONDITIONS:
        fc_vals = [get_condition_fc(c, cond) for c in regular if get_condition_fc(c, cond) is not None]
        dim_means = {}
        for dim in DIMS:
            vals = [get_condition_mean_score(c, cond, dim) for c in regular
                    if get_condition_mean_score(c, cond, dim) is not None]
            dim_means[dim] = round(sum(vals)/len(vals), 4) if vals else None
        # Mixed FVC
        mixed_fvc = [get_condition_mean_score(c, cond, 'FVC') for c in mixed
                     if get_condition_mean_score(c, cond, 'FVC') is not None]
        mixed_etd = [get_condition_mean_score(c, cond, 'ETD') for c in mixed
                     if get_condition_mean_score(c, cond, 'ETD') is not None]
        desc[cond] = {
            'fc_mean': round(sum(fc_vals)/len(fc_vals), 4) if fc_vals else None,
            'n_regular': len(fc_vals),
            'dim_means_regular': dim_means,
            'mixed_fvc_mean': round(sum(mixed_fvc)/len(mixed_fvc), 4) if mixed_fvc else None,
            'mixed_etd_mean': round(sum(mixed_etd)/len(mixed_etd), 4) if mixed_etd else None,
        }
        print(f"  {cond:20s}: FC={desc[cond]['fc_mean']}  IDR={dim_means.get('IDR')}  "
              f"IDP={dim_means.get('IDP')}  FVC_mixed={desc[cond]['mixed_fvc_mean']}")

    results['descriptive'] = desc

    # -----------------------------------------------------------------------
    # H1a: Regular case FC lift (isolated_debate vs baseline, one-sided)
    # -----------------------------------------------------------------------
    print("\n--- H1a: Regular case FC lift ---")
    h1a_pairs = [(get_condition_fc(c, 'isolated_debate'), get_condition_fc(c, 'baseline'))
                 for c in regular
                 if get_condition_fc(c, 'isolated_debate') is not None
                 and get_condition_fc(c, 'baseline') is not None]
    iso_fc  = [p[0] for p in h1a_pairs]
    base_fc = [p[1] for p in h1a_pairs]
    obs_h1a, ci_lo_h1a, ci_hi_h1a, p_h1a = bootstrap_paired_mean_diff(h1a_pairs, N, one_sided=True)

    # H1a threshold: adaptive from HYPOTHESIS.md
    baseline_fc_mean = sum(base_fc)/len(base_fc) if base_fc else 0.0
    h1a_threshold = max(0.03, min(0.10, (1.0 - baseline_fc_mean) * 0.5))
    h1a_pass = obs_h1a is not None and obs_h1a >= h1a_threshold and ci_lo_h1a > 0

    print(f"  lift={obs_h1a}  CI=[{ci_lo_h1a}, {ci_hi_h1a}]  threshold={round(h1a_threshold,4)}  p={p_h1a}  {'PASS' if h1a_pass else 'FAIL'}")
    results['H1a'] = {
        'observed_lift': obs_h1a, 'ci_lo': ci_lo_h1a, 'ci_hi': ci_hi_h1a,
        'p_value': p_h1a, 'threshold': round(h1a_threshold, 4),
        'n_iso': len(iso_fc), 'n_base': len(base_fc),
        'pass': h1a_pass,
    }

    # -----------------------------------------------------------------------
    # H1b: Mixed case FVC lift (isolated_debate vs baseline, one-sided)
    # -----------------------------------------------------------------------
    print("\n--- H1b: Mixed case FVC lift ---")
    h1b_pairs = [(get_condition_mean_score(c, 'isolated_debate', 'FVC'),
                  get_condition_mean_score(c, 'baseline', 'FVC'))
                 for c in mixed
                 if get_condition_mean_score(c, 'isolated_debate', 'FVC') is not None
                 and get_condition_mean_score(c, 'baseline', 'FVC') is not None]
    iso_fvc_mixed  = [p[0] for p in h1b_pairs]
    base_fvc_mixed = [p[1] for p in h1b_pairs]
    obs_h1b, ci_lo_h1b, ci_hi_h1b, p_h1b = bootstrap_paired_mean_diff(h1b_pairs, N, one_sided=True)
    h1b_pass = obs_h1b is not None and ci_lo_h1b > 0

    print(f"  lift={obs_h1b}  CI=[{ci_lo_h1b}, {ci_hi_h1b}]  p={p_h1b}  {'PASS' if h1b_pass else 'FAIL'}")
    results['H1b'] = {
        'observed_lift': obs_h1b, 'ci_lo': ci_lo_h1b, 'ci_hi': ci_hi_h1b,
        'p_value': p_h1b, 'n_iso': len(iso_fvc_mixed), 'n_base': len(base_fvc_mixed),
        'pass': h1b_pass,
    }

    # -----------------------------------------------------------------------
    # H2: Debate vs compute-matched ensemble (two-sided)
    # -----------------------------------------------------------------------
    print("\n--- H2: Debate vs ensemble ---")
    h2_reg_pairs = [(get_condition_fc(c, 'isolated_debate'), get_condition_fc(c, 'ensemble_3x'))
                    for c in regular
                    if get_condition_fc(c, 'isolated_debate') is not None
                    and get_condition_fc(c, 'ensemble_3x') is not None]
    ens_fc = [p[1] for p in h2_reg_pairs]
    obs_h2_reg, ci_lo_h2_reg, ci_hi_h2_reg, p_h2_reg = bootstrap_paired_mean_diff(h2_reg_pairs, N, one_sided=False)

    h2_mix_pairs = [(get_condition_mean_score(c, 'isolated_debate', 'FVC'),
                     get_condition_mean_score(c, 'ensemble_3x', 'FVC'))
                    for c in mixed
                    if get_condition_mean_score(c, 'isolated_debate', 'FVC') is not None
                    and get_condition_mean_score(c, 'ensemble_3x', 'FVC') is not None]
    ens_fvc_mixed = [p[1] for p in h2_mix_pairs]
    obs_h2_mix, ci_lo_h2_mix, ci_hi_h2_mix, p_h2_mix = bootstrap_paired_mean_diff(
        h2_mix_pairs, N, one_sided=False)

    # PASS = CI excludes 0 in favor of isolated (iso > ensemble)
    # FAIL = CI excludes 0 in favor of ensemble
    # INCONCLUSIVE = CI includes 0
    def h2_verdict(ci_lo, ci_hi):
        if ci_lo is None or ci_hi is None:
            return 'INCONCLUSIVE'
        if ci_lo > 0:
            return 'PASS (debate > ensemble)'
        if ci_hi < 0:
            return 'FAIL (ensemble > debate)'
        return 'INCONCLUSIVE'

    h2_reg_verdict = h2_verdict(ci_lo_h2_reg, ci_hi_h2_reg)
    h2_mix_verdict = h2_verdict(ci_lo_h2_mix, ci_hi_h2_mix)

    print(f"  Regular: delta={obs_h2_reg}  CI=[{ci_lo_h2_reg}, {ci_hi_h2_reg}]  → {h2_reg_verdict}")
    print(f"  Mixed FVC: delta={obs_h2_mix}  CI=[{ci_lo_h2_mix}, {ci_hi_h2_mix}]  → {h2_mix_verdict}")
    results['H2'] = {
        'regular': {'observed_delta': obs_h2_reg, 'ci_lo': ci_lo_h2_reg, 'ci_hi': ci_hi_h2_reg,
                    'p_value': p_h2_reg, 'verdict': h2_reg_verdict},
        'mixed_fvc': {'observed_delta': obs_h2_mix, 'ci_lo': ci_lo_h2_mix, 'ci_hi': ci_hi_h2_mix,
                      'p_value': p_h2_mix, 'verdict': h2_mix_verdict},
        'overall_verdict': h2_reg_verdict if h2_reg_verdict == h2_mix_verdict else 'MIXED',
    }

    # -----------------------------------------------------------------------
    # H3: Conditional FM vs natural multiround (Wilcoxon, hard cases only)
    # -----------------------------------------------------------------------
    print("\n--- H3: Conditional FM vs multiround (hard cases) ---")
    hard_cfm_fc = [get_condition_fc(c, 'conditional_fm') for c in hard
                   if get_condition_fc(c, 'conditional_fm') is not None]
    hard_mr_fc  = [get_condition_fc(c, 'multiround') for c in hard
                   if get_condition_fc(c, 'multiround') is not None]

    n_paired = min(len(hard_cfm_fc), len(hard_mr_fc))
    if n_paired > 0:
        differences = [hard_cfm_fc[i] - hard_mr_fc[i] for i in range(n_paired)]
        W, p_wilcoxon, n_eff = wilcoxon_signed_rank(differences)

        # Hollow round rate: rounds where conditional_fm stopped after round 1
        # Proxy: cases where gate_fired == False → stored in raw outputs
        # For now, compute from the runs data if available
        cfm_mean_hard = sum(hard_cfm_fc)/len(hard_cfm_fc)
        mr_mean_hard  = sum(hard_mr_fc)/len(hard_mr_fc)

        h3_pass = p_wilcoxon < 0.05 and cfm_mean_hard > mr_mean_hard
        print(f"  n_hard={n_paired}  CFM mean={round(cfm_mean_hard,4)}  MR mean={round(mr_mean_hard,4)}")
        print(f"  W={W}  p={p_wilcoxon}  n_eff={n_eff}  {'PASS' if h3_pass else 'FAIL'}")
        results['H3'] = {
            'n_hard_cases': n_paired, 'cfm_mean': round(cfm_mean_hard, 4),
            'mr_mean': round(mr_mean_hard, 4), 'mean_diff': round(cfm_mean_hard - mr_mean_hard, 4),
            'W_statistic': W, 'p_value': p_wilcoxon, 'n_effective': n_eff,
            'pass': h3_pass,
        }
    else:
        print(f"  No hard cases with conditional_fm data (n_cfm={len(hard_cfm_fc)}, n_mr={len(hard_mr_fc)})")
        results['H3'] = {'n_hard_cases': 0, 'pass': None, 'note': 'insufficient hard cases'}

    # -----------------------------------------------------------------------
    # H4: ETD quality by debate mode (exploratory, mixed cases)
    # -----------------------------------------------------------------------
    print("\n--- H4: ETD by debate mode (mixed cases, exploratory) ---")
    etd_results = {}
    for cond in ['isolated_debate', 'biased_debate', 'multiround', 'conditional_fm']:
        etd_vals = [get_condition_mean_score(c, cond, 'ETD') for c in mixed
                    if get_condition_mean_score(c, cond, 'ETD') is not None]
        if etd_vals:
            full_rate = sum(1 for v in etd_vals if v == 1.0) / len(etd_vals)
            partial_rate = sum(1 for v in etd_vals if v >= 0.5) / len(etd_vals)
            zero_rate = sum(1 for v in etd_vals if v == 0.0) / len(etd_vals)
            mean_etd = sum(etd_vals) / len(etd_vals)
            etd_results[cond] = {
                'n': len(etd_vals), 'mean': round(mean_etd, 4),
                'full_rate': round(full_rate, 4), 'partial_rate': round(partial_rate, 4),
                'zero_rate': round(zero_rate, 4),
            }
            print(f"  {cond:20s}: mean={round(mean_etd,4)}  full={round(full_rate,2)}  zero={round(zero_rate,2)}")
        else:
            etd_results[cond] = {'n': 0, 'mean': None}

    # Directional test: multiround > isolated_debate
    mr_etd  = [get_condition_mean_score(c, 'multiround', 'ETD') for c in mixed
               if get_condition_mean_score(c, 'multiround', 'ETD') is not None]
    iso_etd = [get_condition_mean_score(c, 'isolated_debate', 'ETD') for c in mixed
               if get_condition_mean_score(c, 'isolated_debate', 'ETD') is not None]
    obs_etd_diff = round(sum(mr_etd)/len(mr_etd) - sum(iso_etd)/len(iso_etd), 4) if mr_etd and iso_etd else None
    etd_direction = 'multiround > isolated' if (obs_etd_diff or 0) > 0 else 'multiround <= isolated'

    results['H4'] = {
        'by_condition': etd_results,
        'multiround_vs_isolated_delta': obs_etd_diff,
        'directional_prediction_confirmed': (obs_etd_diff or 0) > 0,
        'direction': etd_direction,
    }

    # -----------------------------------------------------------------------
    # H6: Persona-biasing (biased_debate vs isolated_debate, two-sided)
    # -----------------------------------------------------------------------
    print("\n--- H6: Persona bias — biased_debate vs isolated_debate ---")
    h6_idr_pairs = [(get_condition_mean_score(c, 'biased_debate', 'IDR'),
                     get_condition_mean_score(c, 'isolated_debate', 'IDR'))
                    for c in critique
                    if get_condition_mean_score(c, 'biased_debate', 'IDR') is not None
                    and get_condition_mean_score(c, 'isolated_debate', 'IDR') is not None]
    h6_idp_pairs = [(get_condition_mean_score(c, 'biased_debate', 'IDP_adj'),
                     get_condition_mean_score(c, 'isolated_debate', 'IDP_adj'))
                    for c in regular
                    if get_condition_mean_score(c, 'biased_debate', 'IDP_adj') is not None
                    and get_condition_mean_score(c, 'isolated_debate', 'IDP_adj') is not None]
    h6_fvc_pairs = [(get_condition_mean_score(c, 'biased_debate', 'FVC'),
                     get_condition_mean_score(c, 'isolated_debate', 'FVC'))
                    for c in mixed
                    if get_condition_mean_score(c, 'biased_debate', 'FVC') is not None
                    and get_condition_mean_score(c, 'isolated_debate', 'FVC') is not None]
    h6_idp_raw_pairs = [(get_condition_mean_score(c, 'biased_debate', 'IDP'),
                         get_condition_mean_score(c, 'isolated_debate', 'IDP'))
                        for c in regular
                        if get_condition_mean_score(c, 'biased_debate', 'IDP') is not None
                        and get_condition_mean_score(c, 'isolated_debate', 'IDP') is not None]

    obs_idr, ci_lo_idr, ci_hi_idr, p_idr = bootstrap_paired_mean_diff(h6_idr_pairs, N, one_sided=False)
    obs_idp, ci_lo_idp, ci_hi_idp, p_idp = bootstrap_paired_mean_diff(h6_idp_pairs, N, one_sided=False)
    obs_fvc, ci_lo_fvc, ci_hi_fvc, p_fvc = bootstrap_paired_mean_diff(h6_fvc_pairs, N, one_sided=False)
    obs_idp_raw, ci_lo_idp_raw, ci_hi_idp_raw, p_idp_raw = bootstrap_paired_mean_diff(
        h6_idp_raw_pairs, N, one_sided=False)

    # PASS criterion: CI excludes 0 for >= 2 of {IDR, IDP_adj, mixed FVC}
    dims_passing = sum([
        ci_lo_idr is not None and not (ci_lo_idr <= 0 <= ci_hi_idr),
        ci_lo_idp is not None and not (ci_lo_idp <= 0 <= ci_hi_idp),
        ci_lo_fvc is not None and not (ci_lo_fvc <= 0 <= ci_hi_fvc),
    ])
    h6_pass = dims_passing >= 2

    print(f"  IDR:     delta={obs_idr}  CI=[{ci_lo_idr}, {ci_hi_idr}]  p={p_idr}")
    print(f"  IDP_adj: delta={obs_idp}  CI=[{ci_lo_idp}, {ci_hi_idp}]  p={p_idp}")
    print(f"  FVC_mix: delta={obs_fvc}  CI=[{ci_lo_fvc}, {ci_hi_fvc}]  p={p_fvc}")
    print(f"  IDP_raw (diagnostic): delta={obs_idp_raw}  CI=[{ci_lo_idp_raw}, {ci_hi_idp_raw}]")
    print(f"  Dims with CI excluding 0: {dims_passing}/3  → {'PASS' if h6_pass else 'FAIL'}")

    results['H6'] = {
        'IDR': {'delta': obs_idr, 'ci_lo': ci_lo_idr, 'ci_hi': ci_hi_idr,
                'p_value': p_idr, 'ci_excludes_0': ci_lo_idr is not None and not (ci_lo_idr <= 0 <= ci_hi_idr)},
        'IDP_adj': {'delta': obs_idp, 'ci_lo': ci_lo_idp, 'ci_hi': ci_hi_idp,
                    'p_value': p_idp, 'ci_excludes_0': ci_lo_idp is not None and not (ci_lo_idp <= 0 <= ci_hi_idp)},
        'mixed_FVC': {'delta': obs_fvc, 'ci_lo': ci_lo_fvc, 'ci_hi': ci_hi_fvc,
                      'p_value': p_fvc, 'ci_excludes_0': ci_lo_fvc is not None and not (ci_lo_fvc <= 0 <= ci_hi_fvc)},
        'IDP_raw_diagnostic': {'delta': obs_idp_raw, 'ci_lo': ci_lo_idp_raw, 'ci_hi': ci_hi_idp_raw,
                               'p_value': p_idp_raw},
        'dims_ci_excluding_0': dims_passing,
        'pass': h6_pass,
    }

    # -----------------------------------------------------------------------
    # 7.3 Per-dimension lift decomposition (isolated vs baseline, regular)
    # -----------------------------------------------------------------------
    print("\n--- Per-dimension lift (isolated_debate vs baseline, regular cases) ---")
    dim_lift = {}
    for dim in ['IDR', 'IDP', 'DRQ', 'FVC']:
        iso_vals  = [get_condition_mean_score(c, 'isolated_debate', dim) for c in regular
                     if get_condition_mean_score(c, 'isolated_debate', dim) is not None]
        base_vals = [get_condition_mean_score(c, 'baseline', dim) for c in regular
                     if get_condition_mean_score(c, 'baseline', dim) is not None]
        if iso_vals and base_vals:
            lift = round(sum(iso_vals)/len(iso_vals) - sum(base_vals)/len(base_vals), 4)
            print(f"  {dim}: iso={round(sum(iso_vals)/len(iso_vals),4)}  base={round(sum(base_vals)/len(base_vals),4)}  lift={lift}")
            dim_lift[dim] = {'iso_mean': round(sum(iso_vals)/len(iso_vals),4),
                             'base_mean': round(sum(base_vals)/len(base_vals),4), 'lift': lift}
    results['dim_lift_decomposition'] = dim_lift

    # -----------------------------------------------------------------------
    # 7.5 Within-case variance analysis
    # -----------------------------------------------------------------------
    print("\n--- Within-case variance (flag > 0.05) ---")
    high_variance_cases = []
    conditions_to_check = ['isolated_debate', 'biased_debate', 'multiround', 'baseline', 'ensemble_3x']
    for case in all_cases:
        cid = case['case_id']
        for cond in conditions_to_check:
            runs = case.get(cond, {}).get('runs', [])
            means = [r.get('mean', 0) for r in runs if r.get('mean') is not None]
            if len(means) >= 2:
                avg = sum(means) / len(means)
                var = sum((m - avg)**2 for m in means) / len(means)
                if var > 0.05:
                    high_variance_cases.append({'case_id': cid, 'condition': cond,
                                                'variance': round(var, 4), 'means': means})

    print(f"  High-variance cases (var>0.05): {len(high_variance_cases)}")
    if high_variance_cases[:5]:
        for hv in high_variance_cases[:5]:
            print(f"    {hv['case_id']} [{hv['condition']}]: var={hv['variance']} means={hv['means']}")
    results['within_case_variance'] = {
        'n_high_variance': len(high_variance_cases),
        'threshold': 0.05,
        'cases': high_variance_cases[:20],  # top 20
    }

    # -----------------------------------------------------------------------
    # 7.4 Failure attribution for cases where isolated < baseline (regular)
    # -----------------------------------------------------------------------
    underperforming = []
    for case in regular:
        cid = case['case_id']
        iso = get_condition_fc(case, 'isolated_debate')
        base = get_condition_fc(case, 'baseline')
        if iso is not None and base is not None and iso < base:
            underperforming.append({
                'case_id': cid,
                'difficulty': case.get('difficulty'),
                'correct_position': case.get('correct_position'),
                'iso_fc': iso, 'base_fc': base, 'delta': round(iso - base, 4),
                'failure_attribution': case.get('isolated_debate', {}).get('runs', [{}])[0].get('failure_attribution', 'unknown'),
            })
    underperforming.sort(key=lambda x: x['delta'])
    results['failure_attribution'] = {
        'n_underperforming': len(underperforming),
        'cases': underperforming,
    }

    # -----------------------------------------------------------------------
    # H5 placeholder (deferred to Phase 9)
    # -----------------------------------------------------------------------
    results['H5'] = {'status': 'deferred_to_phase_9', 'note': 'Cross-vendor scorer agreement measured in Phase 9'}

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    print("\n" + "="*60)
    print("HYPOTHESIS TEST SUMMARY")
    print("="*60)
    for h in ['H1a', 'H1b', 'H3', 'H6']:
        r = results[h]
        verdict = 'PASS' if r.get('pass') else ('FAIL' if r.get('pass') is False else 'N/A')
        print(f"  {h}: {verdict}")
    for h in ['H2']:
        r = results[h]
        print(f"  H2 regular: {r['regular']['verdict']}")
        print(f"  H2 mixed:   {r['mixed_fvc']['verdict']}")
    h4_dir = results['H4']['direction']
    h4_conf = 'confirmed' if results['H4']['directional_prediction_confirmed'] else 'not confirmed'
    print(f"  H4 (exploratory): multiround>isolated prediction {h4_conf} ({h4_dir})")
    print(f"  H5: deferred to Phase 9")

    # Save
    json.dump(results, open(OUTPUT_FILE, 'w'), indent=2)
    print(f"\nResults saved to {OUTPUT_FILE}")


if __name__ == '__main__':
    main()
