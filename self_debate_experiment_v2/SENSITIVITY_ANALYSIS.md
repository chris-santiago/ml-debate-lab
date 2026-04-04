# Sensitivity Analysis — Rubric Design Effects on Reported Lift

**Date:** 2026-04-04
**Triggered by:** Adversarial review of v2 findings using the ml-critic and ml-defender agents

---

## TL;DR

We ran the ml-critic and ml-defender agents against the v2 experiment's own findings. The critic identified two rubric choices that mechanically depress the baseline score before any measurement of the baseline's outputs occurs. We confirmed both choices are hardcoded in the scoring script and ran a sensitivity analysis from the existing results JSON.

**What we found:**
- The +0.586 reported lift includes a rubric design contribution that cannot currently be separated from genuine protocol reasoning advantage
- At a conservative alternative (DC=0.5 instead of DC=0.0), the lift drops to **+0.480** — still 4.8× the pre-registered +0.10 threshold, still a clear win
- The defense_wins finding (baseline scores 0.000 on all 5 exoneration cases) is **not affected** by the rubric choices — it holds under any DC assumption
- Two of the "baseline passes" reported in the JSON are inconsistent: those cases have DC=0.0 stored, which fails the per-dimension floor check — the pass flags appear to have been set before the override was applied
- The DRQ cap effect cannot be quantified: the raw transcript file (`self_debate_transcripts.py`) is missing

**Bottom line:** The protocol's advantage over single-pass reasoning is real and large. The precise magnitude is rubric-dependent. Five follow-on experiments are needed to establish how much of the lift is attributable to the debate structure vs. compute budget, rubric design, and benchmark construction choices.

---

## Background

After committing the v2 results, we ran `ml-critic` and `ml-defender` against the experiment's own findings — the protocol evaluating itself. The critic identified two rubric-level structural choices that mechanically depress the baseline score, independent of the baseline's actual reasoning quality:

1. **DC hardcoded to 0.0 for all baseline cases** (`self_debate_poc.py` line 142)
2. **DRQ capped at 0.5 for all baseline cases** (`self_debate_poc.py` lines 143–144)

Both overrides are labeled `# Structural enforcement (DEBATE.md resolutions)` in the code and are justified in the rubric documentation (`README.md §Evaluation Rubric`). The critic's argument: these overrides are definitional punishments applied before any measurement of the baseline's outputs occurs. The reported +0.586 lift cannot be decomposed into "protocol reasoning advantage" vs. "rubric design choices" without running the sensitivity.

---

## Confirmed: Both Overrides Are Real

```python
# self_debate_poc.py lines 136-144
# Structural enforcement (DEBATE.md resolutions)
if case["correct_position"] == "defense":
    debate_scores["IDR"] = None
    debate_scores["IDP"] = None
    baseline_scores["IDR"] = None
    baseline_scores["IDP"] = None
baseline_scores["DC"] = 0.0                                        # line 142
if baseline_scores.get("DRQ") is not None and baseline_scores["DRQ"] > 0.5:
    baseline_scores["DRQ"] = 0.5                                   # lines 143-144
```

DC applies to all 20 cases and is the widest-gap dimension in the aggregate (+0.867). DRQ applies to all 20 cases. Together they are the two most influential dimensions for the baseline aggregate.

---

## Sensitivity Analysis Results

**Updated 2026-04-04:** DRQ cap effect has been empirically resolved. A baseline scorer agent was run on all 9 DRQ=0.5 cases using the original benchmark prompts. The cap was binding on **all 9 cases** — every baseline response naturally earned DRQ=1.0 (correct resolution type identified), suppressed to 0.5 by the cap.

Five scenarios computed from confirmed scores:

| Scenario | Baseline Mean | Lift vs. Debate (0.970) | Baseline Passes | Pass % |
|---|---|---|---|---|
| **Current** (DC=0.0, DRQ≤0.5) | 0.384 | **+0.586** | 0* | 0% |
| **DC=0.5** | 0.490 | **+0.480** | 8 | 40% |
| **DC=0.5 + DRQ uncapped** | 0.529 | **+0.441** | 9 | 45% |
| **DC=1.0** | 0.596 | **+0.374** | 9 | 45% |
| **DC=1.0 + DRQ uncapped** | 0.635 | **+0.335** | 9 | 45% |

*Reported as 2 in the JSON, but those 2 cases (`broken_baseline_001`, `metric_mismatch_002`) have DC=0.0 stored, which fails the per-dimension floor check (all applicable dims ≥ 0.5). The `baseline_pass` flags were set before the DC override was applied. With DC=0.0 enforced consistently, correct baseline pass count is 0. See CONCLUSIONS.md correction note.

