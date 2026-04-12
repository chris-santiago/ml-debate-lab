# DEBATE.md — v4 Protocol Self-Review

**Purpose:** Track contested points between ml-critic and ml-defender on the v4 experimental design.

---

## Contested Points

| # | Issue | Critic Position | Defender Position | Status |
|---|-------|----------------|-------------------|--------|
| 1 | isolated_debate mechanism | Primary condition tests role-framing only; mechanism text implies adversarial exchange which only multiround has | Role separation (not exchange) is the operative mechanism; elaboration language slightly overreaches but condition is transparently defined; multiround vs isolated_debate comparison isolates exchange effect | Open |
| 2 | isolated_debate vs ensemble structural similarity | Both are parallel-independent-assessment-then-synthesis; "compute-matched" claim is false (3 vs 4 calls); assessor-count confound unacknowledged | Adjudication vs aggregation is a meaningful structural difference; "compute-matched" label should be dropped; confound acknowledged but practical question still answerable | Resolved: defender wins (partial) — Defender concedes "compute-matched" label and acknowledges assessor-count confound; design defensible with honest labeling |
| 3 | fc_lift pools dimension-instances | Pools all non-null dimension values across cases, weighting critique cases 2x defense cases | Critic misread implementation: fc_lift averages per-case fair_comparison_mean floats (one float per case, weight 1/53 regardless of case type) | Resolved: defender wins — Critic's description of implementation factually incorrect; fc_lift is case-balanced by construction |
| 4 | +0.10 threshold calibration | Stated without reference to pilot data or prior measurement; arbitrary relative to ceiling/floor effects | Prior v3 data places baseline in 0.50-0.70 range; +0.10 requires ~one additional half-credit per case on average; calibration reasoning not formally preregistered | Resolved: defender wins (partial) — Defender acknowledges calibration undocumented; threshold not arbitrary given v3 priors; difficulty-stratified lift reporting committed |
| 5 | Asymmetric pass threshold by case type | 0.65 mean threshold harder for empirical_test_agreed (5 dims) vs defense_wins (2 dims); aggregate 75% rate conceals variation | Asymmetry reflects task complexity, not measurement artifact; aggregate rate insufficient — per-case-type reporting committed as required output | Resolved: defender wins (partial) — per-case-type pass rates preregistered as required reporting |
| 6 | IDP awards 1.0 for neutral fabrications | Agent raising only neutral issues scores IDP=1.0 same as agent raising none; metric measures trap-avoidance not general precision | Design intent is trap-avoidance on must_not_claim items; metric name misleading but behavior deliberate; post-execution neutrals audit committed | Resolved: defender wins (partial) — Defender concedes metric name is misleading; audit committed |
| 7 | Secondary H2 unverifiable | score_run() unconditionally sets DC=None for all defense cases; zero computable values; hypothesis produces no data | Full concession — DC=None confirmed; H2 reframed to FVC >= 0.5 on defense_wins cases; correction committed before execution | Resolved: critic wins — Blocker resolved; H2 reframed in PREREGISTRATION.json and HYPOTHESIS.md |
| 8 | Verification status not written back | All 53 case objects show verifier_status "pending"; 12 check definitions undocumented; opaque verification pass | Full concession — status contradicts filename; check definitions must be documented; both gaps closed | Resolved: critic wins — Blocker resolved; verification status written back, check definitions documented in benchmark_verification_checks.md |
| 9 | Difficulty labels empirically unvalidated | No pilot confirming easy >= 0.85 baseline; v3 easy baseline = 0.50; labels may be systematically optimistic | Verification caught one mislabeling; v3 easy=0.50 suggests possible optimism; 5-10 case baseline pilot recommended before full execution | Open |
| 10 | Point resolution rate conflates concession types | Any "Resolved" entry counts identically regardless of whether concession was substantive or social pressure | Correctly scoped as diagnostic-only in preregistration; conflation risk constrained to interpretive use; human-classification check warranted if cited in conclusions | Resolved: empirical_test_agreed — metric is diagnostic-only; human classification check triggered if cited |

---

## Round 1 — Complete

Issues 2, 3, 4, 5, 6 resolved by Defender partial concessions and the Critic acknowledging the implementation is correct (Issue 3).
Issues 7, 8 resolved as hard blockers; both corrected before execution.
Issue 10 resolved as diagnostic-scoped.
Issues 1 and 9 remain open for Round 2.

## Round 2 — Complete

