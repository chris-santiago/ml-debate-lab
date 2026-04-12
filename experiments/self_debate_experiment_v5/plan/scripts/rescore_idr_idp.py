# rescore_idr_idp.py
# /// script
# requires-python = ">=3.10"
# dependencies = ["openai>=1.0"]
# ///
"""
Isolated semantic re-scorer for IDR and IDP dimensions.

Fixes the orchestrator answer-key leakage identified in post_mortem 45eee14b /
issue c82df212. The original issues_found field was populated by the batch
orchestrator which had scoring_targets.must_find_issue_ids in its context window,
collapsing IDR/IDP to ~1.0 for all conditions including baseline.

This script re-scores IDR/IDP from raw agent text using an isolated LLM call
that receives only: (1) the review text, (2) one flaw description. No case ID,
condition label, expected verdict, or answer key is in the scorer context.

Scope: critique-category cases only (80 cases). Defense_wins cases (30) have
IDR/IDP = N/A by protocol and are skipped.

Output: v5_rescored_idr_idp.json

Usage (from self_debate_experiment_v5/):
    uv run plan/scripts/rescore_idr_idp.py [--max-concurrent 100] [--model <id>]
"""

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

from openai import AsyncOpenAI

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

parser = argparse.ArgumentParser()
parser.add_argument('--max-concurrent', type=int, default=100)
parser.add_argument('--model', default='anthropic/claude-haiku-4.5')
parser.add_argument('--raw-dir', default='v5_raw_outputs')
parser.add_argument('--cases-file', default='benchmark_cases_verified.json')
parser.add_argument('--output', default='v5_rescored_idr_idp.json')
parser.add_argument('--limit', type=int, default=0,
                    help='Limit to first N files for smoke testing (0 = no limit)')
args, _ = parser.parse_known_args()

RAW_DIR = Path.cwd() / args.raw_dir
CASES_FILE = Path.cwd() / args.cases_file
OUTPUT_FILE = Path.cwd() / args.output

# Text field priority list per condition (first non-null value wins)
TEXT_FIELD_PRIORITY = {
    'isolated_debate':    ['critic_raw', 'adjudication_raw'],
    'multiround':         ['critic_raw', 'adjudication_raw'],
    'forced_multiround':  ['critic_raw', 'adjudication_raw'],
    'baseline':           ['assessor_raw', 'adjudication_raw', 'critic_raw'],
    # ensemble handled separately (3 assessors + adjudication synthesis)
}
ENSEMBLE_ASSESSOR_FIELDS = ['assessor_1_raw', 'assessor_2_raw', 'assessor_3_raw']

# ---------------------------------------------------------------------------
# Scorer prompts (isolated — no answer-key context)
# ---------------------------------------------------------------------------

IDR_PROMPT = """\
You are a blinded methodology reviewer evaluator. You do not know the case ID, \
expected verdict, or which review condition produced this text.

REVIEW TEXT:
{text}

SPECIFIC FLAW TO CHECK:
{description}

Did the review text identify this specific methodological flaw? Answer "yes" if the \
review raised this concern or described its substance, even using different terminology. \
Answer "no" if the review did not mention this concern, only mentioned it in passing \
without substantive critique, or explicitly dismissed it.

Respond with JSON only — no other text:
{{"found": true, "rationale": "<one sentence>"}}
or
{{"found": false, "rationale": "<one sentence>"}}"""

IDP_PROMPT = """\
You are a blinded methodology reviewer evaluator. You do not know the case ID, \
expected verdict, or which review condition produced this text.

REVIEW TEXT:
{text}

FALSE ALARM TO CHECK:
{claim}

Did the review text flag this concern as a genuine methodological flaw? Answer "yes" \
if the review raised this specific concern as a problem. Answer "no" if the review \
did not raise it, or correctly noted it was not a flaw.

Respond with JSON only — no other text:
{{"raised": true, "rationale": "<one sentence>"}}
or
{{"raised": false, "rationale": "<one sentence>"}}"""


# ---------------------------------------------------------------------------
# Core scorer
# ---------------------------------------------------------------------------

