# synthetic-candidates/

This directory contains the v5 benchmark case generation prompt and, after generation, raw candidate cases produced by an external LLM as inputs to the v5 experiment pipeline.

## Generation

Cases are generated using the v5 case generation prompt (`self_debate_experiment_v5/synthetic-candidates/benchmark_case_generation_prompt.md`), executed on a non-Anthropic LLM (GPT-4o, GPT-5, Gemini, etc.).

The v5 prompt supersedes the v4 prompt with a redesigned hard case generation strategy, motivated by v4 Phase 6 findings: all hard cases scored 1.0 on single-pass assessment, producing no difficulty separation. Root cause: hard case flaws were detectable by internal consistency checking (cross-paragraph contradiction), which LLMs do trivially.

**v5 design changes (hard cases only; easy/medium cases are unchanged):**

- **8 design principles** requiring flaws that cannot be found by internal consistency checking — flaws must be wrong assumptions, quantitative errors requiring computation, critical omissions, or subtly wrong justifications
- **4 flaw types** (A: Assumption Violations, B: Quantitative Errors, C: Critical Omissions, D: Subtly Wrong Justifications) replacing the v4 "structural difficulty" approach
- **Empirically-grounded detection patterns** to design against: Diff-the-Paragraphs, Claim-vs-Evidence Gap Analysis, Label Provenance Tracing, Observational Study Confound Enumeration
- **Trigger phrase prohibition list** derived from v4 raw agent output analysis
- **500–800 word prompts** for hard cases (v4: 200–400 words), written as confident internal memos with no problem statements
- **Opaque case IDs** (`eval_scenario_NNN`) for hard cases to prevent category leakage
- **Run-to-Run Variation Test** as a 5th self-evaluation gate: cases that produce verbatim-identical outputs across runs are too easy
- **Hard case acceptance criteria**: a `claude-haiku-4-5` single-pass assessor must score mean < 0.55

## Role in the pipeline

These files are raw LLM output — unvalidated and unverified. They feed into the v5 pipeline starting at Phase 0:

1. **Phase 0** — `validate_cases.py` checks schema compliance and composition targets (category balance, difficulty distribution, defense_wins coverage, must_find population)
2. **Phase 1** — `CASE_VERIFIER` agent reviews each case for flaw authenticity, benchmark quality, and external sourcing of defense_wins cases
3. **Phase 5.5** — Difficulty gate: sample 10 hard cases, run `claude-haiku-4-5` single-pass; ≥6/10 must score mean < 0.55. Regenerate hard cases if gate fails.
4. Output of verification is `benchmark_cases_verified.json`, which is what the experiment actually runs against

The `.json` files in this directory are candidates only. Do not use them directly for scoring or analysis — use `benchmark_cases_verified.json` produced by Phase 1.

## Files

| File | Role |
|---|---|
| `benchmark_case_generation_prompt.md` | **V5 generation prompt** — full 60-case prompt with v5 hard case redesign integrated; paste to external LLM to generate `benchmark_cases.json` |
| `benchmark_cases.json` | **V5 candidate cases** — raw LLM output; populated after generation |

## Benchmark summary

*To be populated after case generation.*

## Generator self-critique

*To be populated after case generation.*
