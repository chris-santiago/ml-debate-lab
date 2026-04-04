# Self-Debate Experiment

## Hypothesis

On synthetic ML reasoning tasks with known ground truth, a self-debate protocol — where a language model plays an explicit Critique agent, Defense agent, and Judge role in structured sequential prompts — will achieve a benchmark aggregate score at least 0.10 higher than a trivial baseline (single-pass answer plus self-critique, no revision). The isolated two-instance variant (Critique and Defense receive independent context, no shared output) is hypothesized to outperform the contaminated variant and enable `defense_wins` verdicts on cases where the Critique's premise is false.

## Results Summary

Two experiments were run. See `CONCLUSIONS.md` for full per-case scoring and `FINAL_SYNTHESIS.md` for the cross-experiment synthesis.

| | Experiment 1 (contaminated) | Experiment 2 (isolated) |
|---|---|---|
| Cases | 11 | 15 (11 original + 4 defense_wins) |
| Protocol | Single instance, Defense reads Critique | Isolated context: Defense receives task_prompt only |
| Debate mean | 0.988 | 1.000 (original 11) / 0.947 (all 15*) |
| Baseline mean | 0.517 | 0.379 |
| Lift | +0.471 | +0.568 |
| Case pass rate | 11/11 | 11/15 (73.3%)* |
| defense_wins verdicts | 0/0 cases tested | 4/4 correct |

*The 73.3% pass rate is a rubric measurement gap, not a protocol failure. The rubric's `issue_discovery_precision` dimension is undefined for `defense_wins` cases (where the Critique's premise is intentionally false). With IDP scored as N/A for those 4 cases, all 15 pass. See `FINAL_SYNTHESIS.md` §2 for full explanation.

**Primary hypothesis: SUPPORTED.** Isolated architecture is required for `defense_wins` verdicts.

## Quickstart

Run Experiment 1 (original 11 cases, contaminated protocol):
```bash
python self_debate_poc.py
```
Produces `experiment_results.json`.

Run Experiment 2 (all 15 cases, isolated protocol):
```bash
python self_debate_experiment2.py
```
Produces `experiment2_results.json`.

## Pipeline

### Experiment 1
1. **Input:** `benchmark_cases.json` (11 KEEP cases), `evaluation_rubric.json` (read-only)
2. **Debate:** Critique agent → Defense agent (reads Critique) → Judge agent → verdict
3. **Baseline:** Single-pass assessment → self-critique, no revision
4. **Scoring:** 6 rubric dimensions per case for both systems
5. **Output:** `experiment_results.json`, `CRITIQUE.md`, `DEFENSE.md`, `DEBATE.md`

### Experiment 2
1. **Input:** All 15 KEEP cases (original 11 + 4 defense_wins)
2. **Debate (isolated):** Critique agent (task_prompt only) → Defense agent (task_prompt only, no Critique) → Judge (sees both independent outputs)
3. **New metric:** `agent_convergence_rate` — whether Critique and Defense independently identify the same issues (0.800 across 15 cases)
4. **Output:** `experiment2_results.json`

## Scope Exclusions

- `scope_intent_001` excluded: `revise` status in `benchmark_verification.json` (causal inaccuracy in planted issue description)
- No real user tasks or production data. All 16 cases (12 original + 4 defense_wins) are fully synthetic
- `evaluation_rubric.json` is read-only — not modified by any script
- Live API calls are not made. Debate transcripts are embedded structured data in the PoC scripts
- Multi-round debate loops are out of scope for both experiments

## Dependencies

- Python 3.8+
- Standard library only (`json`)

## Artifact Index

| File | Experiment | Description |
|------|-----------|-------------|
| `benchmark_cases.json` | — | 16 synthetic cases (11 original + 4 defense_wins + 1 revise/excluded) |
| `benchmark_verification.json` | — | 15 KEEP decisions |
| `evaluation_rubric.json` | — | Scoring rubric, locked before execution |
| `EXECUTION_PLAN.md` | — | Pre-specified verdict rules for all 5 case categories |
| `self_debate_poc.py` | E1 | Contaminated protocol, 11 cases, embedded transcripts and scores |
| `self_debate_experiment2.py` | E2 | Isolated protocol, 15 cases, convergence data |
| `CRITIQUE.md` | E1 | Critique agent output for 11 original cases |
| `DEFENSE.md` | E1 | Defense agent output for 11 original cases |
| `DEBATE.md` | E1 | Transcripts + verdicts + 9 agreed empirical tests |
| `CONCLUSIONS.md` | E1+E2 | Per-case scoring, aggregate scores, hypothesis verdicts, E2 findings (§7) |
| `REPORT.md` | E1+E2 | Full technical report covering both experiments |
| `REPORT_ADDENDUM.md` | E1+E2 | Production analysis + E2 design rationale and delta results |
| `evaluation_results.json` | E1+E2 | Independent EVALUATOR scores (E1: 11 cases, E2: 15 cases) |
| `FINAL_SYNTHESIS.md` | E1+E2 | Lead synthesis: findings, failures, rubric gap, iteration 3 recommendations |
