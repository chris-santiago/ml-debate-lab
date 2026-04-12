# Phase 6 — Cross-Model Scoring

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - CWD: Bash tool CWD is always repo root (`ml-lab/`). Prefix all bash commands with `cd self_debate_experiment_v6 &&`.
> - Subagent context: authenticated Claude Code session. No direct API calls.

## Required Reading
- [design_decisions.md §7](../references/design_decisions.md#7-scoring-dimensions) — scoring dimensions, which scorer applies to each, union IDR split rule
- [schema_b.md](../references/schema_b.md) — which Schema B fields each scorer reads

## Key Constraints
- GPT-4o scorer must have **no access to ground truth** (`ground_truth`, `scoring_targets`, `planted_issues`) — scoring isolation.
- Bidirectional IDR: two separate scores per file; `idr_documented` is primary.
- Dual IDP: `idp_raw` (from `all_issues_raised`) is the v5-comparable primary; `idp_adj` (from `all_issues_adjudicated`) is secondary.
- ETD scoring applies to mixed-case debate outputs only (`ETD_CONDITIONS`).

---

## Steps

### 6.1 GPT-4o scoring pass — IDR (all 2,160 files)

**Bidirectional IDR — two scores per file:**
- `idr_documented` — recall against `scoring_targets.must_find_issue_ids` from benchmark cases; this is the primary IDR score
- `idr_novel` — novel valid concerns the debate surfaced that the reproducer missed (GPT-4o-judged); secondary, stored separately

GPT-4o receives: `critic_raw` (or assessor output for ensemble), `must_find_issue_ids`  
GPT-4o does NOT receive: `ground_truth`, full `planted_issues` records, `acceptable_resolutions`

### 6.2 GPT-4o scoring pass — IDP (all 2,160 files)

**Dual IDP — two scores per file:**
- `idp_raw` — precision computed from `all_issues_raised` (Critic raw output; current definition; v5-comparable)
- `idp_adj` — precision computed from `all_issues_adjudicated` (adjudicator synthesis; new field added in Phase 0)

GPT-4o receives: the relevant issues list + `scoring_targets.must_not_claim`

### 6.3 GPT-4o scoring pass — ETD (mixed-case debate outputs only)

ETD scoring applies to outputs from:
`{isolated_debate, multiround, conditional_fm, biased_debate}` × mixed cases only.

GPT-4o receives: full debate transcript (critic + defender exchange); scores whether the empirical test specification meets the ETD rubric.
Full credit (1.0) and partial credit (0.5) rates stored separately.

### 6.4 Rule-based scoring — DRQ and FVC (all 2,160 files)

Run `self_debate_poc.py` scoring engine for:
- `DRQ` — decision resolution quality (rule-based, reads `ideal_debate_resolution.type`)
- `FVC` — final verdict correctness (rule-based, reads `acceptable_resolutions`)

These do not require external API calls.

### 6.5 Store per-assessor `found` booleans for ensemble union IDR
For each ensemble file, store `assessor_{1,2,3}_found` boolean per `must_find_issue_id`.
Union IDR computation in Phase 7 uses these booleans.

### 6.6 Compile into `v6_rescored_idr_idp.json`
Merge all scoring results into a single output file with the full score vector per run:
`{case_id, condition, run_idx, idr_documented, idr_novel, idp_raw, idp_adj, drq, fvc, etd}`

```bash
cd self_debate_experiment_v6 && uv run python compile_scores.py
```

---

## Verification
- [ ] Cross-scorer: flag if GPT-4o vs Claude IDR delta > 0.50 (checked in Phase 9; prepare data here)

## Outputs
- `v6_rescored_idr_idp.json` (full score vector for all 2,160 runs)

## Gate
All 2,160 files scored. `v6_rescored_idr_idp.json` complete with all required score fields.
