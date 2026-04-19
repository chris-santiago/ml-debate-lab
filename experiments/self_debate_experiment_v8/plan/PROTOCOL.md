# Protocol

## Phase 0 — Existence Proof (Kill Switch)

**Before building anything, verify the capability exists.**

Take one obviously-sound defense case from the v7 benchmark (after audit). Hand-craft an ideal defender prompt: explicit exoneration instruction, explicit permission to dismiss critiques, full context of why the methodology is sound.

**Criteria:**
- Pass: the model produces `defense_wins` → the model CAN exonerate. The production prompt is the bottleneck. Proceed to Phase 1.
- Fail: the model CANNOT produce `defense_wins` even under ideal conditions → prompt iteration won't help. Execute fallback.

**Fallback (must not be skipped):**
If Phase 0 fails with the default Claude Opus model:
1. Dispatch the same ideal prompt to each model in the 12-model pool as defender (critic and context held constant)
2. If any pool model produces `defense_wins`: the problem is Anthropic-RLHF-specific. Cross-model dispatch is the solution — the pool model becomes the defender for all subsequent runs.
3. If no pool model produces `defense_wins`: the problem is architectural. Do not proceed. Report: "No model in the pool can exonerate sound methodology under ideal conditions. Prompt iteration will not solve this. Require architecture change."

Do not proceed to Phase 1 until Phase 0 passes.

---

## Phase 0.5 — Scoring Validation

**Run before any prompt changes. Run before reading transcripts.**

Take v7 prompts as-is — no modifications. Run them through the v8 evaluation pipeline using the penalty-aware scoring function. Record DER, IDR, FHR, ARR under the new metric.

**This answers the most important question in the experiment:** Is the problem in the prompts, or was it in the measurement?

| Result | Interpretation | Action |
|---|---|---|
| DER > 0.15 on v7 prompts unchanged | Scoring was the bottleneck. Prompts were capable — FVC made hedging look rational. | Prompt work closes the remaining gap. Reduce iteration budget. |
| DER 0.05-0.15 | Mixed. Measurement helped; prompts still need work. | Proceed with prompt iteration but expect fewer iterations needed. |
| DER ~0.00 | Prompts are genuinely broken under any fair scoring. | Full prompt iteration required. Proceed to Phase 1. |

**Secondary check — IDR under new scoring:**

If IDR drops below 0.75 on v7 prompts under the new scoring (i.e., the penalty function breaks existing detection), stop. The penalty function needs recalibration before any prompt work begins. A scoring function that degrades the working part of the system is not a better metric — it is a different problem.

This phase costs approximately 40 cases × 3 runs = 120 evaluations (canary-scale), or the full 280 × 3 = 840 evaluations for maximum signal. Start with the canary-scale run; expand if the result is ambiguous.

---

## Phase 1 — Failure Mode Diagnosis

Pull v7 multiround transcripts for all defense cases. Read them. Classify each failure by type:

| Failure Mode | What it Looks Like | Fix Target |
|---|---|---|
| Full concession | "The critic raises valid points..." | Defender prompt (Intervention B) |
| Partial concession | "While the critic is partially correct..." | Defender prompt (Intervention B) |
| Weak rebuttal | Defender argues but doesn't address the specific claim | Defender prompt (Intervention B) |
| Correct rebuttal, overridden | Defender makes strong argument, adjudicator sides with critic | Adjudicator (Intervention C) |
| Unfalsifiable critique | Critic raises something that can't be rebutted ("could have selection bias") | Critic prompt (Intervention A) |
| Noise accumulation | Critic raises 5 minor nits, defender concedes 2, adjudicator sees 2 concessions as evidence | Critic prompt (Intervention A) |

**Output:** A distribution across the 6 failure modes. This determines intervention priority:
- If majority are full/partial concessions → Intervention B first
- If majority are noise accumulation or unfalsifiable → Intervention A first
- If majority are correct rebuttals overridden → Intervention C first (rare, but changes the order)

**Do not guess the distribution.** Read the transcripts. Phase 1 is the only purely human-work phase.

---

## Phase 2 — Fast Iteration Loop

**Canary set:** 40 cases (20 defense / 10 regular / 10 mixed). Fixed throughout the loop.

