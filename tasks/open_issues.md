# Open Issues — Post-Adversarial Review

Raised by ml-critic and ml-defender during the meta-debate on v2 findings (2026-04-04).
Ordered by expected impact on the core claim.

---

## Priority 1 — Addresses the Core Lift Claim

### 1. Budget-Matched Ensemble Baseline

**Issue:** The debate protocol runs 3-4× more tokens than the single-pass baseline (Critic + Defender + Judge vs. one call). The reported lift may be partly a compute/chain-of-thought aggregation effect rather than an adversarial role structure effect.

**Test:** Run a compute-matched ensemble baseline — three independent single-pass responses per case synthesized by a fourth call, with no Critic/Defender role differentiation. Compare to the debate protocol on the same 20 cases.

**Verdict criteria:**
- If ensemble ≈ debate on non-defense_wins cases → compute budget explains the non-defense_wins lift; role structure does not
- If ensemble < debate on defense_wins cases specifically → isolation architecture is the load-bearing mechanism (expected, since no single-pass system can structurally challenge adversarial framing)
- If ensemble ≈ debate on defense_wins cases → the finding is weaker than claimed

**Effort:** ~80 API calls (4 per case × 20 cases). New script needed: `self_debate_ensemble_baseline.py`.

---

### 2. Recover or Regenerate Raw Transcript Scores (DRQ Cap Effect)

**Issue:** `self_debate_transcripts.py` is missing — it was never committed. The raw baseline DRQ scores before the cap was applied are unknown. Nine cases have DRQ=0.5, which is exactly at the cap ceiling; it's unknown whether these were naturally 0.5 or capped from something higher.

**Fix (Option A — Preferred):** Locate the original investigation session context where transcripts were generated and recover the file. Commit it.

**Fix (Option B):** Re-run the baseline scorer for the 9 DRQ=0.5 cases using the embedded baseline transcript text from `self_debate_results.json` (the `transcripts.baseline` field is present in the JSON). Extract the natural DRQ score without the cap applied.

**Verdict criteria:** If any natural DRQ > 0.5 is found, recompute baseline aggregate with the cap removed and report alongside current figures.

**Effort:** Low (Option B — baseline transcripts are already in the JSON).

---

### 3. Fix Stale Baseline Pass Flags in self_debate_results.json

**Issue:** `broken_baseline_001` and `metric_mismatch_002` are marked `baseline_pass: true` in the JSON, but their stored baseline scores have DC=0.0, which fails the per-dimension floor check (all applicable dims ≥ 0.5). The pass flags were set before the DC override was applied.

**Fix:** After resolving issues 1–2 above, re-run `self_debate_poc.py` to regenerate a consistent `self_debate_results.json`. Until then, note the inconsistency in `CONCLUSIONS.md` and `REPORT.md`.

**Impact:** The reported "baseline pass count = 2" is wrong. With DC=0.0, the correct baseline pass count is 0. With DC=0.5, it's 8. Neither matches the reported 2.

**Effort:** Trivial code fix once the root causes above are addressed.

---

## Priority 2 — Addresses External Validity

### 4. Two-Pass Defender Fix for Reasoning/Label Disconnect

**Issue:** `real_world_framing_001` failed because the Defender correctly identified all critical flaws in analysis text but labeled the verdict `defense_wins` — a reasoning-to-label translation error. The proposed fix (require analysis pass before verdict selection) has not been tested.

**Test:** Modify the `ml-defender` prompt to require a two-pass structure:
1. Analysis pass: identify all issues, concessions, and sound aspects
2. Verdict pass: "Given your analysis above, if you identified critical unaddressed flaws, your verdict is `empirical_test_agreed` or `critique_wins` — not `defense_wins`."

Re-run the 3 failed/partial cases (`real_world_framing_001`, `defense_wins_003`, `defense_wins_005`). If failure rate drops from 3/3 to 0/3, the fix is tractable and should be merged into `~/.claude/agents/ml-defender.md`.

**Effort:** Prompt edit + 3 targeted re-runs (~18 API calls).

---

### 5. Cross-Model Scorer Validation

**Issue:** The Scorer agent is claude-sonnet-4-6 — the same model family that played Critic, Defender, Judge, and Baseline. A model scoring its own outputs against ground truth it effectively generated may exhibit self-consistency bias: recognizing its own phrasing and mapping it to expected labels. The 1.000 IDR across 15 applicable cases is consistent with this effect.

**Test:** Have a different model family (GPT-4o or Gemini 1.5 Pro) score the same embedded transcripts against the same rubric, without access to `must_find` labels. Compare IDR scores. If IDR shifts by >±0.1 on average, self-scoring bias is material.

**Effort:** ~30 scorer calls via a different API. Requires a scoring script that accepts an external model endpoint.

---

### 6. Independent Benchmark Construction

**Issue:** The benchmark designer knew the planted flaws and wrote the prompts. All 20 cases have determinate answers and no missing information as the primary challenge — the designer may unconsciously have made flaws discoverable by the kind of reasoning they knew the model could do. Internal validity is established; external validity is not.

**Test:** Construct a parallel 10-case benchmark from external sources:
- Published ML paper retractions (NeurIPS/ICML reproducibility track)
- Kaggle competition post-mortems with documented evaluation failures
- Ground truth established by domain consensus, not the protocol designer

Run the same protocol and report IDR. If it drops below 0.85, benchmark construction leakage was material.

**Effort:** Significant. Requires sourcing and authoring cases from external materials; estimate 5-10 hours of case construction.

---

## Priority 3 — Statistical Rigor

### 7. Convergence Hypothesis — Adequate Sample Sizes

**Issue:** The secondary hypothesis ("convergence rate decreases with difficulty") was tested with 3 easy cases, 10 medium cases, and 7 hard cases. The easy=0.833 estimate is driven by a single data point (defense_wins_003, conv=0.5). No confidence intervals were reported. The hypothesis is neither confirmed nor refuted — it is underpowered.

**Fix:** Expand the benchmark to ≥10 cases per difficulty tier before re-testing the convergence hypothesis. Alternatively, report CIs on the current per-tier estimates and acknowledge the easy-tier estimate is n=3.

**Effort:** Requires adding ~17 new benchmark cases (7 easy cases minimum). This is also an opportunity to expand the `real_world_framing` category, which is currently 2 cases.

---

## Status Tracking

| # | Issue | Priority | Status | Blocking |
|---|-------|----------|--------|---------|
| 1 | Budget-matched ensemble baseline | P1 | Open | Core lift claim |
| 2 | Recover/recompute raw DRQ scores | P1 | Open | Accurate sensitivity |
| 3 | Fix stale baseline pass flags | P1 | Open | #2 (rerun) |
| 4 | Two-pass Defender fix + retest | P2 | Open | None |
| 5 | Cross-model scorer validation | P2 | Open | None |
| 6 | Independent benchmark | P2 | Open | None |
| 7 | Convergence — adequate n per tier | P3 | Open | None |
