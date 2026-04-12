# v5 Hypothesis — Pre-Registration

## H1 (Primary)

**Claim:** The isolated self-debate protocol (ml-critic + ml-defender each receiving only the
task prompt, orchestrator adjudicates) will achieve a benchmark aggregate score at least +0.10
higher than a single-pass baseline on the fair-comparison dimensions (IDR, IDP, DRQ, FVC) —
dimensions where baseline has equal structural agency.

**Motivation:** Adversarial role separation is hypothesized to force engagement with both sides
of a methodological question, producing better-typed verdicts and catching false positives that
correlated parallel assessors miss. This is a motivating rationale, not a claim established by
H1. The mechanism claim is tested by H2. H1 passing establishes operational value; H2 passing
establishes structural attribution. See H1 × H2 outcome matrix in EXECUTION_PLAN.md.

**Primary metrics:** IDR, IDP, DRQ, FVC (fair-comparison set)

**Secondary metrics:** DC, ETD (debate-internal; not used in lift calculation against baseline)

---

## Conditions

| Condition | Description |
|-----------|-------------|
| `isolated_debate` | Critic and Defender each receive only task_prompt; orchestrator adjudicates |
| `multiround` | Defender sees Critique; up to 4 rounds; ml-lab protocol |
| `forced_multiround` | Same as multiround but minimum 2 rounds enforced; hard cases only |
| `ensemble` | 3 independent assessors + ETD-constrained synthesizer |
| `baseline` | Single-pass, no structure |

---

## N/A Rationale

- **DC = N/A for baseline:** No Defender role exists in baseline; penalizing its absence is not a
  valid comparison. Consistent with ETD N/A treatment for inapplicable case types. Pre-registered.
- **ETD = N/A for ensemble and baseline:** No adversarial exchange occurs in these conditions;
  scoring ETD for conditions that never had adversarial exchange confounds the comparison.
- **DC = N/A for defense_wins cases:** IDR/IDP also N/A per v3 convention.

---

## Secondary Hypotheses

**(H2)** Debate outperforms ensemble on IDR/IDP/DRQ/FVC (fair-comparison dimensions).

**(H3)** Ensemble FVC >= 0.5 on >= 60% of defense_wins cases. (Per v4 DEBATE Issue 7 resolution:
DC=N/A for all defense cases; FVC is used as the observable proxy criterion.)

**(H4)** Forced multiround outperforms natural multiround on hard cases. (Additional exchange
surfaces real signal when cases have genuine complexity.)

---

## Pre-Registered Stratum Analysis (Phase 8)

`fc_lift` will be reported separately for two strata: **critique** and **defense_wins**.

(ARCH-1 note: benchmark has 0 mixed cases — no mixed stratum exists.)

**Expected directional patterns:**
- Defense_wins stratum: primary driver of DRQ/FVC lift — isolated debate Defender prevents
  false condemnation
- Critique stratum: primary driver of IDR/IDP lift — debate surfaces missed issues and reduces
  false positives

**Global `fc_lift` (H1 primary criterion) remains the hypothesis test.** Stratum breakdown is the
interpretive structure for understanding mechanism, pre-registered to prevent post-hoc selection
of a favorable stratum framing.

---

## Known Confound

**multiround vs isolated_debate comparison (v4 DEBATE Issue 1, unresolved):**
multiround's Defender sees the Critic output; isolated_debate's Defender does not. Any advantage
in multiround could be from (a) additional exchange rounds or (b) information access alone.
These two mechanisms are not separable from this design. Results are reported descriptively;
causal attribution is not supported.

---

## Convergence Metric (v5 Replacement)

**Point resolution rate** = (points resolved by concession or empirical agreement) /
(total contested points in DEBATE.md)

Extraction: count DEBATE.md entries with status `"Resolved: critic wins"`,
`"Resolved: defender wins"`, or `"Resolved: empirical_test_agreed"` vs total contested points.

Note: `"empirical_test_agreed"` here is an orchestrator-assigned debate resolution status
(a valid agent output), not a ground-truth case type. ARCH-1 has no ground-truth cases with
`ideal_debate_resolution.type == empirical_test_agreed`, but the orchestrator may still reach
this verdict during live debate rounds.

**Diagnostic only — not used in pass/fail determination.**
