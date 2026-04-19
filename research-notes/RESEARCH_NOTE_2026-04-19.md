# Research Note — ml-lab (v8 Multi-Round Prototype)

*2026-04-19 | scope: this session (full day)*

## Summary
This session extended the v8 multi-round prototype with two diagnostic workstreams: (1) IDR/AER tradeoff
resolution via Options A+C (resolve/mitigate distinction + DEFER>CONCEDE reframing), and (2) model quality
comparison using Opus agents on harder cases. Both confirmed that the IDR failure is a prompt calibration
problem, not a model capability issue. A separate short-circuit failure mode was identified (critic returning
no_material_findings on ETA cases) and traced to claude-3-haiku and llama-4-maverick. Both models removed
from pool. The Stage 4 framing fix (explicit DEFER/CONCEDE conditions in user message) is in place but
unconfirmed — probe_stage4b was noisy and short-circuit removals did not resolve it.

## Key Decisions
- **Skip Phase 0.5** [da8f8113]: v7 prompts baseline run superseded — v7 failure mode already documented.
- **Collapse adjudicator to derive_verdict()** [c93e0fb6]: deterministic Python lookup, eliminates API call.
- **Refined correct_position labeling** [bdd068dd]: second re-labeling pass → final distribution 17/23/5.
- **DEFER requires substantive justification** [ed352ea]: 3-question test applied to both defender prompts.
- **Options A+C implemented** [50bf6b4]: resolve/mitigate distinction added to DEFENDER.md + DEFENDER_R2.md;
  DEFER reframed as stronger conclusion than CONCEDE. Confirmed working on ETA cases when full debate runs.
- **Stage 4 user message fix** [dd87a4f]: build_defender_r2_user_msg rewritten to name all three paths
  (REBUT/DEFER/CONCEDE) with explicit conditions, replacing binary "defend or concede" framing.
- **Exclude claude-3-haiku from pool entirely** [44a246c + today]: as critic → short-circuits on ETA cases;
  as defender → malformed JSON. Removed from models.json and all seeds.
- **Exclude llama-4-maverick from pool** [today]: same short-circuit pattern as haiku on critique_wins cases.
  Pool now 8 models.

## Discoveries & Results
- **Phase 0 existence proof** [7a83d0a4] `confirmed`: 4/4 → defense_wins on clean eval_scenario_858.
- **canary_multiround_run1** [923199c9] `confirmed`: DER=0.471, FDR=0.786, AER=0.739, IDR=0.000, MCC=−0.107.
- **canary_multiround_run2** [25c519a4] `inconclusive`: IDR 0.000→0.600 ✓; AER 0.739→0.217 ✗ (IDR/AER tradeoff).
- **probe_ac2** [1c24f469] `confirmed`: Options A+C fixed ETA prediction on 862 and 185 when full debate ran.
  Remaining defense_wins from critic short-circuits (haiku), not defender prompt failure.
- **probe_ac3** [4919d0ee] `confirmed`: Removing haiku from critic resolved short-circuits. Both ETA cases
  correctly predict empirical_test_agreed by majority vote (185: 3/3; 862: 2/3, one fluctuation absorbed).
- **Opus model quality** [d5346fae] `inconclusive`: Opus 4.6 produces ETA on all 3 harder cases.
  Correct on kirca2022 (GT=ETA). Misses 812 and 852 (GT=critique_wins) — no CONCEDEs produced at any model size.
  IDR failure is prompt calibration, not capability ceiling.
- **probe_stage4b** `inconclusive`: Stage 4 framing fix did not move critique_wins cases. 2/6 runs
  short-circuited (maverick). Full debate runs produced ETA, not critique_wins. Noisy result — needs
  clean re-run after maverick removal.

## Issues
- **Short-circuit failures** (partially resolved): haiku and maverick both returned no_material_findings on
  cases where other models found 4–6 advancing findings. Both removed. May be a broader critic calibration
  issue — watch for recurrence with remaining 8-model pool.
- **Stage 4 DEFER→CONCEDE gap** (open, high): critique_wins cases never produce CONCEDEs. Stage 4
  framing fix is in place but probe_stage4b was too noisy to confirm. Needs clean re-probe.
- **5 partial-run cases** (open, low): 5/45 cases completed only 1 run in canary_multiround_run2.

## Current State
Pool reduced to 8 models (haiku + maverick removed). All seeds patched. Stage 4 framing fix committed
but unvalidated. Next required action: clean probe_stage4 re-run with updated seeds to test whether
explicit DEFER/CONCEDE conditions move critique_wins cases off ETA.

## Next Steps
- Re-run probe_stage4 with new seeds (maverick removed) — get clean signal on Stage 4 framing fix
- If Stage 4 fix confirmed: run full canary_multiround_run3 on updated pool + prompts
- If Stage 4 fix fails: diagnose whether CONCEDE requires additional critic-side calibration
  (critic needs to produce findings the defender cannot rebut, not just finding findings)
- Watch for short-circuit recurrence with remaining pool — if it persists, consider critic prompt fix
