# cross_model_scorer.py
# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "openai>=1.0",
# ]
# ///
"""
Cross-vendor per-dimension validation (async rewrite).

v5 changes from v4:
- Uses OpenAI-compatible async API
- Strips <think>...</think> tags from responses
- Scores IDR, IDP, FVC (external model does not score DRQ or ETD)
- Runs on ALL cases concurrently (asyncio.Semaphore)
- Per-request timeout to prevent silent hangs
- --max-concurrent and --timeout flags
"""
import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path

from openai import AsyncOpenAI

parser = argparse.ArgumentParser()
parser.add_argument('--max-concurrent', type=int, default=20)
parser.add_argument('--timeout', type=float, default=60.0,
                    help='Per-request timeout in seconds')
parser.add_argument('--model', default=os.environ.get('CROSS_VENDOR_MODEL', ''))
parser.add_argument('--base-url', default=os.environ.get('CROSS_VENDOR_BASE_URL', ''))
parser.add_argument('--api-key', default=os.environ.get('CROSS_VENDOR_API_KEY', ''))
parser.add_argument('--output', default='cross_vendor_scores_v5.json')
parser.add_argument('--cases-file', default='benchmark_cases_verified.json')
args, _ = parser.parse_known_args()

if not args.api_key:
    print('ERROR: CROSS_VENDOR_API_KEY not set', file=sys.stderr)
    sys.exit(1)
if not args.base_url:
    print('ERROR: CROSS_VENDOR_BASE_URL not set', file=sys.stderr)
    sys.exit(1)
if not args.model:
    print('ERROR: CROSS_VENDOR_MODEL not set', file=sys.stderr)
    sys.exit(1)

OUTPUT_DIR = Path.cwd()


def build_prompt(case):
    must_find = case['scoring_targets'].get('must_find_issue_ids', [])
    mnc_details = case['scoring_targets'].get('must_not_claim_details', [])
    acceptable = case['scoring_targets'].get('acceptable_resolutions', [])

    mnc_text = '\n'.join(
        f"- [{m['id']}] {m['claim']} (why it is NOT a flaw: {m['why_wrong']})"
        for m in mnc_details
    ) if mnc_details else '(none)'

    return f"""You are independently evaluating an ML scenario. Assess the following.

SCENARIO:
{case['task_prompt']}

ISSUE IDs TO CHECK (for each: is this identifiable from the scenario?):
{json.dumps(must_find, indent=2)}

DESIGN CHOICES THAT ARE VALID (do NOT raise these as flaws):
{mnc_text}

ACCEPTABLE VERDICTS: {json.dumps(acceptable)}

Respond ONLY with a JSON object:
{{
  "issues_identified": {{"issue_id": true/false, ...}},
  "false_positives_raised": ["mnc_id", ...],
  "verdict": "critique_wins | defense_wins | empirical_test_agreed"
}}
No preamble, no explanation, no markdown fences."""


def parse_response(raw, must_find, acceptable):
    raw = re.sub(r'<think>.*?</think>', '', raw, flags=re.DOTALL).strip()
    if raw.startswith('```'):
        raw = raw.split('```')[1].lstrip('json').strip()
    # Extract JSON object
    start = raw.find('{')
    end = raw.rfind('}') + 1
    parsed = json.loads(raw[start:end] if start >= 0 else raw)

    identified = parsed.get('issues_identified', {})
    fp_raised = parsed.get('false_positives_raised', [])
    ext_verdict = parsed.get('verdict')

    ext_idr = round(
        sum(1 for v in identified.values() if v) / max(1, len(must_find)), 4
    ) if must_find else None

    valid_raised = [k for k, v in identified.items() if v and k in must_find]
    invalid_raised = fp_raised
    denom = len(valid_raised) + len(invalid_raised)
    ext_idp = round(len(valid_raised) / denom, 4) if denom > 0 else 1.0

    adjacents = {
        ('critique_wins', 'empirical_test_agreed'),
        ('empirical_test_agreed', 'critique_wins'),
        ('defense_wins', 'empirical_test_agreed'),
        ('empirical_test_agreed', 'defense_wins'),
    }
    if ext_verdict in acceptable:
        ext_fvc = 1.0
    elif ext_verdict and any((ext_verdict, acc) in adjacents for acc in acceptable):
        ext_fvc = 0.5
    else:
        ext_fvc = 0.0 if ext_verdict else None

    return ext_idr, ext_idp, ext_fvc, ext_verdict


