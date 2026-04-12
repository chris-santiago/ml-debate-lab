# /// script
# requires-python = ">=3.10"
# dependencies = ["openai>=1.0", "tqdm"]
# ///
"""
v6 Follow-Up: Minority-Flagged Issue Precision Analysis

Tests whether issues flagged by only 1/3 ensemble assessors have materially lower
precision than issues flagged by 2/3 or 3/3 assessors.

We know from the original analysis that 11 must_find issues (9.5% of the pool) are
caught by only a single assessor — all true positives dropped by majority-vote.
This script measures the *precision* of the full issue universe (not just must_find
issues) by tier, to determine whether the union-output recommendation is safe.

Data: 60 critique cases × 3 runs × 3 assessors/run = 180 (case, run) pairs.
API calls: 1 GPT-4o call per (case, run) = 180 calls.
Each call receives 3 assessors × 5 issues = 15 raw issues + ground truth.

Usage:
    uv run v6_minority_precision.py [--dry-run] [--resume] [--concurrency 20]
"""

import argparse
import asyncio
import json
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

from tqdm import tqdm

try:
    from openai import AsyncOpenAI
except ImportError:
    print("ERROR: openai package required. Run via: uv run v6_minority_precision.py")
    sys.exit(1)

# ---------------------------------------------------------------------------
# CLI args
# ---------------------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument('--dry-run', action='store_true',
                    help='Skip API calls, produce placeholder output for testing')
parser.add_argument('--resume', action='store_true',
                    help='Skip (case, run) pairs already in output file')
parser.add_argument('--concurrency', type=int, default=20,
                    help='Max concurrent GPT-4o calls (default 20)')
parser.add_argument('--model', default='openai/gpt-4o')
parser.add_argument('--cases', default='benchmark_cases_verified.json')
parser.add_argument('--interim-dir', default='v6_interim_ensemble',
                    help='Directory containing chunk_*_run*_assessor*.json files')
parser.add_argument('--output', default='v6_minority_precision_results.json')
args = parser.parse_args()

BASE_DIR = Path(__file__).parent
CASES_FILE = BASE_DIR / args.cases
INTERIM_DIR = BASE_DIR / args.interim_dir
OUTPUT_FILE = BASE_DIR / args.output

VALID_LABELS = {'A.0', 'A.1', 'A.2', 'A.3', 'A.4',
                'B.0', 'B.1', 'B.2', 'B.3', 'B.4',
                'C.0', 'C.1', 'C.2', 'C.3', 'C.4'}
VALID_CLASSES = {'planted_match', 'false_claim', 'valid_novel', 'spurious'}
ASSESSOR_LETTERS = {1: 'A', 2: 'B', 3: 'C'}
LETTER_TO_IDX = {'A': 0, 'B': 1, 'C': 2}

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_case_index(cases_file: Path) -> dict:
    """Load benchmark_cases_verified.json. Returns dict keyed by case_id (critique only)."""
    cases = json.load(open(cases_file))
    idx = {}
    for c in cases:
        if c['ground_truth']['correct_position'] != 'critique':
            continue
        cid = c['case_id']
        planted = {pi['issue_id']: pi['description'] for pi in c.get('planted_issues', [])}
        must_find = c['scoring_targets'].get('must_find_issue_ids', [])
        must_not = c['scoring_targets'].get('must_not_claim_details', [])
        idx[cid] = {
            'planted_issues': planted,
            'must_find_ids': must_find,
            'must_not_claim_details': must_not,
        }
    return idx


def load_assessor_data(interim_dir: Path, critique_ids: set) -> dict:
    """
    Load per-assessor issue data from v6_interim_ensemble/ files.
    Returns dict keyed by (case_id, run_idx) → {assessor_id: [issues]}.
    """
    data = defaultdict(dict)
    for f in sorted(interim_dir.glob('chunk_*.json')):
        entries = json.load(open(f))
        for e in entries:
            cid = e['case_id']
            if cid not in critique_ids:
                continue
            run_idx = e['run_idx']
            assessor_id = e['assessor_id']
            data[(cid, run_idx)][assessor_id] = e['all_issues_raised']
    return dict(data)

# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------


def build_classification_prompt(
    issues_by_assessor: dict,          # {1: [5 strings], 2: [5 strings], 3: [5 strings]}
    planted_issues: dict,              # {issue_id: description}
    must_not_claim_details: list,      # [{claim_id, claim, why_wrong}]
    must_find_ids: list,               # [issue_id, ...]
) -> str:
    # Format assessor issue blocks
    assessor_blocks = []
    for assessor_id in (1, 2, 3):
        letter = ASSESSOR_LETTERS[assessor_id]
        issues = issues_by_assessor.get(assessor_id, [])
        block = f"ASSESSOR {letter} ISSUES:\n"
        block += "\n".join(f"  [{letter}.{i}] {issue}" for i, issue in enumerate(issues))
        assessor_blocks.append(block)
    assessors_section = "\n\n".join(assessor_blocks)

    # Format planted issues
    if planted_issues:
        planted_block = "\n".join(
            f"  [{iid}] {desc}"
            for iid, desc in planted_issues.items()
            if iid in must_find_ids
        )
    else:
        planted_block = "  (none)"

    # Format false claims
    if must_not_claim_details:
        false_claims_block = "\n".join(
            f"  [{d['claim_id']}] CLAIM: {d['claim']}\n    WHY WRONG: {d['why_wrong']}"
            for d in must_not_claim_details
        )
    else:
        false_claims_block = "  (none)"

    return f"""You are evaluating issues raised by three independent assessors of an ML experiment design.

{assessors_section}

---
PLANTED ISSUES (known real flaws in the experimental design — these should be found):
{planted_block}

FALSE CLAIMS (incorrect criticisms that should NOT be raised):
{false_claims_block}

---
INSTRUCTIONS:

Step 1 — DEDUPLICATION:
Group the 15 assessor issues into unique concern clusters. Two issues belong in the
same cluster if they raise substantially the same concern, even if worded differently.
An issue that appears across multiple assessors should be in ONE cluster.
If a single assessor raises the same concern twice, group both into one cluster.

Step 2 — CLASSIFICATION:
For each unique cluster, assign exactly one classification:
  "planted_match" — substantially matches one of the PLANTED ISSUES above (same core flaw,
    even if different terminology)
  "false_claim"   — substantially matches one of the FALSE CLAIMS above (an incorrect or
    misleading criticism that maps to a known false claim)
  "valid_novel"   — a genuine methodological concern NOT covered by any planted issue or
    false claim; a real limitation that would concern a careful reviewer
  "spurious"      — not a genuine concern; vague, trivially true, based on a misunderstanding,
    or so generic it applies to any study (e.g., "more data would help", "results may not
    generalize")

Step 3 — OUTPUT:
Respond with JSON only. No prose before or after.

{{
  "unique_issues": [
    {{
      "summary": "<concise description of the shared concern>",
      "assessors": [<0-indexed assessor IDs who raised this — A=0, B=1, C=2>],
      "raw_issues": ["<bracket label for each contributing issue, e.g. 'A.2', 'B.0'>"],
      "classification": "<planted_match|false_claim|valid_novel|spurious>",
      "matched_id": "<issue_id or claim_id if planted_match/false_claim, else null>"
    }}
  ]
}}

CONSTRAINTS:
- Every bracket label A.0–A.4, B.0–B.4, C.0–C.4 must appear in exactly one cluster.
- "assessors" contains 0-indexed IDs: A=0, B=1, C=2.
- "matched_id" is non-null only for planted_match and false_claim.
- If no planted issues or false claims exist, only valid_novel and spurious are possible.
"""

# ---------------------------------------------------------------------------
# GPT-4o call + validation
# ---------------------------------------------------------------------------


async def call_gpt4o(client, prompt: str, semaphore, model: str, label: str = '') -> dict | None:
    async with semaphore:
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=2048,
                response_format={"type": "json_object"},
            )
            text = response.choices[0].message.content
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"\nWARN: JSON parse error for {label}: {e}")
            return None
        except Exception as e:
            print(f"\nERROR: API call failed for {label}: {e}")
            return None


