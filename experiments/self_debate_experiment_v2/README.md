# Self-Debate Protocol v2 — PoC Design Document

## What this PoC tests

The isolated two-instance self-debate protocol: a language model plays explicit Critique,
Defense, and Judge roles in structured sequential prompts, with Critique and Defense each
receiving only the task_prompt (no shared context). The protocol is evaluated against a
trivial single-pass baseline (no debate loop, no revision) on a 20-case benchmark of
synthetic ML reasoning tasks.

This is a subagent-dispatch implementation. Every case runs isolated subagent invocations
for Critique, Defense, Judge, Scorer, and Baseline roles. Critique and Defense subagents
receive only the task_prompt — they are dispatched in separate context windows with no
shared state. This prevents the single-context contamination where one agent playing all
roles trivially produces perfect agreement.

---

## Architecture

### Isolated Two-Instance Protocol (Debate)

```
task_prompt
    |
    +---> [CRITIQUE AGENT] ---> critique_output
    |                                |
    +---> [DEFENSE AGENT] ---> defense_output
                                     |
    task_prompt + critique_output + defense_output
                                     |
                              [JUDGE AGENT]
                                     |
                              final verdict
```

Key constraint: Defense receives **only** the task_prompt. It never sees the Critique's
output. This prevents contamination of the Defense's independent reasoning and enables
genuine `defense_wins` verdicts on cases where the Critique's premise is false.

### Trivial Baseline

Single API call: task_prompt → answer + self-critique. No debate loop. No revision step.
Scored on the same 6-dimension rubric with structural adaptations.

---

## Benchmark Cases (20 total)

| Category | Cases | IDs |
|----------|-------|-----|
| broken_baseline | 4 | 001-003 (original) + 004 (new hard) |
| metric_mismatch | 3 | 001-003 (original) |
| hidden_confounding | 4 | 001-003 (original) + 004 (new hard) |
| scope_intent_misunderstanding | 2 | 002-003 (original) |
| defense_wins | 5 | 001-004 (original) + 005 (new medium) |
| real_world_framing | 2 | 001 (medium) + 002 (hard) |

**New cases in v2:**
- `broken_baseline_004` (hard): Fine-tuned model vs. zero-shot YOLO-v5 — training regime
  confound, not architectural superiority
- `hidden_confounding_004` (hard): Credit scoring model drift attributed to "economic
  uncertainty" — population shift and feature drift undiagnosed
- `defense_wins_005` (medium): In-domain NER evaluation for deployment-scoped system —
  reviewer applies wrong evaluation standard
- `real_world_framing_001` (medium): LLM symptom triage system — retrospective 87%
  agreement ≠ clinical readiness
- `real_world_framing_002` (hard): Dynamic pricing revenue lift — SKU mix confound and
  year-over-year comparison with catalog change

---

## Evaluation Rubric

All 6 dimensions are scored 0.0–1.0. N/A means inapplicable for that case.

### 1. issue_discovery_recall (IDR)
Fraction of must-find planted issues surfaced by the Critique agent.
- 1.0: all must-find issues identified with correct location and characterization
- 0.5: partial (location correct but characterization wrong, or vice versa)
- 0.0: issue not found
- **N/A**: for `defense_wins` cases (correct_position = "defense"); no genuine issues exist

### 2. issue_discovery_precision (IDP)
**Standard cases (correct_position != "defense"):**
Fraction of Critique's claims that are valid (planted or demonstrably real). Penalized for
forbidden claims from `must_not_claim`.
- 1.0: no forbidden claims made
- 0.5: at least one forbidden claim made (precision degraded)

**Defense_wins cases (IDP REDEFINITION):**
For cases where `correct_position = "defense"`, the Critique is expected to raise INVALID
concerns (because the defense wins). IDP is re-defined as **false-premise precision**:
- 1.0: Critique correctly identifies NO real issues (raises no claims) — rare
- 0.0: Critique raises any claims (all are false positives for a defense_wins case)

Rationale: The standard IDP question is "what fraction of the Critique's claims are valid?"
For defense_wins cases, the correct answer is 0/N claims are valid. Scoring 0.0 is the
correct punishment: the Critique over-claimed and penalized a valid piece of work.

### 3. defense_calibration (DC)
**Standard cases:** Does the Defense concede real planted issues?
- 1.0: Defense acknowledges all must-find issues as real
- 0.5: partial acknowledgment
- 0.0: denies valid issues

