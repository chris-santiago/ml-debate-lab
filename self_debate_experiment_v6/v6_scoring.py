# v6_scoring.py
# /// script
# requires-python = ">=3.10"
# dependencies = ["openai>=1.0", "tqdm"]
# ///
"""
Phase 6 — Cross-Model Semantic Scoring via GPT-4o (OpenRouter)

Produces v6_rescored_idr_idp.json with per-file score vectors consumed by self_debate_poc.py.

Scope:
  - IDR (idr_documented, idr_novel): critique cases only (correct_position == 'critique')
  - IDP (idp_raw, idp_adj): critique cases only
  - ETD: mixed cases × debate conditions only
  - Defense + regular-mixed cases: nulls written; no API call needed

Output schema (keyed by filename):
  {filename: {idr_documented, idr_novel, idp_raw, idp_adj, etd, found_booleans}}

found_booleans is a per-issue dict used by scoring engine for ensemble union IDR.

Usage:
  uv run v6_scoring.py [--dry-run] [--concurrency 20] [--model openai/gpt-4o]
"""

import asyncio
import json
import os
import sys
import argparse
from pathlib import Path

from tqdm import tqdm

try:
    from openai import AsyncOpenAI
except ImportError:
    print("ERROR: openai package required. Run: uv run v6_scoring.py")
    sys.exit(1)

parser = argparse.ArgumentParser()
parser.add_argument('--dry-run', action='store_true', help='Skip API calls, produce null scores')
parser.add_argument('--concurrency', type=int, default=20)
parser.add_argument('--model', default='openai/gpt-4o')
parser.add_argument('--cases', default='benchmark_cases_verified.json')
parser.add_argument('--output', default='v6_rescored_idr_idp.json')
parser.add_argument('--resume', action='store_true', help='Skip files already in output')
args = parser.parse_args()

BASE_DIR = Path(__file__).parent
RAW_DIR = BASE_DIR / 'v6_raw_outputs'
OUTPUT_FILE = BASE_DIR / args.output
CASES_FILE = BASE_DIR / args.cases

ETD_CONDITIONS = {'isolated_debate', 'biased_debate', 'multiround', 'conditional_fm'}
CONDITIONS = ['baseline', 'isolated_debate', 'biased_debate', 'multiround', 'conditional_fm', 'ensemble_3x']


def load_case_index(cases_file):
    cases = json.load(open(cases_file))
    idx = {}
    for c in cases:
        cid = c['case_id']
        idx[cid] = {
            'correct_position': c['ground_truth']['correct_position'],
            'category': c.get('category', 'regular'),
            'must_find_ids': c['scoring_targets'].get('must_find_issue_ids', []),
            'must_not_claim_details': c['scoring_targets'].get('must_not_claim_details', []),
            'planted_issues': {
                pi['issue_id']: pi['description']
                for pi in c.get('planted_issues', [])
            },
        }
    return idx


def build_idr_idp_prompt(critic_raw, all_issues_raised, all_issues_adjudicated,
                          planted_descriptions, must_not_claim_details):
    """Build a single GPT-4o prompt that scores both IDR and IDP in one call."""
    issues_block = "\n".join(
        f"  [{iid}] {desc}"
        for iid, desc in planted_descriptions.items()
    )
    false_claims_block = "\n".join(
        f"  [{d['claim_id']}] CLAIM: {d['claim']}\n    WHY WRONG: {d['why_wrong']}"
        for d in must_not_claim_details
    ) if must_not_claim_details else "  (none)"

    raised_block = "\n".join(f"  - {issue}" for issue in all_issues_raised)
    adj_block = "\n".join(f"  - {issue}" for issue in (all_issues_adjudicated or all_issues_raised))

    return f"""You are evaluating a methodological critique of an ML research paper.

CRITIQUE TEXT:
{critic_raw}

---
TASK 1 — IDR (Issue Detection Rate):
For each PLANTED ISSUE below, determine if the critique semantically addresses it — meaning the critique raises a concern that substantially overlaps in meaning with the planted issue, even if not using the same words.

PLANTED ISSUES (must find):
{issues_block}

---
TASK 2 — IDP (Issue Detection Precision):
Review the issues listed below. For each FALSE CLAIM, determine if any raised issue substantially matches that false claim — meaning the critic raised an incorrect or misleading concern that maps to the false claim.

RAISED ISSUES (raw):
{raised_block}

RAISED ISSUES (adjudicated):
{adj_block}

FALSE CLAIMS (must not raise):
{false_claims_block}

---
OUTPUT: Respond with JSON only. No prose before or after.

{{
  "idr_found": {{
    "<issue_id>": true_or_false,
    ...
  }},
  "idp_raw_false_claim_ids": ["<claim_id_if_raised_in_raw>", ...],
  "idp_adj_false_claim_ids": ["<claim_id_if_raised_in_adjudicated>", ...],
  "idr_novel_count": <integer — count of issues in critique that are valid new concerns NOT in planted issues and NOT false claims>
}}"""