def validate_response(result: dict, must_find_ids: list, must_not_claim_ids: list) -> tuple[bool, list]:
    """
    Validate GPT-4o response. Returns (is_valid, list_of_error_strings).
    Checks: coverage, classification validity, matched_id consistency, assessor ID validity.
    """
    errors = []
    unique_issues = result.get('unique_issues', [])
    if not isinstance(unique_issues, list) or not unique_issues:
        return False, ['unique_issues missing or empty']

    # Coverage: every label must appear exactly once
    seen_labels = []
    for ui in unique_issues:
        seen_labels.extend(ui.get('raw_issues', []))
    seen_set = set(seen_labels)
    missing = VALID_LABELS - seen_set
    duplicates = [l for l in seen_labels if seen_labels.count(l) > 1]
    if missing:
        errors.append(f'missing labels: {sorted(missing)}')
    if duplicates:
        errors.append(f'duplicate labels: {sorted(set(duplicates))}')

    for ui in unique_issues:
        cls = ui.get('classification')
        mid = ui.get('matched_id')
        assessors = ui.get('assessors', [])

        # Classification validity
        if cls not in VALID_CLASSES:
            errors.append(f'invalid classification: {cls!r}')

        # matched_id consistency
        if cls == 'planted_match' and mid not in must_find_ids:
            errors.append(f'planted_match with bad matched_id: {mid!r}')
        elif cls == 'false_claim' and mid not in must_not_claim_ids:
            errors.append(f'false_claim with bad matched_id: {mid!r}')
        elif cls in ('valid_novel', 'spurious') and mid is not None:
            errors.append(f'{cls} should have null matched_id, got {mid!r}')

        # Assessor IDs
        for a in assessors:
            if a not in (0, 1, 2):
                errors.append(f'invalid assessor ID: {a!r}')

    return len(errors) == 0, errors

# ---------------------------------------------------------------------------
# Per-case-run scorer
# ---------------------------------------------------------------------------


async def score_case_run(
    client,
    case_id: str,
    run_idx: int,
    issues_by_assessor: dict,
    case_meta: dict,
    semaphore,
    model: str,
    dry_run: bool,
) -> tuple[str, dict]:
    """Score one (case_id, run_idx) pair. Returns (result_key, result_dict)."""
    key = f"{case_id}__{run_idx}"
    planted = case_meta['planted_issues']
    must_find = case_meta['must_find_ids']
    must_not = case_meta['must_not_claim_details']
    must_not_ids = [d['claim_id'] for d in must_not]

    if dry_run:
        # Produce plausible dry-run output without API call
        fake_issues = []
        letters = ['A', 'B', 'C']
        for mi, iid in enumerate(must_find[:2]):
            assessors_for_issue = [0, 1, 2] if mi == 0 else [0]
            raw = [f"{letters[a]}.{mi}" for a in assessors_for_issue]
            fake_issues.append({
                'summary': f'dry-run planted issue {iid}',
                'assessors': assessors_for_issue,
                'raw_issues': raw,
                'classification': 'planted_match',
                'matched_id': iid,
            })
        # Fill remaining labels as valid_novel
        used = set()
        for fi in fake_issues:
            used.update(fi['raw_issues'])
        remaining = sorted(VALID_LABELS - used)
        if remaining:
            fake_issues.append({
                'summary': 'dry-run valid novel concern',
                'assessors': list(set(LETTER_TO_IDX[l.split('.')[0]] for l in remaining)),
                'raw_issues': remaining,
                'classification': 'valid_novel',
                'matched_id': None,
            })
        return key, {'unique_issues': fake_issues, 'validation_error': False, 'validation_errors': []}

    prompt = build_classification_prompt(issues_by_assessor, planted, must_not, must_find)
    result = await call_gpt4o(client, prompt, semaphore, model, label=key)

    if result is None:
        return key, {'unique_issues': [], 'validation_error': True, 'validation_errors': ['api_failure']}

    is_valid, errors = validate_response(result, must_find, must_not_ids)
    result['validation_error'] = not is_valid
    result['validation_errors'] = errors
    if errors:
        print(f"\nVALID WARN {key}: {errors}")

    return key, result

# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------


def bootstrap_precision_ci(observations: list[tuple[str, bool]], n_boot: int = 10_000, seed: int = 42) -> tuple:
    """
    Bootstrap CI for precision of a tier.
    observations: list of (case_id, is_valid) — resample at case level.
    Returns (precision, ci_lo, ci_hi).
    """
    random.seed(seed)
    if not observations:
        return None, None, None

    # Group by case_id for case-level resampling
    by_case = defaultdict(list)
    for cid, is_valid in observations:
        by_case[cid].append(is_valid)
    case_ids = list(by_case.keys())

    obs_precision = sum(v for _, v in observations) / len(observations)

    boot_precisions = []
    for _ in range(n_boot):
        sample_cases = [case_ids[random.randint(0, len(case_ids) - 1)] for _ in range(len(case_ids))]
        vals = []
        for cid in sample_cases:
            vals.extend(by_case[cid])
        boot_precisions.append(sum(vals) / len(vals) if vals else 0)
    boot_precisions.sort()

    ci_lo = boot_precisions[int(0.025 * n_boot)]
    ci_hi = boot_precisions[int(0.975 * n_boot)]
    return round(obs_precision, 4), round(ci_lo, 4), round(ci_hi, 4)


def bootstrap_precision_diff(
    obs_a: list[tuple[str, bool]],
    obs_b: list[tuple[str, bool]],
    n_boot: int = 10_000,
    seed: int = 42,
) -> tuple:
    """
    Bootstrap CI for precision(a) - precision(b). Unpaired (tiers are independent samples).
    Returns (observed_diff, ci_lo, ci_hi, p_value).
    """
    random.seed(seed)
    if not obs_a or not obs_b:
        return None, None, None, None

    def resample_precision(obs):
        by_case = defaultdict(list)
        for cid, v in obs:
            by_case[cid].append(v)
        case_ids = list(by_case.keys())
        sample = [case_ids[random.randint(0, len(case_ids) - 1)] for _ in range(len(case_ids))]
        vals = []
        for cid in sample:
            vals.extend(by_case[cid])
        return sum(vals) / len(vals) if vals else 0

    obs_diff = (sum(v for _, v in obs_a) / len(obs_a)) - (sum(v for _, v in obs_b) / len(obs_b))
    boot_diffs = sorted(resample_precision(obs_a) - resample_precision(obs_b) for _ in range(n_boot))
    ci_lo = boot_diffs[int(0.025 * n_boot)]
    ci_hi = boot_diffs[int(0.975 * n_boot)]
    p_val = sum(1 for d in boot_diffs if d <= 0) / n_boot
    return round(obs_diff, 4), round(ci_lo, 4), round(ci_hi, 4), round(p_val, 4)


