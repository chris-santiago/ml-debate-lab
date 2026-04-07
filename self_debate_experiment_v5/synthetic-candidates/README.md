# synthetic-candidates/

This directory contains v5 benchmark case generation prompts and, after generation, raw candidate cases produced by external LLMs as inputs to the v5 experiment pipeline.

## Generation

Two prompts are provided, each targeting different hard-case sources:

1. **`benchmark_case_generation_prompt.md`** — main 60-case prompt (easy + medium + hard), executed against a non-Anthropic LLM (GPT-4o, GPT-5, Gemini, etc.).
2. **`REAL_PAPER_CASE_GENERATION_PROMPT.md`** — supplementary hard-case-only prompt grounded in real published ML paper flaws, transposed to anonymized domains. Produces cases with IDs `eval_scenario_101`+.

The v5 prompts supersede v4 with a redesigned hard case generation strategy, motivated by v4 Phase 6 findings: all hard cases scored 1.0 on single-pass assessment, producing no difficulty separation. Root cause: hard case flaws were detectable by internal consistency checking (cross-paragraph contradiction), which LLMs do trivially.

**v5 design changes (hard cases only; easy/medium cases are unchanged):**

- **8 design principles** requiring flaws that cannot be found by internal consistency checking — flaws must be wrong assumptions, quantitative errors requiring computation, critical omissions, or subtly wrong justifications
- **4 flaw types** (A: Assumption Violations, B: Quantitative Errors, C: Critical Omissions, D: Subtly Wrong Justifications) replacing the v4 "structural difficulty" approach
- **Empirically-grounded detection patterns** to design against: Diff-the-Paragraphs, Claim-vs-Evidence Gap Analysis, Label Provenance Tracing, Observational Study Confound Enumeration
- **Trigger phrase prohibition list** derived from v4 raw agent output analysis
- **500–800 word prompts** for hard cases (v4: 200–400 words), written as confident internal memos with no problem statements
- **Opaque case IDs** (`eval_scenario_NNN`) for hard cases to prevent category leakage
- **Run-to-Run Variation Test** as a 5th self-evaluation gate: cases that produce verbatim-identical outputs across runs are too easy
- **Hard case acceptance criteria**: a `claude-haiku-4-5` single-pass assessor must score mean < 0.55

**Real-paper prompt additions:**

- **12-paper source library** covering documented methodological failures (Dacrema 2019, Obermeyer 2019, DeGrave 2021, Lazer 2014, Zech 2018, Recht 2019, Hooker ROAR 2019, SMOTE-before-CV, Caruana 2015, time series leakage, offline-online recommendation gap, RLHF reward overoptimization)
- **Source Recognition Test** as a 6th self-evaluation gate: a reviewer who has read the source paper must not recognize it
- **`source_paper` schema field** (real-paper cases only)
- **Domain transposition table** to prevent shortcut learning via source familiarity

## Role in the pipeline

These files are raw LLM output — unvalidated and unverified. They feed into the v5 pipeline starting at Phase 0:

1. **Phase 0** — `validate_cases.py` checks schema compliance and composition targets (category balance, difficulty distribution, defense_wins coverage, must_find population). Run against both JSON files and merge before verification.
2. **Phase 1** — `CASE_VERIFIER` agent reviews each case for flaw authenticity, benchmark quality, and external sourcing of defense_wins cases
3. **Phase 5.5** — Difficulty gate: sample 10 hard cases, run `claude-haiku-4-5` single-pass; ≥6/10 must score mean < 0.55. Regenerate hard cases if gate fails.
4. Output of verification is `benchmark_cases_verified.json`, which is what the experiment actually runs against

The `.json` files in this directory are candidates only. Do not use them directly for scoring or analysis — use `benchmark_cases_verified.json` produced by Phase 1.

## Files

| File | Role |
|---|---|
| `benchmark_case_generation_prompt.md` | **Main v5 generation prompt** — 60-case prompt (easy/medium/hard) with v5 hard case redesign integrated; paste to external LLM to generate `openai_benchmark_cases.json` |
| `REAL_PAPER_CASE_GENERATION_PROMPT.md` | **Real-paper hard-case prompt** — grounded in 12 published ML paper flaw mechanisms transposed to anonymized domains; produces `real_paper_cases.json` |
| `openai_benchmark_cases.json` | **Main candidate cases** — raw LLM output from main prompt; 50 cases (10 easy, 20 medium, 20 hard) after generator self-curation |
| `real_paper_cases.json` | **Real-paper candidate cases** — raw LLM output from real-paper prompt; 14 hard cases (`eval_scenario_101`–`eval_scenario_114`) |
| `benchmark_summary.md` | **Main prompt generator self-critique** — composition counts, difficulty discrimination predictions, disqualified/flagged cases, self-critique |
| `real_paper_cases_summary.md` | **Real-paper generator self-critique** — per-case summaries with planted issues, scoring targets, and self-evaluation notes |

## Benchmark summary

### Main prompt (`openai_benchmark_cases.json`)

50 cases after generator self-curation (10 disqualified from an original larger set).

| Split | Count |
|---|---:|
| Easy | 10 |
| Medium | 20 |
| Hard | 20 |

| Category | Count |
|---|---:|
| broken_baseline | 8 |
| metric_mismatch | 8 |
| hidden_confounding | 8 |
| scope_intent_misunderstanding | 6 |
| defense_wins | 11 |
| real_world_framing | 9 |

Predicted difficulty discrimination (failed rubric dimensions, single-pass assessor):

| Difficulty | Predicted failed dims | Target |
|---|---:|---|
| Easy | 0.3 | ≤ 0.5 |
| Medium | 1.0 | 0.5–1.5 |
| Hard | 2.6 | ≥ 2.0 |

### Real-paper prompt (`real_paper_cases.json`)

14 hard cases (`eval_scenario_101`–`eval_scenario_114`), all grounded in documented published paper flaws.

| Category | Count |
|---|---:|
| broken_baseline | 3 |
| metric_mismatch | 2 |
| hidden_confounding | 3 |
| scope_intent_misunderstanding | 3 |
| defense_wins | 2 |
| real_world_framing | 1 |

## Generator self-critique

### Main prompt

1. Several hard cases rely on domain-specific norms (clinical validation, off-policy evaluation, AML queue auditing). That is desirable for discrimination, but some reviewers may argue a subset drifts from general-ML methodology into domain-governance judgment.
2. The final benchmark intentionally includes many mixed-position cases. That improves calibration and ETD/DRQ stress-testing, but it also increases scorer burden because acceptable resolutions are sometimes broader than simple critique_wins / defense_wins labels.
3. Some easy/medium cases remain classic benchmark motifs by design so the trivial baseline can succeed on a non-trivial fraction of the set. An adversarial reviewer may say a few of these cases are familiar rather than novel, though they serve the benchmark's lift-measurement purpose.

### Real-paper prompt

See `real_paper_cases_summary.md` for per-case self-evaluation notes. Each of the 14 cases passed all 6 self-evaluation tests including the Source Recognition Test.