**Issue 1:** `empirical_test_required` — multiround vs. isolated_debate confounded by Defender information exposure (Defender sees Critique; Critic does not see Defender first pass). Cannot isolate exchange effect from information access effect within current design. Proposed control: one-shot condition where Defender sees Critique but no second round occurs. Outside current design scope.

**Issue 9:** `critique_wins` — pilot revised to 15 cases minimum (5+ easy, 5+ medium, 5+ hard). Decision rule must cover three branches: (a) easy baseline < 0.70 → audit and relabel all easy cases before full execution; (b) 0.70–0.84 → proceed with calibration uncertainty noted; (c) ≥ 0.85 → proceed as planned. Forced_multiround scope adjustment is secondary, not a substitute for the relabeling gate.

## Final Status

| # | Final Status |
|---|-------------|
| 1 | empirical_test_required |
| 2 | Resolved: defender wins (partial) |
| 3 | Resolved: defender wins |
| 4 | Resolved: defender wins (partial) |
| 5 | Resolved: defender wins (partial) |
| 6 | Resolved: defender wins (partial) |
| 7 | Resolved: critic wins (blocker fixed) |
| 8 | Resolved: critic wins (blocker fixed) |
| 9 | Resolved: critique_wins |
| 10 | Resolved: empirical_test_agreed (diagnostic-only scope) |

---

### Defender — Round 2

#### Issue 1 — Information asymmetry as confound in the multiround vs. isolated_debate comparison

The Critic's sharpened position is correct on the structural asymmetry: in multiround, the Defender sees the Critique before its first response, while the Critic does not see the Defender's initial output before generating Round 2. This is not symmetric exchange — it is Defender-information exposure plus one additional round. Any performance difference between multiround and isolated_debate therefore conflates (a) the Defender having seen the Critique at all and (b) the Critic having seen the Defender response and sharpened its position. Those are distinguishable causes and the current design cannot separate them.

The Critic's proposed control — a condition where the Defender sees the Critique but no second round occurs — would isolate information exposure from exchange. That condition does not exist in the design.

**Concede.** The Critic's force-resolution is accepted: the comparison is confounded by Defender information exposure, and the proposed empirical test (Critic-sees-only condition) would be necessary to cleanly attribute any multiround advantage to exchange vs. mere information access. This is a real limitation on the causal interpretation of the multiround vs. isolated_debate comparison. It does not invalidate the comparison as a descriptive finding, but the mechanistic inference — that exchange rounds drive improvement — is not supportable from this design alone.

Status update: **empirical_test_required** — the confound is real; the proposed control condition is the correct test; the current design cannot resolve the attribution.

---

#### Issue 9 — Pilot size and decision rule scope

The Critic's sharpened position has two components: (1) the pilot needs 15+ cases with 5+ easy cases, not 5-10 cases; and (2) the preregistered decision rule must cover relabeling, not only forced_multiround scope adjustment, if easy baseline falls below 0.70.

On component (1): the Critic is correct that 5-10 cases is underpowered for validating difficulty stratification across three tiers. With 12 easy cases in the full benchmark, a 5-case pilot may include zero or one easy case by chance, making it useless for the specific check the pilot is meant to perform. A 15-case pilot with 5+ easy cases is a defensible minimum. This is a concession — the original pilot specification was underspecified.

On component (2): the original Round 1 defense committed to difficulty-stratified lift reporting and acknowledged forced_multiround scope as the primary remediation. The Critic is correct that this leaves the most consequential failure unaddressed: if easy cases are mislabeled at scale, the lift threshold interpretation is wrong, not just the H3 comparison. A preregistered decision rule that only adjusts forced_multiround scope while leaving mislabeled easy cases in the benchmark would produce a misleading primary metric. The decision rule must include a relabeling branch.

**Concede both components.** The pilot specification should be revised to: 15 cases minimum, stratified to include at least 5 easy cases, 5 medium cases, and 5 hard cases. The preregistered pilot decision rule must cover: (a) if easy baseline mean < 0.70, audit all easy cases for relabeling before full execution; (b) if easy baseline mean is in 0.70-0.84, flag as boundary and proceed with difficulty-stratified reporting but note calibration uncertainty; (c) if easy baseline >= 0.85, proceed as planned. Forced_multiround scope adjustment is a secondary consequence of hard-case validation, not a substitute for the relabeling gate.

Status update: **critique_wins** — both the pilot size and the decision rule scope require revision before execution; the defender's prior position on Issue 9 was insufficiently concrete on the relabeling branch.