def run_analysis(results: dict) -> dict:
    """
    Aggregate per-(case, run) results into tier-level precision statistics.
    Returns analysis dict (also printed to stdout).
    """
    # Collect per-tier issue observations: (case_id, is_valid)
    tier_obs: dict[str, list[tuple[str, bool]]] = {'1/3': [], '2/3': [], '3/3': []}
    tier_counts: dict[str, dict[str, int]] = {
        '1/3': defaultdict(int),
        '2/3': defaultdict(int),
        '3/3': defaultdict(int),
    }

    planted_recovery = defaultdict(lambda: {'found_minority': 0, 'found_majority': 0, 'found_unanimous': 0, 'missed': 0})

    for key, result in results.items():
        if result.get('validation_error') and result.get('validation_errors') == ['api_failure']:
            continue
        case_id = key.split('__')[0]
        unique_issues = result.get('unique_issues', [])

        for ui in unique_issues:
            n_assessors = len(ui.get('assessors', []))
            cls = ui.get('classification', '')
            mid = ui.get('matched_id')

            if n_assessors == 1:
                tier = '1/3'
            elif n_assessors == 2:
                tier = '2/3'
            elif n_assessors == 3:
                tier = '3/3'
            else:
                continue  # skip clusters with 0 assessors (shouldn't happen)

            is_valid = cls in ('planted_match', 'valid_novel')
            tier_obs[tier].append((case_id, is_valid))
            tier_counts[tier][cls] += 1

            # Planted issue recovery tracking
            if cls == 'planted_match' and mid:
                if tier == '1/3':
                    planted_recovery[mid]['found_minority'] += 1
                elif tier == '2/3':
                    planted_recovery[mid]['found_majority'] += 1
                else:
                    planted_recovery[mid]['found_unanimous'] += 1

    # Per-tier precision + CIs
    tier_stats = {}
    for tier in ('1/3', '2/3', '3/3'):
        obs = tier_obs[tier]
        n = len(obs)
        prec, ci_lo, ci_hi = bootstrap_precision_ci(obs)
        counts = dict(tier_counts[tier])
        tier_stats[tier] = {
            'n_clusters': n,
            'precision': prec,
            'ci_lo': ci_lo,
            'ci_hi': ci_hi,
            'fp_rate': round(1 - prec, 4) if prec is not None else None,
            'planted_match': counts.get('planted_match', 0),
            'valid_novel': counts.get('valid_novel', 0),
            'false_claim': counts.get('false_claim', 0),
            'spurious': counts.get('spurious', 0),
        }

    # Key test: precision(1/3) - precision(3/3)
    diff_1_3, ci_lo_diff, ci_hi_diff, p_val = bootstrap_precision_diff(
        tier_obs['1/3'], tier_obs['3/3']
    )

    # Also test 1/3 vs 2/3
    diff_1_2, ci_lo_12, ci_hi_12, p_val_12 = bootstrap_precision_diff(
        tier_obs['1/3'], tier_obs['2/3']
    )

    # Overall precision across all tiers
    all_obs = tier_obs['1/3'] + tier_obs['2/3'] + tier_obs['3/3']
    all_prec, all_ci_lo, all_ci_hi = bootstrap_precision_ci(all_obs)
    all_counts: dict[str, int] = defaultdict(int)
    for tier in ('1/3', '2/3', '3/3'):
        for cls, count in tier_counts[tier].items():
            all_counts[cls] += count

    analysis = {
        'tier_stats': tier_stats,
        'precision_diff_1vs3': {
            'observed': diff_1_3, 'ci_lo': ci_lo_diff, 'ci_hi': ci_hi_diff, 'p_value': p_val,
            'interpretation': (
                'CI excludes 0 — minority precision is materially lower'
                if (ci_lo_diff is not None and ci_hi_diff is not None and ci_hi_diff < 0)
                else 'CI includes 0 — no significant precision difference' if ci_lo_diff is not None
                else 'insufficient data'
            ),
        },
        'precision_diff_1vs2': {
            'observed': diff_1_2, 'ci_lo': ci_lo_12, 'ci_hi': ci_hi_12, 'p_value': p_val_12,
        },
        'overall': {
            'n_clusters': len(all_obs),
            'precision': all_prec,
            'ci_lo': all_ci_lo,
            'ci_hi': all_ci_hi,
            **{k: v for k, v in all_counts.items()},
        },
        'planted_recovery': dict(planted_recovery),
        'validation_errors': sum(1 for r in results.values() if r.get('validation_error')),
        'total_scored': len(results),
    }

    # Print summary
    print()
    print("=" * 78)
    print("MINORITY-FLAGGED PRECISION ANALYSIS")
    print("=" * 78)
    print(f"\n{'Tier':<6} {'N':>6} {'Precision':>10} {'95% CI':>20} {'FP_rate':>8}  "
          f"{'planted':>8} {'novel':>8} {'false_clm':>10} {'spurious':>9}")
    print("-" * 78)
    for tier in ('1/3', '2/3', '3/3'):
        s = tier_stats[tier]
        ci = f"[{s['ci_lo']:.3f}, {s['ci_hi']:.3f}]" if s['ci_lo'] is not None else "N/A"
        prec_str = f"{s['precision']:.3f}" if s['precision'] is not None else "N/A"
        fp_str = f"{s['fp_rate']:.3f}" if s['fp_rate'] is not None else "N/A"
        print(f"{tier:<6} {s['n_clusters']:>6} {prec_str:>10} {ci:>20} {fp_str:>8}  "
              f"{s['planted_match']:>8} {s['valid_novel']:>8} {s['false_claim']:>10} {s['spurious']:>9}")
    print("-" * 78)
    ap = f"{all_prec:.3f}" if all_prec is not None else "N/A"
    aci = f"[{all_ci_lo:.3f}, {all_ci_hi:.3f}]" if all_ci_lo is not None else "N/A"
    print(f"{'ALL':<6} {len(all_obs):>6} {ap:>10} {aci:>20}")
    print()
    print(f"Precision diff (1/3 − 3/3): {diff_1_3:+.4f}  "
          f"95% CI [{ci_lo_diff:.4f}, {ci_hi_diff:.4f}]  p={p_val:.4f}"
          if diff_1_3 is not None else "Precision diff: N/A")
    print()
    interp = analysis['precision_diff_1vs3']['interpretation']
    print(f"Interpretation: {interp}")
    print()
    print(f"Validation errors: {analysis['validation_errors']} / {analysis['total_scored']} case-runs")
    print("=" * 78)

    return analysis

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


