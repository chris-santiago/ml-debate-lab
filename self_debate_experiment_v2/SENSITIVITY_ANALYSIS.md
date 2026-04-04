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

Computed from `self_debate_results.json` without re-running API calls. Three scenarios for baseline DC:

| Scenario | Baseline Mean | Lift vs. Debate (0.970) | Baseline Passes | Pass % |
|---|---|---|---|---|
| **Current** (DC=0.0 hardcoded) | 0.384 | **+0.586** | 0* | 0% |
| **DC=0.5** (conservative: partial calibration credit) | 0.490 | **+0.480** | 8 | 40% |
| **DC=1.0** (upper bound) | 0.596 | **+0.374** | 9 | 45% |

*Reported as 2 in the JSON, but those 2 cases (`broken_baseline_001`, `metric_mismatch_002`) have DC=0.0 stored, which fails the per-dimension floor check (all applicable dims ≥ 0.5). The `baseline_pass` flags in the JSON appear to have been set before the DC override was applied. This is a secondary inconsistency in the results.

**DRQ cap effect:** Cannot be quantified. The `self_debate_transcripts.py` file (source of raw pre-override scores) is missing. All stored baseline DRQ values are exactly 0.0 or 0.5 — indistinguishable from natural scores at those values or from values that were capped downward. Nine cases are marked with DRQ=0.5 where the cap may have been binding.

---

## What the Sensitivity Tells Us

**The lift is real but overstated.** At DC=0.5 (a conservative assumption — baseline can express partial calibration in free-text but earns no credit for structured defense), the lift drops from +0.586 to +0.480. This is still 4.8× the pre-specified +0.10 threshold, and the benchmark still passes all three criteria. The protocol's advantage is genuine.

**The defense_wins finding is unaffected by the DC override.** On the five defense_wins cases, the baseline scores DRQ=0.0 and FVC=0.0 because it structurally accepts the adversarial premise and reaches the wrong verdict — not because DC is forced to 0.0. Removing the DC override on defense_wins cases raises the baseline mean on those cases from 0.0 to 0.167 (DC=0.5) or 0.333 (DC=1.0), but the fundamental finding — the baseline cannot exonerate valid work — remains intact.

**The "5.86× threshold" framing should be qualified.** The precise multiplier depends on rubric design choices that were made before the experiment but that now appear non-neutral. Reporting the lift as "+0.586 (rubric-adjusted) / +0.480 (DC=0.5 sensitivity)" is more honest than the single number.

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
