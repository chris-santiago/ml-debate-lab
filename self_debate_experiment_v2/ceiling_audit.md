# Rubric Ceiling Effect — Audit (Issue 11)

**Date:** 2026-04-04
**Addresses:** Issue 11 from `tasks/open_issues.md`

---

## Findings

### Corrected ceiling count

The report stated 14/20 cases hit 1.000. Actual count from `self_debate_results.json`: **16/20**.

| Group | Ceiling | Non-ceiling |
|-------|---------|-------------|
| Critique cases (n=15) | **13/15** | 2/15 |
| Defense_wins cases (n=5) | **3/5** | 2/5 |
| **Total** | **16/20** | **4/20** |

### Non-ceiling cases — all are known failure modes

| Case | Mean | Non-1.0 dim | Cause |
|------|------|-------------|-------|
| real_world_framing_001 | 0.833 | DC=0.0 | Reasoning/label disconnect (fixed by two-pass Defender) |
| scope_intent_003 | 0.900 | DC=0.5 | Partial verdict calibration |
| defense_wins_003 | 0.833 | DC=0.5 | Defender overconceded |
| defense_wins_005 | 0.833 | DC=0.5 | Defender overconceded |

**Key observation:** Every non-ceiling case is a DC failure. IDR, IDP, DRQ, FVC, and ETD are 1.0 on every correctly-working case.

### Dimension-level ceiling analysis (13 ceiling critique cases)

| Dimension | All 1.0? | N (applicable) |
|-----------|----------|----------------|
| IDR | Yes | 13 |
| IDP | Yes | 13 |
| DC | Yes | 13 |
| DRQ | Yes | 13 |
| ETD | Yes | 12 (1 N/A) |
| FVC | Yes | 13 |

The rubric has **zero discriminative power** at the treatment level on correctly-working critique cases.

---

## Root Cause: Benchmark Difficulty, Not Scoring Leniency

Two candidate explanations:
1. **Scoring too lenient** — rubric awards 1.0 even for partial work
2. **Benchmark too easy** — all cases are discoverable enough that the protocol never partially detects them

The data rules out (1): IDR=1.0 means all must_find issues were found, not that partial findings were rewarded. The rubric assigns IDR=0.5 for partial detection — but no case ever triggered this.

**Root cause is (2): benchmark difficulty.** All 15 non-defense_wins cases have 1–2 must_find issues stated implicitly but plainly in the scenario text. The debate protocol finds all of them every time.

### Contributing factors

- **Small must_find sets:** 12 of 15 critique cases have exactly 2 must_find items. With only 2 required issues, the protocol either finds both (IDR=1.0) or one (IDR=0.5). No case triggered IDR=0.5.
- **Discoverable flaws:** Even "hard" cases (hidden_confounding_002, hidden_confounding_004, broken_baseline_003) contain flaws that are identifiable from ML intuition alone. None require deep domain expertise.
- **No red herrings:** The benchmark contains no valid-but-suspicious cases that might elicit false critiques. IDP=1.000 across all 15 cases confirms the Critic never raised spurious issues on any of them.

---

## Proposed Fixes

### Fix A — Fractional IDR (immediate, no new cases needed)

Change IDR from {0.0, 0.5, 1.0} to a continuous fraction: `issues_found / total_must_find`.

Effect on existing results: no change (all cases found all issues → still 1.0).
Effect on future harder cases: a 3-must_find case where 2/3 are found scores IDR=0.667 instead of IDR=0.5.

**Recommendation:** Implement fractional IDR for all future scoring runs.

### Fix B — Harder benchmark cases (Issue 7 + Issue 12)

Add cases that stress the protocol below ceiling:
- Cases with 3–4 must_find items (harder to find all)
- Cases where flaws require domain knowledge beyond standard ML methodology
- Cases with red herrings that might elicit spurious critiques (tests IDP, Issue 12)

`new_benchmark_cases.json` (10 cases, including 3 hard) partially addresses this. Run results needed to confirm whether any hard case breaks ceiling.

### Fix C — Document the ceiling as a benchmark scope limitation

Add to §7 Limitations in REPORT.md: the rubric's discriminative power for the treatment condition is limited to DC failures. IDR, IDP, DRQ, FVC, ETD carry no variance across correctly-working cases. The benchmark's "difficulty" labels predict baseline score variation, not debate protocol score variation.

---

## Status

- Root cause diagnosed: ✅ benchmark difficulty (not scoring leniency)
- Ceiling count corrected: 16/20 (was reported as 14/20)
- Fix A (fractional IDR): documented, implement in future scoring
- Fix B (harder cases): `new_benchmark_cases.json` running now (Issue 7)
- Fix C (limitations note): see REPORT.md §7 update below