def build_etd_prompt(output_data):
    """Build ETD extraction prompt from debate transcript."""
    critic_raw = output_data.get('critic_raw', '')
    round_transcripts = output_data.get('round_transcripts', [])
    defender_raw = output_data.get('defender_raw', '')
    all_adj = output_data.get('all_issues_adjudicated', [])

    # Build debate transcript text
    if round_transcripts:
        transcript = "\n\n".join(
            f"[Round {r.get('round', i+1)}]\nCRITIC: {r.get('critic', '')}\nDEFENDER: {r.get('defender', '')}"
            for i, r in enumerate(round_transcripts)
        )
    elif defender_raw:
        transcript = f"CRITIC:\n{critic_raw}\n\nDEFENDER:\n{defender_raw}"
    else:
        transcript = f"CRITIC:\n{critic_raw}"

    adj_block = "\n".join(f"  - {i}" for i in all_adj) if all_adj else "  (none)"

    return f"""You are analyzing a debate about an ML research paper where both sides raise empirical questions.

DEBATE TRANSCRIPT:
{transcript}

ADJUDICATED ISSUES:
{adj_block}

---
TASK — ETD (Empirical Test Design):
Determine if the debate produced a valid empirical test specification — a concrete experimental design that could resolve the core dispute. Look for:
- condition: What specific experiment or test would resolve the dispute
- supports_critique_if: What result would confirm the critic's concern
- supports_defense_if: What result would vindicate the defense

OUTPUT: Respond with JSON only. No prose before or after.

{{
  "empirical_test": {{
    "condition": "<description of the test or null if absent>",
    "supports_critique_if": "<what result confirms the critique or null if absent>",
    "supports_defense_if": "<what result vindicates the defense or null if absent>",
    "ambiguous_if": "<what result is inconclusive or null if absent>"
  }}
}}"""


def compute_idp_from_false_claims(false_claim_ids, all_issues_count):
    """Convert false claim IDs to IDP score using the v6 binned scale."""
    if all_issues_count == 0:
        return 1.0
    n_invalid = len(false_claim_ids)
    n_valid = all_issues_count - n_invalid
    denominator = all_issues_count
    frac = n_valid / denominator
    if frac >= 0.9:
        return 1.0
    elif frac >= 0.5:
        return 0.5
    return 0.0


def compute_etd_from_dict(etd_dict):
    """Compute ETD float score from extracted empirical_test dict."""
    if not etd_dict or not isinstance(etd_dict, dict):
        return 0.0
    has_condition = bool(etd_dict.get('condition'))
    has_critique = bool(etd_dict.get('supports_critique_if'))
    has_defense = bool(etd_dict.get('supports_defense_if'))
    if has_condition and has_critique and has_defense:
        return 1.0
    elif has_condition and (has_critique or has_defense):
        return 0.5
    return 0.0


async def call_gpt4o(client, prompt, semaphore, model, filename=''):
    """Call GPT-4o via OpenRouter with JSON extraction."""
    async with semaphore:
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=1024,
                response_format={"type": "json_object"},
            )
            text = response.choices[0].message.content
            return json.loads(text)
        except json.JSONDecodeError as e:
            print(f"\nWARN: JSON parse error for {filename}: {e}")
            return None
        except Exception as e:
            print(f"\nERROR calling GPT-4o for {filename}: {e}")
            return None


