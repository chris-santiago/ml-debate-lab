# Agents

All agents are subagents dispatched via the Agent tool from the main session. They run with isolated context — each agent sees only the artifacts passed to it.

## ml-critic

**Role:** Adversarial critic — finds flaws the PoC hasn't tested.

**Dispatched by:** `/ml-lab` skill at Step 3.

- **Debate mode:** dispatched once (Stage A.1)
- **Ensemble mode:** dispatched 3 times independently with no cross-visibility

**Persona:** Skeptical ML engineer with an applied mathematics background. Looks for fundamental flaws in the proof-of-concept.

**Modes:**

| Mode | When | Input |
|------|------|-------|
| Initial critique (Step 3) | First review cycle | PoC code + hypothesis |
| Debate rounds (Step 5) | Open-ended debate | Prior exchange history |
| Evidence-informed re-critique | Macro-iteration cycles 2+ | Prior critique + experimental results |

**Output:** `CRITIQUE.md` (debate) or `CRITIQUE_{1,2,3}.md` (ensemble) with severity-tagged findings (FATAL, MATERIAL, MINOR).

---

## ml-critic-r2

**Role:** R2 challenger — issues ACCEPT/CHALLENGE/PARTIAL verdicts on defender rebuttals.

**Dispatched by:** `/ml-lab` skill at Step 3, Stage B only (debate mode).

**Not used in ensemble mode.**

**Input:** Defender's rebuttal for a specific finding.

**Output:** Per-finding verdict with justification. Fed into `derive_verdict()` for deterministic case-level verdict computation.

---

## ml-defender

**Role:** Design defender — argues for the implementation against adversarial critique.

**Dispatched by:** `/ml-lab` skill at Step 3 (debate mode only).

**Not used in ensemble mode.**

**Persona:** The original designer who understands the intent behind every choice.

**Rebuttal taxonomy (7 types):**

| Type | Meaning |
|------|---------|
| CONCEDE | Finding is valid; will fix |
| REBUT-DESIGN | Design choice was intentional and correct |
| REBUT-SCOPE | Finding is out of scope for this investigation |
| REBUT-EVIDENCE | Evidence doesn't support the claimed severity |
| REBUT-IMMATERIAL | Finding is real but doesn't affect conclusions |
| DEFER | Will address as pre-flight item before main run |
| EXONERATE | Finding is based on a misunderstanding |

**Modes:**

| Mode | When | Input |
|------|------|-------|
| Initial defense (Stage A.2) | After critic R1 | Critic findings + PoC |
| Structured R2 response (Stage B.2) | After critic-r2 challenge | R2 verdict + prior exchange |
| Evidence-informed re-defense | Macro-iteration cycles 2+ | Prior defense + experimental results |

**Output:** `DEFENSE.md` with per-finding structured rebuttals.

---

## research-reviewer

**Role:** Deep peer reviewer — Opus-class structured review of `REPORT.md`.

**Dispatched by:** `/ml-lab` skill at Step 10, Round 1.

**Output:** `PEER_REVIEW_R1.md` with severity-tagged findings.

---

## research-reviewer-lite

**Role:** Verification reviewer — Haiku-class follow-up review.

**Dispatched by:** `/ml-lab` skill at Step 10, Rounds 2–3.

**Purpose:** Verify that remediation addressed the Round 1 findings without introducing new issues. Lighter weight than the full reviewer.

---

## report-writer

**Role:** Produces technical reports from investigation artifacts.

**Dispatched by:** `/ml-lab` skill at Steps 8 and 11.

**Modes:**

| Mode | Output | Input |
|------|--------|-------|
| Mode 1 (Step 8) | `REPORT.md` | Analytical artifacts + quantitative results |
| Mode 2 (Step 11) | `TECHNICAL_REPORT.md` | All available artifacts (results-mode synthesis) |

---

## readme-rewriter

**Role:** Outside-reader README rewriter.

**Dispatched by:** `/ml-lab` skill at Step 13 (user-confirmed).

**Process:** diagnose (as first-time reader) → outline (proposed structure) → rewrite (complete README optimized for external audiences).

---

## intent-monitor

**Role:** Pre-registration drift monitor.

**Dispatched by:** `/intent-watch` skill.

**Process:** Indexes binding constraints from a source-of-truth document, detects recent git changes, evaluates diffs for conflicts. Emits a clean-pass line or structured conflict report.