**Model seeds:** Fixed for the duration of the loop. Same 3 model draws per canary case across all iterations. Seed file generated once before the loop begins (see MODELS.md for format).

**Per iteration:**
1. Make exactly one prompt change to exactly one agent (critic OR defender OR adjudicator — never multiple)
2. Run canary set: 40 cases × 3 runs = 120 evaluations
3. Score with penalty-aware function × VS weighting
4. Compare against previous iteration using MMD thresholds (see SCORING.md)
5. Accept or reject (see acceptance criteria)
6. Log to journal as `experiment` entry with changelog entry

**Intervention ordering:** A → B → C. Do not combine until each has been tested in isolation.

---

## Acceptance Criteria

**Accept a prompt change if:**
- Primary metric (weighted DER) improves by ≥ 0.08 (1 MMD)
- IDR does not drop by > 0.05
- FHR does not increase by > 0.05
- ARR does not drop by > 0.05

**Reject a prompt change if:**
- Primary metric does not move by ≥ 0.08
- Any regression exceeds its threshold
- Leading indicator does not move (the mechanism didn't activate)

**Important:** Do not use statistical significance for acceptance in the canary loop. With n=120, most differences are not significant. Use MMD. Statistical significance is assessed at the full benchmark run only.

---

## Stopping Rules

**Trigger full benchmark run when:** 3-5 consecutive accepted prompt changes without a rejection.

**Full benchmark run:**
- All v7 benchmark cases (280 cases after audit) × 3 random model draws = ~840 evaluations
- Model seeds NOT fixed — fully random draws for each run
- Score with penalty-aware function × VS weighting
- Compare against the re-baselined v7 results (v7 prompts under new scoring)

**If full benchmark does not reproduce canary gains:**
- If DER drops below canary estimate by > 0.10: diagnose. Likely cause: fixed seeds created systematic bias in canary. Re-examine which models were drawn in the fixed seed set.
- If DER drops by 0.05-0.10: acceptable variance. Report the full benchmark result, not the canary result.
- If IDR drops below 0.75: regression. Return to Phase 2 — the accepted changes degraded detection on a larger sample.

**Stopping rules for the iteration loop:**

| Condition | Action |
|---|---|
| 3-5 consecutive accepted changes → full benchmark passes | Done. Proceed to deliverables. |
| Max 15 iterations reached without 3 consecutive accepts | Declare intervention plateau. Report best configuration found. |
| Full benchmark run fails twice | Stop. Report: "Canary gains do not generalize to full benchmark." Diagnose seed bias. |
| Phase 0 fallback exhausted all pool models | Stop. Report architectural failure. |
| DER target not reached after 2 full benchmark runs | Stop. Report progress made and remaining gap. |

**Budget cap:** 2 full benchmark runs maximum.

---

## Iteration Log Format

Each iteration is tracked in the journal as an `experiment` entry and in the prompt changelog:

**Journal entry fields:**
- `type`: experiment
- `description`: "[agent]-v{N}: {one-sentence change description}"
- `verdict`: confirmed / refuted / inconclusive
- `metric`: weighted DER
- `result`: "DER {before} → {after}, IDR {before} → {after}, FHR {before} → {after}"
- `linked_hypothesis_id`: the hypothesis this iteration tests

**Prompt changelog entry:** see PROMPTS.md for template.

---

## Pre-Run Checklist

Before the first canary iteration:

- [ ] Phase 0 existence proof passed
- [ ] Phase 0.5 scoring validation complete — v7 prompts re-scored under penalty-aware function, DER baseline recorded
- [ ] IDR confirmed stable under new scoring (not degraded below 0.75)
- [ ] Phase 1 transcript reading complete — failure mode distribution recorded
- [ ] Ground truth audit complete (CASES.md Gate 1)
- [ ] Taxonomy coverage check complete (CASES.md Gate 2)
- [ ] v7 prompts re-scored under penalty-aware function — baseline established
- [ ] Model pool validated on OpenRouter (all 12 available)
- [ ] Technical architecture decision made (MODELS.md)
- [ ] Model seed file generated and saved
- [ ] DCR taxonomy defined (METRICS.md)
- [ ] Mixed-case calibration metric defined (ARR or alternative — METRICS.md)
- [ ] Acceptance thresholds set (PROMPTS.md)
- [ ] Phase 0 fallback specified (OBJECTIVE.md)
