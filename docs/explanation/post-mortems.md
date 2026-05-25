# Post-Mortems & Lessons

Three experiment versions (v3, v4, v5) produced formal post-mortems documenting what broke and what the fixes revealed about LLM evaluation.

## v3: Scoring infrastructure failures

**What broke:** The measurement infrastructure failed before the thing being measured could be evaluated. Specific issues:

- Scoring bugs where rubric dimensions were applied inconsistently across cases
- Judge reliability varied across case types without this variation being measured
- Composite metrics masked dimension-level effects

**Lesson:** Instrument the measurement before measuring the subject. A rubric that produces a number is not the same as a rubric that produces a *reliable* number. v3's post-mortem led directly to v4's pre-registration requirement — if the rubric had been locked before cases were scored, the inconsistencies would have surfaced as violations rather than silently degrading results.

## v4: Specification drift

**What broke:** Implementation changes during the experiment silently violated the pre-registration constraints. The pre-registered hypothesis said one thing; the code measured something subtly different. The divergence was small enough to miss in code review but large enough to invalidate the result.

**Lesson:** Pre-registration without enforcement is just documentation. v4's post-mortem produced `/intent-watch` — automated monitoring that catches drift as it happens rather than after the experiment concludes. The key insight was that drift is normal and expected during implementation; the problem is *undetected* drift.

## v5: Case difficulty calibration

**What broke:** Benchmark cases were too easy. Critics found planted flaws at near-100% rates, which meant the evaluation couldn't distinguish a good critic from a mediocre one. The cases had obvious tells — naming conventions, structural patterns, or severity levels that were too uniform.

**Lesson:** Generating hard evaluation cases is itself a hard problem. v5's response was a dedicated case generation pipeline with validation gates: each case was tested against multiple LLMs before entering the benchmark, and cases where all models succeeded trivially were rejected or revised. The pipeline went through three architectural iterations before producing cases that reliably separated critic quality levels.

## Cross-cutting themes

Three patterns appear across all post-mortems:

1. **Silent failures are worse than loud ones.** Every major issue was discovered after results were produced, not during execution. The PoC appeared to work; the scores appeared reasonable; the drift appeared minor. Building detection into the process (pre-registration enforcement, rubric prevalence audits, difficulty calibration gates) is cheaper than post-hoc forensics.

2. **The measurement is the hardest part.** In all three cases, the underlying ML methodology being evaluated was less problematic than the evaluation infrastructure. Building a critic is easier than building a reliable way to measure whether the critic is good.

3. **Post-mortems produce features.** Every post-mortem led to a concrete ml-lab feature: v3 produced pre-registration, v4 produced `/intent-watch`, v5 produced the case generation pipeline. The features weren't designed speculatively — they were responses to documented failures.
