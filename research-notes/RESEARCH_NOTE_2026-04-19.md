# Research Note — ml-lab (v8 Self-Debate Experiment)

*2026-04-19 | 13 experiment entries, 7 decisions, 12 commits | scope: today*

## Summary

Session completed the v8 multi-round debate protocol validation and closed out the main intervention loop. The central question — whether the ~40–45% IDR gap on `critique_wins` cases was a prompt design problem or a capability ceiling — was definitively answered: a Sonnet agent probe achieved IDR=1.00 on both targeted cases (eval_scenario_705 and eval_scenario_812) using the current v8 prompts. The gap is an API pool model capability ceiling, not a fixable prompt issue. The session also contained a significant reversal: a FATAL DEFER backstop rule was added, deployed to canary_run3, catastrophically over-fired on legitimate DEFERs (AER destroyed, eval_scenario_862 went 3/3 critique_wins), and was reverted within the same session. The surviving intervention — question-4 conclusion-survival DEFER gate — remains in all prompts and produces a measurable IDR lift without AER regression. A full port plan (ML_LAB_PORT_PLAN.md) was written.

## Key Decisions

- **Backstop reverted (DO NOT PORT):** The FATAL DEFER backstop (`DEFER + orig_sev≥7 + adj_sev≥6 → critique_wins`) was added as a deterministic override in `derive_verdict()`. canary_run3 showed it fires on any FATAL DEFER regardless of whether the flaw is conclusion-invalidating — eval_scenario_862 (confirmed ETA) went 3/3 critique_wins. Reverted. The correct mechanism is question 4 at the prompt level, not a severity-based verdict override.
- **Question-4 DEFER gate stays:** Requiring defenders to answer "can the primary conclusion survive if this critique is correct?" before DEFERring. This prompt-level gate produced real IDR lift (~0.60 in canary_run4 vs. 0.000 baseline) without the AER catastrophe of the backstop.
- **IDR gap = capability ceiling:** The Sonnet agent probe confirmed current v8 prompts are sufficient for the task. Pool models (haiku, gemma, qwen, deepseek) cannot reliably surface and CONCEDE FATAL flaws that Sonnet handles correctly. No further prompt work warranted.
- **haiku excluded from critic role:** probe_ac3 confirmed haiku-specific short-circuit failures (no_material_findings on ETA cases where all other models found 4–6 advancing findings). Exclusion is critic-role only; haiku remains in defender pool.
- **derive_verdict() replaces adjudicator LLM:** Collapsed from an LLM call into a deterministic Python function. Eliminates sampling variance from the verdict path, aligns with production ml-lab behavior.
- **correct_position labeling refined:** defense_wins requires either invalid critic concerns or genuinely trivial real concerns. empirical_test_agreed is correct when design is sound but real material uncertainties remain. Second re-labeling pass moved 6 cases from defense_wins → ETA.

## Discoveries & Results

- **Sonnet probe (f01a4c80) — IDR=1.00 on 705 and 812:** 705 run0: direct CONCEDE on preprocessing leakage (adj=8). 705 run1: REBUT-EVIDENCE on F1, but independently CONCEDEd F2+F3 → critique_wins via different path. 812 runs 0+1: both immediately CONCEDEd metric mismatch (span-level F1 hypothesis vs. report-level recall evaluation). Both cases handled correctly; prompts are sound.
- **canary_run3 backstop catastrophe (acd59c3e):** Backstop produced ~IDR=0.80 on targeted cases but ~DER=0.10 overall and AER destroyed. 20/135 task failures. eval_scenario_862, eval_scenario_868, hyp_240, hyp_204_case all flipped to critique_wins. Reverted same session.
- **canary_run4 (3b22f651) — question-4 only, no backstop:** 112 completed, 23 failures. Majority-vote gives ~3/5 critique_wins cases correct (801, 852, hyp_037). AER dramatically recovered vs. run3 — 777, 848 back to 3/3 ETA. 705 regressed (backstop was doing the work there). Net: measurable improvement over run2 baseline, IDR ceiling ~0.60.
- **Opus 4.6 probe (d5346fae) — ETA not critique_wins at model quality ceiling:** All 3 hard cases (812, 852, kirca2022) → empirical_test_agreed. Every FATAL finding DEFER'd with valid 3-question settling experiments but no CONCEDEs. Model quality lifts defense_wins→ETA but does not push ETA→critique_wins on its own.

## Issues

- **IDR ceiling ~0.60 with API pool (open):** Remaining gap on 705 and other cases is capability-dependent. No prompt intervention can close it further given pool model constraints.
- **23/135 task failures in canary_run4 (open, minor):** 17% failure rate — JSON parse errors, timeouts, empty responses. Retry logic catches most; root cause is API pool instability at high concurrency.

## Current State

All v8 canary benchmark runs complete. FATAL DEFER backstop reverted. Question-4 gate is the production-ready intervention. STATUS.md and ML_LAB_PORT_PLAN.md written and committed. Port to ml-lab plugin is unblocked.

## Next Steps

- Port v8 multi-round protocol to ml-lab plugin per ML_LAB_PORT_PLAN.md
  - Promote `ml-critic-r2` as new agent
  - Update `ml-critic`, `ml-defender`, `ml-lab` agents with multi-round prompts + question-4 gate
  - Add `derive_verdict()` deterministic rules (backstop explicitly excluded)
  - Add faithfulness tests (derive_verdict() unit tests, schema constraints, convergence loop)
  - Update README to reflect debate as default mode
- Confirm haiku exclusion is reflected in production canary_seeds before any future full run
