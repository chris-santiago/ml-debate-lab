# Mixed Case Generation — ETD Testing Plan

**Context:** This document records the plan for generating `mixed`-position benchmark cases
to enable ETD (Empirical Test Design) scoring. It is written against the v5 synthetic
pipeline architecture. See `DATA_ACQUISITION.md` for the broader v6 direction (RC reports).

---

## Problem Statement

ETD is a primary scoring dimension in `self_debate_poc.py` but produced zero signal in v5.
Root cause: `compute_etd` returns `None` whenever `ideal_resolution` is `critique_wins` or
`defense_wins` — and the v5 benchmark contained 110 cases, all of type `critique_wins` (80)
or `defense_wins` (30). Zero mixed cases → ETD always N/A → no ETD signal of any kind.

ETD also returns `None` for ensemble and baseline conditions by design (no adversarial
exchange). So ETD is only observable on:

```
debate conditions (isolated, multiround, forced_multiround) × mixed cases
```

---

## What a Mixed Case Is

A `mixed` case is **not** a corrupted design. It is a design with an empirically contingent
choice — a decision that is:

- **Defensible:** there is a legitimate reason the designer made this choice
- **Challengeable:** a careful critic can raise a valid concern
- **Unresolvable from the document alone:** the correct answer depends on data properties
  that must be measured, not inferred from the design narrative

The correct debate outcome is not a verdict but an empirical test specification: "here is
what you would need to measure to determine whether this choice is valid."

---

## Pipeline Changes Required

The v5 pipeline generates cases via a 5-stage flow:

```
Stage 1 (hypothesis) → Stage 2 (sound design) → Stage 3 (corrupt N flaws)
  → Stage 4 (ground truth assembler) → Stage 5 (smoke test)
```

Mixed cases require a parallel 3-stage path that replaces Stages 2–5:

```
Stage 1 (hypothesis) → Stage 2-mixed (ambiguous design) → Stage 3-mixed (ground truth)
  → [no smoke test]
```

### Files to Create

**`pipeline/prompts/stage2_mixed_writer.md`**

Role: write a sound design with a built-in empirically contingent choice. The ambiguous
decision must:
- Sound like a deliberate engineering choice (not an oversight)
- Have a defensible domain-specific justification
- Have a legitimate counter-argument a critic could raise
- Be resolvable only by measuring something in the actual data or model output

Good ambiguous choice types:
- Split strategy on data with unknown or mild temporal structure
- Evaluation metric that is appropriate for the stated goal but may obscure tail behavior
- Model capacity choice where the optimal level depends on actual feature correlation
- Regularization strength where the correct level depends on actual overfitting behavior
- Threshold for a classification decision where the operational cost ratio is approximate

The output schema is identical to Stage 2 — a `design_narrative` — plus an
`ambiguous_choice` block identifying which decision is deliberately contestable and why.

**`pipeline/prompts/stage3_mixed_assembler.md`**

Role: assemble the ground truth for a mixed case. Input is the Stage 2-mixed output only
(no corruption report). Output schema:

```json
{
  "case_id": "...",
  "correct_verdict": "mixed",
  "ideal_debate_resolution": {
    "type": "mixed",
    "condition": "The specific empirical test that could resolve the dispute",
    "supports_critique_if": "What result confirms the critic's concern",
    "supports_defense_if": "What result vindicates the design choice",
    "ambiguous_if": "Edge condition where neither position is clearly right"
  },
  "planted_issues": [],
  "must_find_issue_ids": [],
  "must_not_claim": [],
  "acceptable_resolutions": [
    "empirical_test_agreed"
  ]
}
```

Key constraint: `condition` must be concrete and measurable — a specific metric, test, or
observable. Not "it depends on the data." Example: "Compute autocorrelation of the target
variable at lag 1 week; if > 0.4, temporal split is required."

### Files to Modify

| File | Change |
|---|---|
| `pipeline/orchestrator.py` | Add `--mixed N` flag. For N mixed cases per batch, route through `stage2_mixed_writer.md` → `stage3_mixed_assembler.md`. Skip Stage 5 (smoke test binary approve/critique does not apply to mixed cases). |
| `pipeline/select_cases.py` | Add fifth stratum: `mixed / 0 flaws`. Defaults to `--tier-mixed 15`. Mixed cases are not proxy-filtered (no smoke score). |
| `self_debate_poc.py:score_run` | Add `elif correct_position == 'mixed':` branch at line 172. IDR, IDP, DC all `None`. DRQ and FVC accept both critique and defense stances as valid if paired with an empirical test (`acceptable_resolutions = ['empirical_test_agreed']`). ETD is the primary signal. |

---

## Scoring Logic for Mixed Cases

When `correct_position == 'mixed'`:

| Dimension | Value | Rationale |
|---|---|---|
| IDR | N/A | No must-find issues — design is not definitively wrong |
| IDP | N/A | No must-not-claim violations predetermined |
| DC | N/A | No definitive verdict for Defender to reach |
| DRQ | Scored against `empirical_test_agreed` | Correct outcome is producing an empirical test, not a verdict |
| FVC | N/A or flexible | Both critique/defense stances acceptable if test is produced |
| ETD | **Primary signal** | Full credit (1.0) for all three fields; partial (0.5); zero (0.0) |

The per-case pass criterion for mixed cases reduces to: `ETD >= 0.5`.

---

## Target N and Effective Sample Size

ETD is N/A for ensemble and baseline. Mixed cases only contribute ETD observations in
the three debate conditions:

| Mixed cases | × conditions | × runs | = ETD observations |
|---|---|---|---|
| 15 | 3 | 3 | 135 |
| 20 | 3 | 3 | 180 |
| 25 | 3 | 3 | 225 |

**Recommendation:** 20 mixed cases. Sufficient for per-condition ETD comparison
(isolated vs. multiround vs. forced_multiround) with 60 observations per condition.

---

## Relationship to v6 RC Approach

`DATA_ACQUISITION.md` describes a different path to mixed cases: RC reports that document
"paper is mostly sound but X is overstated." These are naturally occurring mixed cases
where the reproducer raised a concern but neither confirmed nor denied the design choice.

The synthetic pipeline above is an alternative when RC-sourced mixed cases are:
- Too few (RC reports skew toward definitive flaws)
- Insufficiently diverse in domain/task type
- Unavailable in the target difficulty range

If RC acquisition proceeds, the mixed case extraction step in that pipeline should produce
the same `ideal_debate_resolution` schema defined here, enabling unified scoring.

---

## Implementation Order

1. Write `stage2_mixed_writer.md` — highest-stakes prompt; quality of the ambiguous choice
   definition determines whether mixed cases test real ETD vs. trivial ambiguity
2. Write `stage3_mixed_assembler.md` — must enforce concreteness of `condition` field
3. Dry-run 5 mixed cases through the new path; inspect `ideal_debate_resolution` outputs
4. Modify `score_run` to handle `correct_position == 'mixed'`
5. Add `--mixed N` to orchestrator and fifth stratum to `select_cases.py`
6. Generate 20 mixed cases; add to benchmark alongside existing 110