async def score_case(client, sem, case, claude_scores, retries=2):
    cid = case['case_id']
    must_find = case['scoring_targets'].get('must_find_issue_ids', [])
    acceptable = case['scoring_targets'].get('acceptable_resolutions', [])
    prompt = build_prompt(case)

    ext_idr = ext_idp = ext_fvc = ext_verdict = None
    error = None

    for attempt in range(retries):
        try:
            async with sem:
                resp = await asyncio.wait_for(
                    client.chat.completions.create(
                        model=args.model,
                        max_tokens=600,
                        messages=[
                            {'role': 'system', 'content': 'You are a helpful assistant.'},
                            {'role': 'user', 'content': prompt},
                        ],
                    ),
                    timeout=args.timeout,
                )
            raw = resp.choices[0].message.content or ''
            ext_idr, ext_idp, ext_fvc, ext_verdict = parse_response(raw, must_find, acceptable)
            error = None
            break
        except Exception as e:
            if attempt == retries - 1:
                ext_idr = ext_idp = ext_fvc = ext_verdict = None
                error = str(e)
            else:
                await asyncio.sleep(2.0)

    claude = claude_scores.get(cid, {})
    deltas = {
        dim: round(val - (claude.get(dim) or 0), 4)
        if val is not None and claude.get(dim) is not None else None
        for dim, val in [('IDR', ext_idr), ('IDP', ext_idp), ('FVC', ext_fvc)]
    }

    status = f"IDR_delta={deltas.get('IDR')}" if not error else f"ERR:{error[:80]}"
    print(f'{cid}: {status}')

    return {
        'case_id': cid,
        'category': case['category'],
        'difficulty': case['difficulty'],
        'correct_position': case['ground_truth']['correct_position'],
        'model': args.model,
        'external': {'IDR': ext_idr, 'IDP': ext_idp, 'FVC': ext_fvc, 'verdict': ext_verdict},
        'claude_isolated_debate': claude,
        'deltas': deltas,
        'error': error,
    }


async def main():
    client = AsyncOpenAI(api_key=args.api_key, base_url=args.base_url)
    sem = asyncio.Semaphore(args.max_concurrent)

    with open(OUTPUT_DIR / args.cases_file) as f:
        cases = json.load(f)
    with open(OUTPUT_DIR / 'v5_results.json') as f:
        v5 = json.load(f)

    claude_scores = {
        r['case_id']: {
            dim: round(
                sum(run['scores'].get(dim, 0) or 0 for run in r['isolated_debate']['runs']
                    if run['scores'].get(dim) is not None) /
                max(1, sum(1 for run in r['isolated_debate']['runs']
                           if run['scores'].get(dim) is not None)), 4
            )
            for dim in ['IDR', 'IDP', 'DRQ', 'FVC']
        }
        for r in v5['cases']
    }

    print(f'Scoring {len(cases)} cases with model={args.model} max_concurrent={args.max_concurrent}')

    tasks = [score_case(client, sem, case, claude_scores) for case in cases]
    results = await asyncio.gather(*tasks)
    results = list(results)

    with open(OUTPUT_DIR / args.output, 'w') as f:
        json.dump(results, f, indent=2)

    valid = [r for r in results if r['external']['IDR'] is not None]
    print(f'\nParse rate: {len(valid)}/{len(results)} ({len(valid)/len(results):.1%})')

    if valid:
        for dim in ['IDR', 'IDP', 'FVC']:
            deltas = [r['deltas'][dim] for r in valid if r['deltas'].get(dim) is not None]
            if deltas:
                mean_delta = sum(deltas) / len(deltas)
                material = abs(mean_delta) > 0.1
                print(f'{dim} delta ({args.model} vs Claude): {mean_delta:+.4f} n={len(deltas)}')
                print(f'  {"MATERIAL (>0.1): bias may be present" if material else "Not material"}')

    print(f'\nWrote {args.output}')


if __name__ == '__main__':
    asyncio.run(main())
