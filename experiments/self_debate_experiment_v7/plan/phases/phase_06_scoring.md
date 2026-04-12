# Phase 6 — Cross-Model Scoring

> **Reminders:** `uv run` only. CWD: repo root. Cross-vendor scoring uses GPT-4o via OpenRouter.

## Required Reading
- [v6_lessons.md L5](../references/v6_lessons.md) — cross-vendor scoring rationale

---

## Steps

### 6.1 Run IDR/IDP scorer
GPT-4o scores Claude outputs — not Claude scoring itself. Uses `CROSS_VENDOR_API_KEY`.

```bash
cd experiments/self_debate_experiment_v7 && \
uv run pipeline/v7_scoring.py \
  --mode rescore \
  --input v7_raw_outputs \
  --cases benchmark_cases_v7_raw.json \
  --output v7_rescored_idr_idp.json \
  --scorer-model $CROSS_VENDOR_MODEL \
  --scorer-base-url $CROSS_VENDOR_BASE_URL \
  --scorer-api-key $CROSS_VENDOR_API_KEY
```

IDR scoring (bidirectional per v6 lesson):
- `idr_documented` — recall against `must_find` issues in `benchmark_cases_v7_raw.json`
- `idr_novel` — novel valid concerns not in `must_find` (secondary, stored separately)

IDP scoring (dual field):
- `idp_raw` — precision from `all_issues_raised`
- `idp_adj` — precision from `all_issues_adjudicated`

### 6.2 Validate scorer output
```bash
cd experiments/self_debate_experiment_v7 && \
uv run python -c "
import json
scores = json.load(open('v7_rescored_idr_idp.json'))
expected = set()
import glob
for f in glob.glob('v7_raw_outputs/*.json'):
    d = json.load(open(f))
    expected.add((d['case_id'], d['condition'], d['run_idx']))
scored = {(s['case_id'], s['condition'], s['run_idx']) for s in scores}
missing = expected - scored
print(f'Scored: {len(scored)}, Missing: {len(missing)}')
if missing: print('Sample missing:', list(missing)[:5])
"
```

### 6.3 Rule-based scoring (DRQ + FVC)
DRQ and FVC are rule-based — computed directly from output verdict fields:
- `FVC`: `verdict == correct_position` → 1.0, else 0.0
- `DRQ`: 1.0 if verdict in `acceptable_resolutions`, 0.5 if partial, 0.0 otherwise

These are computed in `v7_scoring.py` from `benchmark_cases_v7_raw.json` ground truth,
not by a separate API scorer.

---

## Verification
- [ ] `v7_rescored_idr_idp.json` has IDR/IDP entries for all 2,640 files
- [ ] `idr_documented` and `idr_novel` both present per entry
- [ ] `idp_raw` and `idp_adj` both present per entry
- [ ] No missing entries (scorer coverage = 100%)

## Outputs
- `v7_rescored_idr_idp.json`

## Gate
`v7_rescored_idr_idp.json` complete with 100% coverage.
