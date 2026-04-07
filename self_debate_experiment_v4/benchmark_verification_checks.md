# Benchmark Verification Check Definitions

The CASE_VERIFIER in Phase 1 applied 12 checks to each case. These definitions are the canonical reference for interpreting `checks_passed` and `checks_failed` arrays in `benchmark_verification.json`.

| # | Check | Description |
|---|-------|-------------|
| 1 | No target leakage | Correct verdict is not inferrable from `case_id` or the first sentence of `task_prompt` |
| 2 | Ground truth unambiguous | `ideal_debate_resolution.type` is clearly correct; domain experts would agree |
| 3 | Must-find items findable | Each item in `scoring_targets.must_find_issue_ids` is identifiable from `task_prompt` alone |
| 4 | Scenario realistic | The scenario is plausible as something a real ML team would encounter |
| 5 | Empirical test diagnostic | For `empirical_test_agreed` cases: `supports_critique_if` and `supports_defense_if` specify distinct falsifiable outcomes |
| 6 | Schema complete | `planted_issues` has `severity`; `acceptable_resolutions` is non-empty; `verifier_status` is "pending"; `notes` field present |
| 7 | Defense_wins justification in prompt | For defense cases: the justification is explicitly stated in `task_prompt` |
| 8 | Mixed-position genuinely two-sided | Both positions are defensible from `task_prompt` alone |
| 9 | Hard cases require domain expertise | For hard non-defense_wins cases: the must-find flaw requires knowledge beyond general ML intuition; if discoverable by standard ML reasoning, mark REVISE |
| 10 | Critique cases have red herring features | For non-defense_wins cases: the scenario contains at least one feature that looks suspicious but is actually valid; cases without `must_not_claim` are noted as weaker |
| 11 | Defense_wins external grounding | At least 3 defense_wins cases are grounded in externally verifiable ML methodology (flag if fewer than 3; not a REJECT condition) |
| 12 | Difficulty label validation | Difficulty is defined by expected rubric performance on single-pass baseline: easy ≥ 0.85, medium 0.55–0.85, hard expected to fail ≥ 2 rubric dimensions (IDR, DRQ, ETD, DC, IDP) |

## Outcome summary

- **53 cases:** verdict = `keep` → `verifier_status = "verified"` in `benchmark_cases_verified.json`
- **1 case (`eval_scenario_035`):** verdict = `revise` (Check 12 failed — difficulty mislabeled medium, should be hard); excluded from `benchmark_cases_verified.json`
- **0 cases:** verdict = `reject`
- **Defense_wins externally grounded:** 11 of 11 cases (threshold of 3 met)