async def score_file(client, output_path, case_meta, semaphore, model, dry_run):
    """Score a single output file. Returns (filename, score_dict)."""
    filename = output_path.name
    output_data = json.load(open(output_path))
    condition = output_data.get('condition', '')
    correct_position = case_meta.get('correct_position', 'critique')

    score = {
        'idr_documented': None,
        'idr_novel': None,
        'idp_raw': None,
        'idp_adj': None,
        'etd': None,
        'found_booleans': {},
    }

    # Defense or mixed: IDR/IDP are N/A
    if correct_position in ('defense', 'mixed'):
        # ETD only for mixed cases in debate conditions
        if correct_position == 'mixed' and condition in ETD_CONDITIONS:
            if dry_run:
                score['etd'] = 0.5  # placeholder
            else:
                prompt = build_etd_prompt(output_data)
                result = await call_gpt4o(client, prompt, semaphore, model, filename)
                if result:
                    etd_dict = result.get('empirical_test', {})
                    score['etd'] = compute_etd_from_dict(etd_dict)
                else:
                    score['etd'] = 0.0
        return filename, score

    # Critique case: IDR + IDP
    must_find_ids = case_meta['must_find_ids']
    planted_descriptions = {
        iid: case_meta['planted_issues'][iid]
        for iid in must_find_ids
        if iid in case_meta['planted_issues']
    }
    must_not_claim_details = case_meta['must_not_claim_details']

    if not must_find_ids:
        # No planted issues to find — IDR is vacuously 1.0
        score['idr_documented'] = 1.0
        score['idr_novel'] = 0.0
        score['idp_raw'] = 1.0
        score['idp_adj'] = 1.0
        return filename, score

    critic_raw = output_data.get('critic_raw', '')
    all_issues_raised = output_data.get('all_issues_raised', [])
    all_issues_adjudicated = output_data.get('all_issues_adjudicated', all_issues_raised)

    if dry_run:
        # Placeholder scores for dry run
        score['idr_documented'] = 0.75
        score['idr_novel'] = 0.0
        score['idp_raw'] = 1.0
        score['idp_adj'] = 1.0
        score['found_booleans'] = {iid: True for iid in must_find_ids}
        return filename, score

    prompt = build_idr_idp_prompt(
        critic_raw, all_issues_raised, all_issues_adjudicated,
        planted_descriptions, must_not_claim_details
    )
    result = await call_gpt4o(client, prompt, semaphore, model, filename)

    if result:
        idr_found = result.get('idr_found', {})
        idp_raw_false = result.get('idp_raw_false_claim_ids', [])
        idp_adj_false = result.get('idp_adj_false_claim_ids', [])
        novel_count = result.get('idr_novel_count', 0)

        # IDR: fraction of must_find issues found
        if must_find_ids:
            n_found = sum(1 for iid in must_find_ids if idr_found.get(iid, False))
            score['idr_documented'] = round(n_found / len(must_find_ids), 4)
            score['found_booleans'] = {iid: bool(idr_found.get(iid, False)) for iid in must_find_ids}
        else:
            score['idr_documented'] = 1.0
            score['found_booleans'] = {}

        # IDR novel: normalize by total must_find count as a proxy denominator
        denom = max(len(must_find_ids), 1)
        score['idr_novel'] = round(min(novel_count / denom, 1.0), 4)

        # IDP: binned precision
        score['idp_raw'] = compute_idp_from_false_claims(idp_raw_false, len(all_issues_raised))
        score['idp_adj'] = compute_idp_from_false_claims(
            idp_adj_false, len(all_issues_adjudicated or all_issues_raised)
        )
    else:
        # API failure fallback: use neutral scores
        score['idr_documented'] = 0.5
        score['idr_novel'] = 0.0
        score['idp_raw'] = 1.0
        score['idp_adj'] = 1.0
        score['found_booleans'] = {iid: False for iid in must_find_ids}

    return filename, score