async def main():
    print(f"Loading case index from {CASES_FILE}...")
    case_index = load_case_index(CASES_FILE)
    critique_ids = set(case_index.keys())
    print(f"  Critique cases: {len(critique_ids)}")

    print(f"Loading assessor data from {INTERIM_DIR}...")
    assessor_data = load_assessor_data(INTERIM_DIR, critique_ids)
    print(f"  (case, run) pairs loaded: {len(assessor_data)}")

    # Verify completeness: every pair should have all 3 assessors
    incomplete = [(k, v) for k, v in assessor_data.items() if len(v) != 3]
    if incomplete:
        print(f"  WARNING: {len(incomplete)} incomplete pairs (not all 3 assessors)")

    # Load existing results if resuming
    existing = {}
    if args.resume and OUTPUT_FILE.exists():
        existing = json.load(open(OUTPUT_FILE)).get('results', {})
        print(f"Resuming: {len(existing)} case-runs already scored")

    # Build task list
    to_score = [(cid, run_idx) for (cid, run_idx) in sorted(assessor_data.keys())
                if f"{cid}__{run_idx}" not in existing]
    print(f"Case-runs to score: {len(to_score)} / {len(assessor_data)} total")

    if args.dry_run:
        print("DRY RUN — no API calls will be made")

    client = AsyncOpenAI(
        api_key=os.environ.get('OPENROUTER_API_KEY', ''),
        base_url='https://openrouter.ai/api/v1',
    )
    semaphore = asyncio.Semaphore(args.concurrency)

    tasks = [
        score_case_run(
            client, cid, run_idx,
            assessor_data[(cid, run_idx)],
            case_index[cid],
            semaphore, args.model, args.dry_run,
        )
        for cid, run_idx in to_score
    ]

    print(f"\nRunning {len(tasks)} scoring tasks (concurrency={args.concurrency})...")

    results = dict(existing)
    batch_size = 60
    with tqdm(total=len(tasks), unit='case-run') as pbar:
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i + batch_size]
            batch_results = await asyncio.gather(*batch, return_exceptions=True)
            for r in batch_results:
                if isinstance(r, BaseException):
                    print(f"\nERROR: {r}")
                elif r is not None:
                    key, result = r
                    results[key] = result
            pbar.update(len(batch))
            # Checkpoint after each batch
            json.dump(
                {'model': args.model, 'total_scored': len(results), 'results': results},
                open(OUTPUT_FILE, 'w'), indent=2,
            )

    print(f"\nDone. Scored {len(results)} case-runs total.")

    # Run analysis and embed in output
    analysis = run_analysis(results)
    json.dump(
        {'model': args.model, 'total_scored': len(results), 'results': results, 'analysis': analysis},
        open(OUTPUT_FILE, 'w'), indent=2,
    )
    print(f"\nSaved to {OUTPUT_FILE}")


if __name__ == '__main__':
    asyncio.run(main())
