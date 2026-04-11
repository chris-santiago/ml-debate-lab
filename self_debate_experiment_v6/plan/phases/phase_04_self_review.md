# Phase 4 — Pre-Experiment Self-Review

> **Reminders (cross-cutting rules)**
> - All script invocations use `uv run`. Never `python` or `python3` directly.
> - Agents dispatched by name only. Do not read any file from `agents/`.
> - CWD: Bash tool CWD is always repo root (`ml-debate-lab/`). Prefix all bash commands with `cd self_debate_experiment_v6 &&`.
> - Subagent context: authenticated Claude Code session. No direct API calls.

## Required Reading
- [hypotheses.md](../references/hypotheses.md) — full hypothesis definitions; `ml-critic` reviews these
- [design_decisions.md](../references/design_decisions.md) — full design context for the critic/defender exchange

## Key Constraints
- **`HYPOTHESIS.md` must be committed to git before Phase 5 begins.** This is the pre-registration lock.
- RC scoring scope (`idr_documented` + `idr_novel`) must be committed to `HYPOTHESIS.md` in this phase.
- The orchestrator prompt audit (started in Phase 0) is reviewed again here with the critic looking for answer-key leakage vectors in the batch agent context window composition.

---

## Steps

### 4.1 Finalize and commit `HYPOTHESIS.md`
Ensure `HYPOTHESIS.md` contains:
- All 6 hypotheses (H1a, H1b, H2, H3, H4, H5, H6) with formulas and test specifications
- H1a threshold value (set in Phase 3)
- RC scoring scope: bidirectional IDR (`idr_documented` primary, `idr_novel` secondary)
- Statistical test specifications (bootstrap 95% CI, one-sided for H1a/H1b, two-sided for H2/H6)

Commit before dispatching review agents.

### 4.2 Dispatch `ml-critic`
Agent prompt:
```
Review HYPOTHESIS.md and the evaluation rubric for the v6 benchmark experiment.

Context: This is a pre-registered benchmark experiment testing whether the ml-lab adversarial
debate protocol (critic + defender) outperforms single-pass baseline on 120 ML methodology
review cases (60 regular, 20 defense, 40 mixed).

Your tasks:
1. Evaluate whether each hypothesis (H1a-H6) is falsifiable and the test specifications are
   correct (formulas, CIs, test types, threshold).
2. Identify any confounds, power issues, or design gaps not addressed by the mitigations in
   v5_mitigations.md.
3. Audit the batch agent context window composition for answer-key leakage vectors — specifically,
   check whether any information in the agent's context window could allow it to infer the
   correct verdict before completing its analysis.
4. Generate PRE-1 through PRE-N pre-execution requirements that must be addressed before Phase 5.

Read: self_debate_experiment_v6/HYPOTHESIS.md
Reference: self_debate_experiment_v6/plan/references/hypotheses.md
Reference: self_debate_experiment_v6/plan/references/v5_mitigations.md
```

### 4.3 Dispatch `ml-defender`
After receiving critic output, dispatch `ml-defender` with:
- Critic output from 4.2
- `HYPOTHESIS.md`
- Instruction to defend the design choices and respond to each PRE-N requirement

### 4.4 Up to 2 debate rounds
Run 1-2 rounds of critic/defender exchange. Stop when requirements are stable.

### 4.5 Resolve PRE-N requirements
Address each pre-execution requirement identified by the critic. Document resolutions.

### 4.6 Final commit
Commit the resolved `HYPOTHESIS.md` + any scoring engine changes required by PRE-N resolutions.

---

## Verification
- [ ] Scoring isolation: GPT-4o scorer has no access to ground truth (answer keys not in scorer context)
- [ ] RC scoring scope committed to `HYPOTHESIS.md`: bidirectional (recall + novel concerns, both saved)
- [ ] `HYPOTHESIS.md` committed to git before Phase 5
- [ ] `CRITIQUE.md`, `DEFENSE.md`, and `DEBATE.md` written before Phase 5

## Outputs
- Committed `HYPOTHESIS.md` with all 6 hypotheses, H1a threshold, and RC scoring scope
- PRE-N pre-execution requirements documented and resolved
- `CRITIQUE.md` — raw ml-critic output reviewing the experiment design
- `DEFENSE.md` — raw ml-defender response to the critique
- `DEBATE.md` — full critic/defender exchange transcript with per-point resolution status

## Gate
`HYPOTHESIS.md` committed to git. All PRE-N requirements addressed. No open answer-key leakage vectors. `CRITIQUE.md`, `DEFENSE.md`, and `DEBATE.md` written.
