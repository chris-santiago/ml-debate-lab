# DEBATE.md — v5 Protocol Self-Review

**Phase 4 — Contested points from CRITIQUE.md vs DEFENSE.md**

Rounds: up to 4. Unresolved points after Round 4 are force-resolved as `empirical_test_required`.

---

## Contested Points

### Point 1 — Issue 1 Component A: Is proxy_mean-based filtering circularity or standard design?

**Critic position:** Selecting cases where Sonnet fails, then measuring whether Sonnet does better under role structure, confounds role structure benefit with "second chance" regression-to-mean effects. The isolated_debate condition gives Sonnet a structured retry, not an independent evaluation.

**Defender position:** Filtering for hard cases is standard benchmark design. isolated_debate gives each agent only `task_prompt` — structurally identical information access to baseline. The adversarial roles produce distinct reasoning pathways, not a retry.

**Status:** Resolved — defender wins. Condition: PRE-3 (H1 × H2 outcome matrix) must be confirmed pre-registered in EXECUTION_PLAN.md before Phase 5. PRE-8 accepted as supplementary early-warning.

---

### Point 2 — Issue 2: H2 secondary vs co-primary for mechanism validation

**Critic position:** H1 cannot validate the mechanism claim ("adversarial role separation forces engagement"). If H1 passes and H2 fails, the mechanism is undemonstrated but the pre-registration structure invites misreading "H1 passed" as protocol validation. H2 should be co-primary or the mechanism claim should be dropped from H1's framing.

**Defender position:** H1 as necessary condition + H2 as mechanism test is correct two-tier experimental logic. The fix is a pre-committed outcome matrix, not restructuring the hypothesis hierarchy. H1 passing + H2 failing is a meaningful result ("compute helps; structure doesn't add beyond that"), not an ambiguous one — if the matrix is written down.

**Status:** Open

---

### Point 3 — Issue 4: Is per-dimension lift computation required as a primary sensitivity output?

**Critic position:** The aggregate fc_lift mixes 4-dimension per-case means (critique) with 2-dimension per-case means (defense_wins). H1 is judged on this aggregate. A condition that fails IDR/IDP but passes DRQ/FVC could produce fc_lift >= 0.10 via the defense_wins stratum, and this would not be flagged by the current pass criterion.

**Defender position:** The stratum breakdown (pre-registered, mandatory in Phase 8) will surface this composition effect if it occurs. The per-dimension lift computation is achievable at low implementation cost and should be added to sensitivity_analysis.py — but the H1 criterion itself does not need to change.

**Status:** Open

---

### Point 4 — Issue 5: Should a variance gate precede the full Phase 6 run?

**Critic position:** +0.10 threshold was set before within-case variance was known. If the CI on fc_lift is wider than 0.10 at N=110 with 3 runs, the test cannot distinguish lift = 0.10 from lift = 0.00. The Phase 5.5 pilot should be extended to 3 runs per case and a pre-execution variance gate added.

**Defender position:** The +0.10 threshold is a policy choice (minimum practically meaningful effect), not a power-derived value. The concern is about *detectability*, not threshold validity. The fix is extending Phase 5.5 to 3 runs to generate a pre-execution variance estimate — a gate on n_runs_per_case if variance is high — without changing the threshold.

**Status:** Open

---

## Resolved Points

**Point 2 — Issue 2 (H2 secondary vs. co-primary):** Resolved Round 1 — Defender concedes. PRE-9 added: revise HYPOTHESIS.md H1 "Mechanism" field to "Motivation" with explicit note that mechanism claim is H2's conclusion; cross-reference to H1 × H2 outcome matrix.

**Points 3 and 4 — Issues 4 and 5 (per-dimension lift / variance gate):** Resolved Round 1 — Defender wins, conditional on PRE-5 (per-dimension lift in sensitivity_analysis.py) and PRE-6 (Phase 5.5 extended to 3 runs, variance gate).

**Point 1 — Issue 1 Component A (proxy_mean filtering):** Resolved Round 2 — Defender wins. Structural protection is PRE-3 (H1 × H2 outcome matrix); PRE-8 (pilot ensemble lift flag) accepted as supplementary. Condition: PRE-3 confirmed pre-registered in EXECUTION_PLAN.md before Phase 5.

---

## Round Log

### Critic — Round 2

**Point 1 only. Gate-to-flag conversion.**

**Position: Concede, with a specific structural caveat that must be on record.**

The defender's PRE-8 flag is acceptable. Here is why I concede, and here is the caveat.

**Why I concede the gate requirement:**

A gate that blocks Phase 6 execution conditional on pilot-scale ensemble lift estimates has the same noise problem as the flag — worse, actually, because a gate forces a hard binary on an estimate computed from 10-15 pilot cases with unknown within-case variance. PRE-6 is still characterizing that variance at the time the gate would fire. A Phase 6 execution blocker armed from a noisy 10-case estimate is not more rigorous than a flag — it is more brittle. The gate does not solve the structural concern; it just moves the noisy decision to before Phase 6 rather than after.

**Why the flag is adequate:**

The structural protection for Point 1's core concern is not PRE-8. It is PRE-3: the pre-committed H1 × H2 outcome matrix. The concern was that selection-driven lift (cases filtered to where Sonnet fails create headroom for any second-call condition) would be misattributed to adversarial role structure. PRE-3 directly addresses this: the H1 pass + H2 fail cell explicitly maps to "compute benefit confirmed; adversarial structure not demonstrated beyond compute volume." H2 is a full-run comparison of debate vs. ensemble, executed under the same N=110 cases and the same variance conditions as H1. That is the right test for distinguishing protocol benefit from compute benefit — not a pilot-scale estimate.

PRE-8 adds modest early-warning value. If the pilot ensemble lift is clearly high (>= 0.05), flagging the Phase 9 interpretation directive is sensible discipline. I accept it.

**The caveat I require on record:**

PRE-8's trigger is estimated at pilot scale (10-15 cases, 3-run basis per PRE-6). A pilot-scale ensemble lift just below the 0.05 trigger (e.g., 0.04) could represent a full-run lift of 0.08–0.12 given pilot variance. If the flag does not arm at the pilot stage but ensemble lift is materially high on the full run, no pre-committed qualification obligation exists for Phase 8 or Phase 9 unless PRE-3's H1 × H2 matrix covers it.

This caveat is already covered by PRE-3 if PRE-3 is written correctly. The one-sentence confirmation I need is this: **PRE-3's H1 × H2 outcome matrix is the primary structural protection for the selection-advantage concern, not PRE-8.** PRE-8 is supplementary. If PRE-3 is confirmed as pre-registered before Phase 5, the flag-vs-gate question is resolved.

**Verdict: Defense wins, conditional on PRE-3 being confirmed pre-registered before execution.**

Point 1 status: Resolved — defender wins. Condition: PRE-3 (H1 × H2 outcome matrix) must appear in EXECUTION_PLAN.md before Phase 5. PRE-8 is accepted as supplementary early-warning; it does not replace PRE-3 as the primary protection.
