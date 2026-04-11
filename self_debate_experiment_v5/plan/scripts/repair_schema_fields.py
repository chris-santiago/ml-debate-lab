# repair_schema_fields.py
# /// script
# requires-python = ">=3.10"
# ///
"""
Post-hoc repair for multiround/forced_multiround files missing:
  - Top-level: points_resolved, points_force_resolved, point_resolution_rate
  - rounds entries: verdict, points_resolved, points_open

Inferred values are conservative defaults (cannot reconstruct per-round metrics
without re-reading debate content). Repaired files are annotated with
schema_repair_note. Phase 10.5 hollow-round analysis is unreliable for
repaired files — see PHASE6_OBSERVATIONS.md.

Run from self_debate_experiment_v5/:
    uv run plan/scripts/repair_schema_fields.py
"""

import json
import sys
from pathlib import Path

RAW_DIR = Path.cwd() / 'v5_raw_outputs'

MULTIROUND_TOP = ['points_resolved', 'points_force_resolved', 'point_resolution_rate']
ROUND_SNAP = ['verdict', 'points_resolved', 'points_open']

repaired = 0
skipped = 0

for path in sorted(RAW_DIR.glob('*.json')):
    with open(path) as f:
        try:
            d = json.load(f)
        except Exception as e:
            print(f"SKIP (parse error): {path.name} — {e}")
            skipped += 1
            continue

    condition = d.get('condition', '')
    is_stub = d.get('note') == 'not_applicable_difficulty'

    if condition not in ('multiround', 'forced_multiround') or is_stub:
        continue

    needs_repair = False

    # Check top-level fields
    for field in MULTIROUND_TOP:
        if field not in d:
            needs_repair = True
            break

    # Check rounds entries
    rounds = d.get('rounds')
    if isinstance(rounds, list):
        for entry in rounds:
            if isinstance(entry, dict):
                for field in ROUND_SNAP:
                    if field not in entry:
                        needs_repair = True
                        break

    if not needs_repair:
        continue

    # --- Infer missing top-level fields ---
    final_verdict = d.get('verdict')
    all_issues = d.get('all_issues_raised') or []
    issues_found = d.get('issues_found') or []
    n_raised = len(all_issues)

    # Points resolved toward critique = issues_found that were actually raised
    # For defense_wins cases: 0 points resolved (all defended successfully)
    if final_verdict == 'critique_wins':
        pts_resolved = len(issues_found)
    else:
        pts_resolved = 0

    if 'points_resolved' not in d:
        d['points_resolved'] = pts_resolved
    if 'points_force_resolved' not in d:
        d['points_force_resolved'] = 0
    if 'point_resolution_rate' not in d:
        d['point_resolution_rate'] = (
            round(pts_resolved / n_raised, 4) if n_raised > 0 else 0.0
        )

    # --- Repair rounds entries ---
    if isinstance(rounds, list):
        n_rounds = len(rounds)
        for i, entry in enumerate(rounds):
            if not isinstance(entry, dict):
                continue
            if 'verdict' not in entry:
                # Conservative: use final verdict for all rounds
                entry['verdict'] = final_verdict
            if 'points_resolved' not in entry:
                # Put all resolved points in the last round; earlier rounds = 0
                entry['points_resolved'] = pts_resolved if i == n_rounds - 1 else 0
            if 'points_open' not in entry:
                cumulative = pts_resolved if i == n_rounds - 1 else 0
                entry['points_open'] = max(0, n_raised - cumulative)

    d['schema_repair_note'] = (
        'points_resolved/points_force_resolved/point_resolution_rate inferred post-hoc; '
        'per-round verdict and counts are conservative defaults (final verdict used for '
        'all rounds; resolved points placed in last round). '
        'Hollow-round detection in Phase 10.5 is unreliable for this file.'
    )

    with open(path, 'w') as f:
        json.dump(d, f, indent=2)

    repaired += 1

print(f"Repaired: {repaired}  Skipped (already valid or stub): {skipped}")