async def score_idr_one(client, sem, text, description, retries=3):
    """Score whether text identified a specific flaw. Returns {"found": bool, "rationale": str}."""
    for attempt in range(retries):
        try:
            async with sem:
                resp = await client.chat.completions.create(
                    model=args.model,
                    messages=[{'role': 'user', 'content': IDR_PROMPT.format(
                        text=text[:6000],  # cap to avoid token overflow
                        description=description,
                    )}],
                    temperature=0,
                    max_tokens=128,
                )
            content = resp.choices[0].message.content or ''
            # Extract JSON from response (may have surrounding text)
            start = content.find('{')
            end = content.rfind('}') + 1
            result = json.loads(content[start:end] if start >= 0 else content)
            return {'found': bool(result.get('found', False)),
                    'rationale': result.get('rationale', '')}
        except Exception as e:
            if attempt == retries - 1:
                print(f'  WARN: IDR scorer failed after {retries} attempts: {e}', file=sys.stderr)
                return {'found': False, 'rationale': f'scorer_error: {e}', 'error': True}
            await asyncio.sleep(1.5 ** attempt)


async def score_idp_one(client, sem, text, claim, retries=3):
    """Score whether text raised a false alarm. Returns {"raised": bool, "rationale": str}."""
    for attempt in range(retries):
        try:
            async with sem:
                resp = await client.chat.completions.create(
                    model=args.model,
                    messages=[{'role': 'user', 'content': IDP_PROMPT.format(
                        text=text[:6000],
                        claim=claim,
                    )}],
                    temperature=0,
                    max_tokens=128,
                )
            content = resp.choices[0].message.content or ''
            start = content.find('{')
            end = content.rfind('}') + 1
            result = json.loads(content[start:end] if start >= 0 else content)
            return {'raised': bool(result.get('raised', False)),
                    'rationale': result.get('rationale', '')}
        except Exception as e:
            if attempt == retries - 1:
                print(f'  WARN: IDP scorer failed after {retries} attempts: {e}', file=sys.stderr)
                return {'raised': False, 'rationale': f'scorer_error: {e}', 'error': True}
            await asyncio.sleep(1.5 ** attempt)


# ---------------------------------------------------------------------------
# Per-file scoring
# ---------------------------------------------------------------------------

