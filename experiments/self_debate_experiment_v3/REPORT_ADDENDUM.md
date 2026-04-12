# Report Addendum: Production Re-Evaluation

This addendum addresses what changes when the self-debate protocol moves from a closed benchmark to a live ML review workflow. It covers operational considerations, deployment failure modes, and update latency — none of which appear in the primary report's hypothesis-driven analysis.

---

## What Changes If Deployed in a Real ML Review Workflow?

**The answer key disappears.** The benchmark uses pre-specified must_find_issue_ids and acceptable_resolutions as scoring targets. In production, these don't exist — the protocol must produce a verdict, an issue list, and optionally an empirical test specification with no oracle to check against. The measurable properties of the output (structured format, verdict type validity, ETD key presence) can still be verified, but correctness relative to ground truth cannot.

This has an immediate consequence for the corrected lift figure (+0.127 / +0.138): it was computed on a benchmark where must_not_claim false-positive guards are explicitly enumerated. In production, a reviewer may raise issues that are plausible but wrong, and there is no pre-specified list to catch them. IDP=1.0 across all conditions in the benchmark may be optimistic.

**Defense cases are the hardest production scenario.** Defense_wins cases (n=11 in the benchmark, 11/11 pass rate across all debate conditions) require the system to exonerate the ML paper's claims — to correctly conclude that a critique is wrong. On the benchmark, the correct answer is known. In production, a real reviewer who is too aggressive produces false positives with no mechanism to detect them in real time. The benchmark demonstrates that the debate protocol can exonerate cleanly (11/11 correct defenses); production cannot verify this without an independent audit, which reintroduces the human labor the system was meant to reduce.

**The closed-loop design is optimistic against unfamiliar distributions.** All benchmark cases are GPT-generated (claude-sonnet-4-6 as scorer, GPT-generated as cases). The external validation (16 cases, including 13 published-paper cases) provides evidence of cross-corpus generalization, but the scorer remains claude-sonnet-4-6 throughout. Against a genuinely unfamiliar domain (e.g., proprietary biobank studies, non-English language papers, non-standard experiment designs), the scorer's familiarity advantage may not hold and absolute scores may drop. Relative comparisons (debate vs. baseline) should be more stable than absolute scores, but this has not been tested.

---

## Update Latency: How Quickly Can Post-Mortem Fixes Be Applied?

**ETD schema mismatch (scorer bug).** The scorer bug (compute_etd() expected measure/success_criterion/failure_criterion but agents produced condition/supports_critique_if/supports_defense_if) was discovered after all 588 benchmark runs completed and fixed within the same session: one function updated, six scripts re-run (stats_analysis.py, sensitivity_analysis.py, extract_within_case_variance.py, difficulty_validation.py, generate_figures.py, coherence_audit.py). Total fix time: approximately 10 minutes. Five cases changed from FAIL to PASS.

In production, a scorer bug discovered after deployment requires re-evaluating all historical cases to apply the corrected scorer. With 588 runs already complete, re-running the scorer (not the agents) is computationally inexpensive. But at production scale — hundreds of papers reviewed over weeks — the latency of discovering a systematic scorer error, communicating it to users, and retroactively correcting stored verdicts is a real operational cost. Scorer versioning (tagging each stored verdict with the scorer version that produced it) would allow targeted re-evaluation without re-running all cases.

**Isolation breach fix (2 cases re-run).** Two isolation breaches were detected by check_isolation.py and both cases were re-run before scoring — handled within the same session. In production, isolation breaches would require a re-run queue: the original runs are invalidated, the affected cases go back through the full agent pipeline (critic, defender, adjudicator), and the stored verdicts are updated. With a queue-based architecture (each case dispatched independently), re-runs for isolated cases can be inserted into the queue without affecting other cases. The fix latency is dominated by agent execution time, not orchestration overhead.

---

## Operational Complexity

**Cost (agent calls).** 588 main benchmark runs at approximately 3 agent invocations each (critic, defender, adjudicator) = ~1,764 agent calls for the main benchmark. The external benchmark adds 192 runs (~576 agent calls). Multiround adds rounds beyond the first: 173/189 multiround runs resolved in round 1, 11 required round 2, 5 required 0 rounds — adding approximately 16 extra invocations above the single-round count. Total across all conditions: ~2,800+ agent calls for 49 cases × 4 conditions × 3 runs. In production, each unique case review is a single run of one condition — approximately 3–4 agent calls per paper.

**Latency.** Multiround is sequential: each round depends on the previous round's output. Isolated debate and ensemble can parallelize all assessors across cases simultaneously. Baseline is trivially fast (single agent invocation). For real-time review workflows where latency matters, isolated_debate or ensemble are preferable to multiround. The 7-batch parallel execution in Phase 6 reduced wall-clock time by running 7 cases concurrently; a production queue-based architecture dispatching each case independently would scale this further.

**The 4-round cap.** Multiround was capped at 4 rounds per case in this experiment. In practice, 91.5% of cases resolved in round 1 (173/189 runs). The cap was never a binding constraint — no case reached 4 rounds. In production, a 2-round cap with a force-resolution instruction would cover 97.4% of cases (rounds 1 and 2) while eliminating the tail risk of pathological non-convergence.

---

## Production Failure Modes That Differ From Benchmark Failure Modes

**Verdict type errors** (real_world_framing_003: `mixed` verdict). In production, no post-hoc validator catches an invalid verdict type. The benchmark scorer detects FVC=0.0 when the verdict is not in acceptable_resolutions; in production, an invalid verdict (`mixed`) would be returned to the user with no flag, and the user would have no reliable way to know the verdict type is structurally wrong. Mitigation: add explicit output validation to the adjudicator prompt constraining the valid verdict set (`critique_wins`, `defense_wins`, `empirical_test_agreed`), and add a format check at the API boundary that rejects any verdict not in this set.

**ETD specification absent on empirical cases** (real_world_framing_005, real_world_framing_008). The isolated debate adjudicator produced `critique_wins` without an ETD specification on two cases where the ground truth was `empirical_test_agreed`. In production, ETD absence is not flagged — the user receives a critique verdict with no test design, and cannot determine whether an empirical test was considered and rejected, or never considered at all. The ensemble synthesizer avoids this failure because it has an explicit ETD-forcing instruction. Mitigation: add the same ETD-forcing instruction to the isolated debate adjudicator prompt: "If any assessor identifies a contested empirical claim, you must produce an empirical test specification with condition, supports_critique_if, and supports_defense_if populated, regardless of verdict."

**Isolation breaches.** In the benchmark, two runs were silently contaminated (Defender received Critic output) before check_isolation.py detected them. In production without a post-hoc isolation check, contaminated runs would propagate to stored verdicts. check_isolation.py-style verification should run automatically after each debate, not as a separate post-hoc analysis step. The check is inexpensive (reading the agent task output fields) and should be integrated into the orchestration layer as a required gate before the adjudicator is invoked.

**Schema drift.** The ETD schema divergence (scorer expected one key set, agents produced another) would silently corrupt scores in production — ETD would score 0.0 on all cases where the correct keys were present but under the wrong names. No error would be raised; the scorer would simply not find the keys and return 0.0. Mitigation: enforce structured output schemas on all agent roles using the model API's structured output feature (or a JSON schema validator at output time). Schema validation at agent output time would have caught this bug before any scoring ran.