async def main():
    print(f"Loading cases from {CASES_FILE}...")
    case_index = load_case_index(CASES_FILE)

    # Load existing results if resuming
    existing = {}
    if args.resume and OUTPUT_FILE.exists():
        existing = json.load(open(OUTPUT_FILE)).get('scores', {})
        print(f"Resuming: {len(existing)} files already scored")

    # Collect all output files to score
    all_files = sorted(RAW_DIR.glob('*.json'))
    if not all_files:
        print(f"ERROR: No files found in {RAW_DIR}")
        sys.exit(1)

    # Filter out already-done files when resuming
    to_score = [f for f in all_files if f.name not in existing]
    print(f"Files to score: {len(to_score)} / {len(all_files)} total")

    # Count by type
    critique_files = [f for f in to_score
                      if case_index.get(json.load(open(f)).get('case_id', ''), {}).get('correct_position') == 'critique']
    mixed_debate_files = [
        f for f in to_score
        if (case_index.get(json.load(open(f)).get('case_id', ''), {}).get('correct_position') == 'mixed'
            and any(c in f.name for c in ETD_CONDITIONS))
    ]
    print(f"  Critique cases (IDR+IDP): {len(critique_files)}")
    print(f"  Mixed debate cases (ETD): {len(mixed_debate_files)}")
    print(f"  Defense/other (nulls): {len(to_score) - len(critique_files) - len(mixed_debate_files)}")

    if args.dry_run:
        print("DRY RUN — no API calls will be made")

    client = AsyncOpenAI(
        api_key=os.environ.get('OPENROUTER_API_KEY', ''),
        base_url='https://openrouter.ai/api/v1',
    )

    semaphore = asyncio.Semaphore(args.concurrency)
    scores = dict(existing)

    # Process in batches with progress bar
    tasks = []
    for f in to_score:
        output_data = json.load(open(f))
        cid = output_data.get('case_id', '')
        case_meta = case_index.get(cid, {'correct_position': 'critique', 'must_find_ids': [], 'planted_issues': {}, 'must_not_claim_details': []})
        tasks.append(score_file(client, f, case_meta, semaphore, args.model, args.dry_run))

    print(f"\nRunning {len(tasks)} scoring tasks with concurrency={args.concurrency}...")

    # Process with progress bar
    completed = 0
    batch_size = 100
    with tqdm(total=len(tasks), unit='file') as pbar:
        for i in range(0, len(tasks), batch_size):
            batch = tasks[i:i+batch_size]
            results = await asyncio.gather(*batch, return_exceptions=True)
            for r in results:
                if isinstance(r, BaseException):
                    print(f"\nERROR: {r}")
                elif r is not None:
                    fname, score = r[0], r[1]
                    scores[fname] = score
            completed += len(batch)
            pbar.update(len(batch))

            # Save checkpoint every batch
            json.dump({'scores': scores, 'model': args.model, 'total': len(scores)},
                      open(OUTPUT_FILE, 'w'), indent=2)

    print(f"\nDone. Scored {len(scores)} files.")

    # Summary stats
    idr_vals = [s['idr_documented'] for s in scores.values() if s['idr_documented'] is not None]
    idp_vals = [s['idp_raw'] for s in scores.values() if s['idp_raw'] is not None]
    etd_vals = [s['etd'] for s in scores.values() if s['etd'] is not None]
    print(f"IDR documented: n={len(idr_vals)}, mean={sum(idr_vals)/len(idr_vals):.3f}" if idr_vals else "IDR: none")
    print(f"IDP raw:        n={len(idp_vals)}, mean={sum(idp_vals)/len(idp_vals):.3f}" if idp_vals else "IDP: none")
    print(f"ETD:            n={len(etd_vals)}, mean={sum(etd_vals)/len(etd_vals):.3f}" if etd_vals else "ETD: none")

    json.dump({'scores': scores, 'model': args.model, 'total': len(scores)},
              open(OUTPUT_FILE, 'w'), indent=2)
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == '__main__':
    asyncio.run(main())
