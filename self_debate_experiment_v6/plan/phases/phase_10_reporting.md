# Phase 10 — Reporting

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - CWD: Bash tool CWD is always repo root (`ml-debate-lab/`). Prefix all bash commands with `cd self_debate_experiment_v6 &&`.
> - Subagent context: authenticated Claude Code session. No direct API calls.

## Required Reading
None specific — all reference documents consumed in prior phases.

## Key Constraints
- Run `/artifact-sync` after all artifacts are complete; do not mark work done before the coherence audit passes.

---

## Steps

### 10.1 `REPORT.md`
Full experiment report: all hypothesis results with tables, bootstrap CIs, effect sizes, per-dimension breakdowns, failure attribution taxonomy, limitations, and related work.

### 10.2 `REPORT_ADDENDUM.md`
Production deployment recommendation: should the ml-lab debate protocol be used in production, under what conditions, and at what compute cost?

### 10.3 `ENSEMBLE_ANALYSIS.md`
Union IDR analysis: ensemble vs isolated_debate comparison. Document the split rule (union IDR for recall, majority-vote for verdict) and its effect on the H2 result.

### 10.4 `PEER_REVIEW_R1.md`
Dispatch `research-reviewer` (Opus) against `REPORT.md`.

Agent prompt:
```
Conduct a peer review of self_debate_experiment_v6/REPORT.md.

This is a benchmark experiment testing whether an adversarial ML debate protocol
outperforms single-pass critique on 120 ML methodology review cases. The pre-registered
hypotheses are in HYPOTHESIS.md. Focus on:
1. Whether conclusions are supported by the reported data
2. Whether the null/positive results are correctly framed
3. Any statistical concerns (CI interpretation, multiple comparisons, effect size adequacy)
4. Whether the limitations section is complete

Read: self_debate_experiment_v6/REPORT.md
Read: self_debate_experiment_v6/HYPOTHESIS.md
```

If Round 1 finds MAJOR issues, dispatch a second review round.

### 10.5 `FINAL_SYNTHESIS.md`
Orchestrator synthesis: pull together `v6_results.json`, `SENSITIVITY_ANALYSIS.md`, `CONCLUSIONS.md`, `CROSS_VENDOR_VALIDATION.md`, and peer review feedback into a final executive synthesis.

### 10.6 `/artifact-sync` and coherence audit
```
/artifact-sync
```
This updates all artifacts and runs a three-check coherence audit (conflicts, staleness, completeness). Do not mark Phase 10 complete until the coherence audit passes.

---

## Verification
- [ ] `/artifact-sync` run after Phase 10 and coherence audit passes

## Outputs
- `REPORT.md`
- `REPORT_ADDENDUM.md`
- `ENSEMBLE_ANALYSIS.md`
- `PEER_REVIEW_R1.md`
- `FINAL_SYNTHESIS.md`

## Gate
All artifacts written. `/artifact-sync` coherence audit passes with no conflicts or staleness flags.