async def score_file(client, sem, path, case_scoring_targets, planted_issues):
    """
    Score one output file. Returns dict with rescored_idr, rescored_idp, details.
    Skips if text is not available (returns None).
    """
    d = json.load(open(path))
    condition = d.get('condition', '')
    verdict = d.get('verdict')

    # Determine review text
    if condition == 'ensemble':
        # Score each assessor separately; use majority for IDR, adjudication for IDP
        idr_texts = [d.get(f) for f in ENSEMBLE_ASSESSOR_FIELDS if d.get(f)]
        idp_text = d.get('adjudication_raw') or (idr_texts[0] if idr_texts else None)
    elif condition in TEXT_FIELD_PRIORITY:
        text = next((d.get(field) for field in TEXT_FIELD_PRIORITY[condition] if d.get(field)), None)
        idr_texts = [text] if text else []
        idp_text = text
    else:
        return None  # Unknown condition

    if not idr_texts and not idp_text:
        return None  # No scorable text

    must_find = case_scoring_targets.get('must_find_issue_ids', [])
    must_not_claim = case_scoring_targets.get('must_not_claim_details', [])

    # --- IDR scoring ---
    idr_detail = {}
    for i, issue_id in enumerate(must_find):
        if i >= len(planted_issues):
            break
        flaw_desc = planted_issues[i].get('description', '')
        if not flaw_desc:
            continue

        if condition == 'ensemble':
            # Score each assessor; majority vote
            assessor_results = await asyncio.gather(*[
                score_idr_one(client, sem, t, flaw_desc) for t in idr_texts
            ])
            found_count = sum(1 for r in assessor_results if r.get('found'))
            found = found_count >= 2  # majority of 3
            idr_detail[issue_id] = {
                'found': found,
                'assessor_results': assessor_results,
                'majority_threshold': '2/3',
            }
        else:
            result = await score_idr_one(client, sem, idr_texts[0], flaw_desc)
            idr_detail[issue_id] = result

    rescored_idr = (
        sum(1 for v in idr_detail.values() if v.get('found')) / len(must_find)
        if must_find else None
    )

    # --- IDP scoring ---
    idp_detail = {}
    if idp_text and must_not_claim:
        results = await asyncio.gather(*[
            score_idp_one(client, sem, idp_text, mnc.get('claim', ''))
            for mnc in must_not_claim
        ])
        for mnc, result in zip(must_not_claim, results):
            idp_detail[mnc['id']] = result

        false_alarms = sum(1 for v in idp_detail.values() if v.get('raised'))
        rescored_idp = 1.0 - (false_alarms / len(must_not_claim)) if must_not_claim else None
    else:
        rescored_idp = None

    return {
        'rescored_idr': round(rescored_idr, 4) if rescored_idr is not None else None,
        'rescored_idp': round(rescored_idp, 4) if rescored_idp is not None else None,
        'idr_detail': idr_detail,
        'idp_detail': idp_detail,
        'original_issues_found': d.get('issues_found'),
        'verdict': verdict,
        'condition': condition,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        print('ERROR: OPENROUTER_API_KEY not set', file=sys.stderr)
        sys.exit(1)

    client = AsyncOpenAI(
        api_key=api_key,
        base_url='https://openrouter.ai/api/v1',
    )

    cases = json.load(open(CASES_FILE))
    case_map = {c['case_id']: c for c in cases}

    # Critique cases only — defense_wins IDR/IDP = N/A by protocol
    critique_cases = {c['case_id'] for c in cases if c.get('category') == 'critique'}
    print(f'Critique cases to re-score: {len(critique_cases)}')

    sem = asyncio.Semaphore(args.max_concurrent)

    # Build task list
    files = sorted(RAW_DIR.glob('*.json'))
    critique_files = [
        f for f in files
        if any(f.name.startswith(cid + '_') for cid in critique_cases)
        and 'forced_multiround' not in f.name or True  # include all conditions
    ]
    # More precise filter
    critique_files = []
    for f in files:
        case_id = '_'.join(f.stem.split('_')[:-2]) if f.stem.count('_') >= 3 else None
        # Handle case IDs with underscores by trying known critique case IDs
        matched = next((cid for cid in critique_cases if f.name.startswith(cid + '_')), None)
        if matched:
            # Skip not-applicable stubs
            d = json.load(open(f))
            if d.get('note') == 'not_applicable_difficulty':
                continue
            critique_files.append((f, matched))

    if args.limit > 0:
        critique_files = critique_files[:args.limit]
        print(f'SMOKE TEST MODE: limiting to {args.limit} files')

    print(f'Files to score: {len(critique_files)}')

    # Dispatch all scoring tasks
    async def score_with_key(f, case_id):
        case = case_map[case_id]
        result = await score_file(
            client, sem, f,
            case.get('scoring_targets', {}),
            case.get('planted_issues', []),
        )
        return f.name, result

    tasks = [score_with_key(f, cid) for f, cid in critique_files]
    total = len(tasks)
    completed = 0
    results = {}

    print(f'Scoring {total} files with max_concurrent={args.max_concurrent}...')
    for coro in asyncio.as_completed(tasks):
        fname, result = await coro
        if result:
            results[fname] = result
        completed += 1
        if completed % 100 == 0 or completed == total:
            print(f'  {completed}/{total} files scored')

    # Write output
    with open(OUTPUT_FILE, 'w') as f:
        json.dump({
            'meta': {
                'model': args.model,
                'max_concurrent': args.max_concurrent,
                'total_files_scored': len(results),
                'critique_cases': len(critique_cases),
                'note': (
                    'IDR/IDP rescored from raw agent text using isolated semantic scorer. '
                    'Fixes orchestrator answer-key leakage (post_mortem 45eee14b, issue c82df212). '
                    'Defense_wins cases excluded — IDR/IDP N/A by protocol.'
                ),
            },
            'scores': results,
        }, f, indent=2)

    print(f'\nWrote {OUTPUT_FILE}')

    # Quick summary stats
    idr_vals = [v['rescored_idr'] for v in results.values() if v.get('rescored_idr') is not None]
    idp_vals = [v['rescored_idp'] for v in results.values() if v.get('rescored_idp') is not None]
    if idr_vals:
        print(f'Rescored IDR mean: {sum(idr_vals)/len(idr_vals):.4f} (n={len(idr_vals)})')
    if idp_vals:
        print(f'Rescored IDP mean: {sum(idp_vals)/len(idp_vals):.4f} (n={len(idp_vals)})')


if __name__ == '__main__':
    asyncio.run(main())