**Defense_wins cases:** Does the Defense independently identify the claim as valid?
- 1.0: Defense maintains claim is valid with supporting reasoning
- 0.5: Defense is equivocal
- 0.0: Defense incorrectly concedes the false critique

**Baseline DC:** Always 0.0 (structural: no revision step; position_update = 0.0).

### 4. debate_resolution_quality (DRQ)
Does the actual verdict match the ideal resolution type?
- 1.0: exact match
- 0.5: in acceptable_resolutions but not ideal type
- 0.0: wrong type

**Baseline DRQ:** Capped at 0.5 (no actual debate performed).

### 5. empirical_test_diagnosticity (ETD)
Does the proposed empirical test actually distinguish critique-wins from defense-wins?
- 1.0: test has clear procedure, measurable outcome, maps to two verdict types
- 0.5: test is relevant but underspecified
- **N/A**: for cases with ideal resolution `critique_wins` or `defense_wins`

### 6. final_verdict_correctness (FVC)
Does the system's final stated verdict align directionally with the ground truth?
- 1.0: correct direction
- 0.0: wrong direction or no verdict emitted

---

## Pass/Fail Thresholds

| Level | Threshold |
|-------|-----------|
| Per-dimension | >= 0.5 (no applicable dimension may be below 0.5) |
| Per-case | mean >= 0.65 AND all applicable dimensions >= 0.5 |
| Benchmark | mean >= 0.65 AND case-pass fraction >= 75% AND lift >= +0.10 |

---

## agent_convergence_rate

Computed per case; measures whether Critique and Defense independently identified the
same primary issues.

**For critique-wins/mixed cases:**
- 1.0: all must-find issues appear in both outputs independently
- 0.5: partial overlap
- 0.0: no overlap

**For defense_wins cases:**
- 1.0: Critique raises no issues (or minimal) AND Defense correctly asserts claim is valid
- 0.5: Defense correctly asserts validity but Critique raised false concerns
- 0.0: Both agents fall for the false framing

Expected pattern: easy cases > hard cases in convergence rate (prior run showed 0.727
overall; hard cases had lower convergence).

---

## API call budget

6 calls per case × 20 cases = **120 total API calls**.

| Call | Role | Receives |
|------|------|----------|
| 1 | Critique | task_prompt only |
| 2 | Defense | task_prompt only (no Critique output) |
| 3 | Judge | task_prompt + Critique output + Defense output |
| 4 | Scorer (debate) | ground truth + all three agent outputs → JSON scores |
| 5 | Baseline | task_prompt only (single-pass + self-critique) |
| 6 | Scorer (baseline) | ground truth + baseline output → JSON scores |

The Scorer produces a JSON object with scores (1.0 / 0.5 / 0.0 / null) and
one-sentence justifications for each of the 6 rubric dimensions. This replaces
heuristic keyword matching from the prior run — scoring quality is now on par
with debate quality.

---

## Running the experiment

The orchestrator dispatches isolated subagents for each role per case. Subagents are
invoked sequentially within each case (Critique and Defense first — independently — then
Judge, then Scorer, then Baseline, then Scorer for baseline). Critique and Defense are
in separate context windows and never see each other's output before generating their
own assessment.

Once all transcripts are collected, `python self_debate_poc.py` reads `self_debate_transcripts.py`
and writes `self_debate_results.json`.

Output: `self_debate_results.json` (raw scores + transcripts + scorer outputs), stdout summary table.

---

## Differences from prior experiments

| Dimension | Prior (E1 / E2) | This (v2) |
|-----------|-----------------|-----------|
| API calls | Simulated transcripts | Live Anthropic API |
| Scoring method | Heuristic keyword matching | 4th LLM scorer call per case |
| Case count | 11 (E1) / 15 (E2) | 20 |
| New categories | None | real_world_framing |
| IDP for defense_wins | Undefined/excluded | Redefined as false-premise precision |
| DC for contaminated defense | Partial-contestation penalty | N/A (isolated protocol) |

---

## Files produced

| File | Contents |
|------|----------|
| `self_debate_poc.py` | This script (self-contained, all 20 cases embedded) |
| `README.md` | This design document |
| `self_debate_results.json` | Raw scores, transcripts, aggregate metrics (written by script) |