**DRQ cap finding:** The 9 baseline cases with DRQ=0.5 earned that score because the cap suppressed natural 1.0 scores — not because the baseline arrived at the wrong resolution type. Single-pass evaluation reliably identifies the correct resolution type (empirical_test_agreed or critique_wins) across all 9 cases. The cap penalizes the baseline for not having performed a structured debate, even when the baseline's conclusion matches the ideal resolution exactly.

---

## What the Sensitivity Tells Us

**The lift is real but the headline number reflects rubric design choices, not only protocol reasoning.** At DC=0.5 with DRQ uncapped (the most empirically grounded correction), the lift drops from +0.586 to **+0.441** — still 4.4× the pre-registered +0.10 threshold. The benchmark passes all three criteria under every scenario.

**The defense_wins finding is unaffected.** On the five defense_wins cases, the baseline scores DRQ=0.0 and FVC=0.0 because it structurally accepts the adversarial premise and reaches the wrong verdict — this is genuine protocol failure, not a rubric artifact. The fundamental finding holds under all scenarios.

**The DRQ cap is the larger contributor.** Removing the DC override (DC: 0.0→0.5) moves the baseline mean by +0.106. Removing the DRQ cap moves it by a further +0.039. Together they account for +0.145 of the headline +0.586 lift. At the upper bound (DC=1.0 + DRQ uncapped), the lift floor is +0.335 — still 3.35× the threshold.

**The "5.86× threshold" framing should be retired.** The multiplier is rubric-dependent. The honest range is **+0.335 to +0.586** depending on how structural absence of a defense role is penalized. The conservative defensible figure is **+0.441**.

---

## Defender's Rebuttal (Preserved)

The defender's position on the DC=0.0 override:

> The rubric defines DC as measuring whether the Defense concedes real planted issues and reaches the correct verdict type. The baseline has no Defense role. Scoring DC=0.0 is definitional, not punitive: a system with no defense agent earns no defense calibration credit. The question "what would the baseline's DC be with a defense role?" is counterfactual — the baseline is defined by the absence of that role.

The defender conceded that a sensitivity analysis was warranted, and that the +0.586 headline number should not be presented without qualification. The defense_wins advantage is architecturally robust; the non-defense_wins lift magnitude is rubric-dependent.

---

## Recommended Follow-On Experiments

In order of expected impact:

1. **Budget-matched ensemble baseline** (highest priority)
   Run three independent single-pass baseline responses per case, synthesize with a fourth call (no role differentiation). If this ensemble matches debate on non-defense_wins cases, the adversarial role mechanism claim is not established. If the debate protocol still outperforms on defense_wins cases, the isolation architecture is the load-bearing finding.

2. **Re-run with DRQ uncapped on baseline**
   Requires recovering or regenerating the raw transcript scores for the 9 DRQ=0.5 cases. Determine whether the cap was binding and by how much.

3. **Cross-model scorer validation**
   Have a different model family (e.g., GPT-4o) score the embedded transcripts against the same rubric without access to `must_find` labels. If IDR scores differ by >±0.1, self-scoring bias is material.

4. **Independent benchmark construction**
   Construct a parallel 20-case benchmark from published ML paper retractions, NeurIPS reproducibility failures, or Kaggle post-mortems — ground truth established by domain consensus, not the protocol designer. Run the same protocol and report IDR. If it drops below 0.85, benchmark leakage was material.

5. **Two-pass Defender fix tested on real_world_framing cases**
   Implement the proposed fix for the reasoning/label disconnect failure (analysis pass → verdict pass, with explicit instruction: "if your analysis identifies critical unaddressed flaws, your verdict is not defense_wins"). Re-run the 3 failed/partial cases. If failure rate drops to 0/3, the fix is tractable.

---

## Additional Issues Raised by ml-critic (Not Addressed by Sensitivity)

These were identified in the adversarial review but require new experiments to test, not just a recompute:

- **Compute confound:** The debate protocol runs 3-4× more tokens than the baseline. The lift may be partly a chain-of-thought aggregation effect rather than an adversarial role effect. Only a budget-matched ensemble test can separate these.
- **Convergence result is post-hoc with n=3 easy cases:** The easy difficulty stratum has 3 cases. The easy=0.833 convergence estimate is driven by a single case (defense_wins_003). The conclusion "convergence does not decrease with difficulty" is underpowered and should be treated as a not-supported secondary finding, not a confirmed finding.
- **Benchmark design leakage:** The entity that designed the benchmark, labeled the ground truth, and scored the outputs is the same model family. An independent benchmark from external sources is the only path to external validity.
