# v8: Iterating on the Defender — Making ml-lab Say "Defense Wins"

## Problem Statement

ml-lab cannot exonerate sound methodology. Across all v7 conditions (480 defense-case evaluations: 4 conditions x 40 cases x 3 runs), the system produces **zero** `defense_wins` verdicts. The best outcome is `empirical_test_agreed` (a hedge, scored 0.5) — achieved on 50% of multiround defense runs. The system's critique bias means every methodology gets flagged, every design gets questioned, and the system recommends experiments that aren't needed.

A review system that can't say "this is fine, proceed" trains its users to ignore it.

## Diagnosis: Why 0% Exoneration?

### The Smoking Gun — Prompt Asymmetry

The defender prompt (`plugins/ml-lab/ml-defender.md`) mentions **"concede" 5 times**:
- Line 31: "Concede — the critique is correct."
- Line 49: "Concede — the critic's sharpened argument is convincing."
- Line 57: "You must concede when the critic makes a genuinely good point."
- Line 76: "If it didn't, concede."
- Line 89: "If the critic identifies a genuine flaw, concede immediately."

It mentions `defense_wins` **once** — to say when NOT to use it:
- Line 35: "...your overall verdict must be `empirical_test_agreed` or `critique_wins` — not `defense_wins`."

There is **zero instruction for when `defense_wins` IS the correct verdict.** The prompt has no exit path for "I reviewed the critique and none of it holds up — the methodology is sound."

The critic prompt (`plugins/ml-lab/ml-critic.md`) has zero mentions of `defense_wins` or exoneration. The critic cannot output "this methodology is sound." It is structurally incapable of finding nothing wrong.

### Three Compounding Mechanisms

1. **The critic has no "nothing found" exit path.** The prompt says "find methodology flaws." Given any methodology, an instruction-tuned LLM will generate something — minor nits, edge cases, theoretical concerns. No threshold exists below which the critic says "not worth raising."

2. **The defender is prompted to concede, not to win.** Five explicit concession instructions vs. zero exoneration instructions. The persona calibration section (line 86-93) emphasizes conceding fast. There is no equivalent instruction for dismissing noise firmly.

3. **Adjudication has no cost model.** In v7, adjudication is handled inline by the orchestrating Claude context (ml-lab.md), not a separate adjudicator agent. The orchestrator weighs critique quality vs. defense quality but never asks: "Would acting on these critiques change the conclusions? Is the recommended experiment worth running?" Without a cost threshold, any non-zero critique wins.

## Goal

Iterate on ml-lab's agent prompts — primarily the defender, but also the critic and orchestrator adjudication logic — until the system can:

1. **Correctly exonerate sound methodology** (DER > 0.30 on defense cases)
2. **Without breaking detection** (IDR >= 0.75 on regular cases)
3. **Without increasing false hedging** (FVC_mixed on mixed cases does not regress)

### Metric Distinction: DER vs. FVC

FVC gives 0.5 credit for `empirical_test_agreed`. The system already hedges on 50% of multiround defense runs. Improving FVC is easy — just hedge more. The actual problem is confident exoneration: `defense_wins` verdicts on sound methodology. **DER (Defense Exoneration Rate) is the primary metric.** DER = proportion of defense cases receiving `defense_wins`.

## Approach: TDD for Prompt Engineering

### Phase 0 — Existence Proof (Kill Switch)

Before building any iteration framework, verify the capability exists.

**Test:** Take one obviously-sound defense case from the v7 benchmark. Hand-craft an ideal defender prompt for just that case — give it every advantage: explicit instruction to exonerate, explicit permission to dismiss critiques, the full context of why the methodology is sound.

- If the model produces `defense_wins` under ideal conditions -> the model CAN do this. The production prompt is the bottleneck. Proceed to Phase 1.
- If the model CANNOT produce `defense_wins` even with a perfect prompt -> prompt iteration won't help. Pivot to:
  - Cross-model defense (different model family as defender)
  - Architecture change (two-phase triage: classify before critiquing)
  - Stop and report the negative result

This is the plan's kill switch. Don't build the iteration framework until this passes.

### Phase 1 — Failure Mode Diagnosis

Pull v7 multiround transcripts for defense cases. Read them. Classify each failure:

| Failure Mode | What It Looks Like | Fix Target |
|---|---|---|
| Full concession | "The critic raises valid points..." | Defender prompt |
| Partial concession | "While the critic is partially correct..." | Defender prompt |
| Weak rebuttal | Defender argues but doesn't address the specific claim | Defender prompt |
| Correct rebuttal, ignored | Defender makes strong argument, adjudicator sides with critic | Orchestrator adjudication logic |
| Unfalsifiable critique | Critic raises something that can't be rebutted ("could have selection bias") | Critic prompt |
| Noise accumulation | Critic raises 5 minor nits, defender concedes 2, adjudicator sees 2 concessions as evidence | Critic prompt (significance threshold) |

The distribution across these categories determines which prompt to fix first. **Don't guess — read the transcripts.**

### Phase 2 — Fast Iteration Loop

**Canary set** (30 cases from v7 benchmark):
- 10 defense cases (prioritize the most egregious failures from Phase 1)
- 10 regular cases (regression check — detection must not degrade)
- 10 mixed cases (regression check — ambiguity recognition must hold)

**Per iteration:**
- 30 cases x 1 condition (multiround) x 3 runs = 90 evaluations
- Estimated cost: ~$5-10 per iteration (mix of Sonnet generation + gpt-5.4-mini scoring)
- Target: 10-15 iterations before full benchmark run

**Iteration protocol:**
1. One prompt change per iteration (defender OR critic OR orchestrator — never multiple)
2. Run canary set
3. Score: DER on defense, IDR on regular, FVC_mixed on mixed
4. Accept if primary metric improves without regressions; reject otherwise
5. Log each iteration as `experiment` journal entry with version/change/hypothesis/result
6. After 3-5 consecutive improvements on canary, run full benchmark to validate

**Full benchmark run:**
- All 280 v7 cases x 4 conditions x 3 runs = 3,360 evaluations
- Only triggered by consistent canary improvement
- Estimated cost: ~$150-200 per full run
- Budget cap: 2 full runs maximum ($400)

### Phase 3 — Intervention Candidates

Three interventions to test, ordered by expected impact based on the diagnostic (Phase 1 results may reorder):

**Intervention A: Critique Significance Threshold (critic prompt)**

After the critic produces findings, add a self-filtering step:

> "For each finding, classify: FATAL (invalidates conclusions), MATERIAL (weakens a central claim), MINOR (worth noting but doesn't affect conclusions), NIT (stylistic or theoretical). Only report FATAL and MATERIAL findings. If no findings reach MATERIAL threshold, explicitly state: 'No significant methodology flaws found.'"

This gives the critic a "nothing found" exit path. The defender only has to rebut material findings, not noise.

**Intervention B: Defender Exoneration Path (defender prompt)**

Add explicit instruction for when defense_wins is correct:

> "If your Pass 1 analysis finds that none of the critic's findings are FATAL or MATERIAL — that all findings are minor concerns, theoretical edge cases, or based on misunderstanding the design — your verdict MUST be `defense_wins`. Defending sound methodology against noise is not obstruction; it is the defender's primary function. A defender who concedes to immaterial critiques wastes experimental resources."

Balance the 5 concession instructions with explicit exoneration guidance.

**Intervention C: Cost-Weighted Adjudication (orchestrator logic)**

Add to the orchestrator's adjudication prompt:

> "Before rendering a verdict, evaluate the cost of action: recommending an unnecessary experiment has a cost (time, resources, trust erosion). Only recommend `empirical_test_agreed` if the expected information gain exceeds the cost of running the experiment. If the critique identifies only minor or immaterial issues, the methodology is sound and the verdict is `defense_wins`."

This addresses mechanism #3 — the adjudicator currently has no cost threshold.

## Scope and Limitations

### In Scope
- Prompt-level changes to defender, critic, and orchestrator adjudication logic
- Measured against v7 benchmark (280 cases, 3 strata)
- Canary-set-validated iteration with full benchmark confirmation

### Out of Scope (acknowledged, not addressed)
- **Token count confound.** Multiround processes more tokens than ensemble due to adjudicator context. The debate FVC_mixed advantage (v7: +0.225) may be partly explained by token budget, not adversarial structure. A "long-critic" control condition would test this. Scoped out of v8 — the goal here is making the existing architecture work better, not comparing architectures.
- **Cross-model defense.** Using a different model family as defender might break sycophancy. Pursued only if Phase 0 existence proof fails.
- **GAN-style benchmark generation.** The v7 benchmark is the fixed test suite. Building a harder benchmark is a separate effort (see journal memo 05dfae14).
- **New benchmark cases.** v8 uses the v7 benchmark as-is. Case quality improvements are future work.

## Success Criteria

| Metric | v7 Baseline | v8 Target | Rationale |
|---|---|---|---|
| DER (defense) | 0.00 | > 0.30 | System can exonerate at least 30% of sound methodology |
| IDR (regular) | 0.803 (ensemble) / 0.634 (multiround) | >= 0.75 (multiround) | Detection must not degrade |
| FVC_mixed (mixed) | 0.731 (multiround) | >= 0.70 | Ambiguity recognition must hold |
| FAR (defense) | 1.00 | < 0.50 | Fewer than half of sound cases get false critique_wins |

## Prompt Changelog Template

Each iteration is tracked:

```
Version:       defender-v{N}
Change:        {one-sentence description}
Hypothesis:    {what failure mode this addresses}
Canary DER:    {before} -> {after}
Canary IDR:    {before} -> {after}
Canary FVC_m:  {before} -> {after}
Verdict:       ACCEPT / REJECT
Journal ID:    {entry id}
```

## Cost Estimate

| Phase | Evaluations | Estimated Cost |
|---|---|---|
| Phase 0 (existence proof) | ~10 | ~$1 |
| Phase 1 (diagnosis) | 0 (transcript reading) | $0 |
| Phase 2 (iterations, 10-15x) | 900-1,350 | $50-150 |
| Full benchmark (2x max) | 6,720 | $300-400 |
| **Total** | | **$350-550** |

---------

 What about penalties for defaulting to experiment when the correct answer is defense wins. I am genuinely interested in how to make a better ml-lab
  system that ca confidently state “defense wins” and avoid useless experiments.

⏺ Now that's the real problem. Not "can debate beat ensemble on a rigged benchmark" but "why can't the system ever say 'this is fine'?"

  ★ Insight ─────────────────────────────────────
  The 0% exoneration rate isn't a benchmark calibration issue or a scoring issue. It's a structural bias in the system architecture. The critic is
  prompted to find flaws — it will always find something. The defender is sycophantic — it concedes rather than rebuts. The adjudicator has no mechanism
  to say "the critic's findings are noise." Every path through the system applies pressure toward critique_wins. There is no path that applies pressure
  toward defense_wins.
  ─────────────────────────────────────────────────

  Why this matters more than debate-vs-ensemble

  A real ML review system that can't say "proceed without experiments" is worse than useless — it trains its users to ignore it. Every methodology gets
  flagged. Every design gets questioned. The team runs unnecessary experiments to satisfy the system, or they stop trusting it. Either way, the system has
   failed.

  The practical cost function isn't symmetric:

  ┌───────────────────────┬──────────────────┬──────────────────────────────────────┐
  │      System says      │  Truth: flawed   │             Truth: sound             │
  ├───────────────────────┼──────────────────┼──────────────────────────────────────┤
  │ critique_wins         │ Correct (+1)     │ False alarm — wasted experiment (-1) │
  ├───────────────────────┼──────────────────┼──────────────────────────────────────┤
  │ empirical_test_agreed │ Cautious (+0.5)  │ Hedge — still wastes time (-0.5)     │
  ├───────────────────────┼──────────────────┼──────────────────────────────────────┤
  │ defense_wins          │ Missed flaw (-2) │ Correct — team moves fast (+1)       │
  └───────────────────────┴──────────────────┴──────────────────────────────────────┘

  Missing a real flaw is the worst outcome, but false alarms have a real cost that the current system ignores entirely. Right now the system optimizes
  exclusively for the top-left cell and doesn't care about the right column at all.

  Why 0% exoneration happens — structural diagnosis

  Three mechanisms compound:

  1. The critic has no "nothing found" exit path.
  The prompt says "find methodology flaws." Given any methodology, a sufficiently capable LLM will always generate something — minor nits, edge cases,
  theoretical concerns, stylistic preferences. There's no threshold below which the critic says "these aren't worth raising." Every observation, no matter
   how minor, gets surfaced as a finding.

  2. The defender concedes instead of rebutting.
  Sycophancy (Sharma et al., Yao et al.). The defender is supposed to argue "this methodology is sound" but instead produces "the critic raises valid
  concerns, however..." That partial concession is death — the adjudicator reads agreement where there should be disagreement.

  3. The adjudicator has no cost model.
  The adjudicator weighs critique quality vs. defense quality but doesn't ask: "Would acting on these critiques change the conclusions? Is the recommended
   experiment worth running?" Without a cost threshold, any non-zero critique wins.

  What to actually build

  This is three interventions, testable independently:

  Intervention A: Critique significance threshold.

  After the critic produces findings, run a critique validator (separate call, different prompt):

  ▎ "For each finding, answer: If this issue were resolved, would the paper's central conclusions change? Rate: FATAL / MATERIAL / MINOR / NIT."

  Only FATAL and MATERIAL findings survive. If no findings survive → defense_wins automatically, no debate needed.

  This directly addresses mechanism #1. The critic can still find everything — but a gate filters noise from signal before the rest of the pipeline sees
  it.

  Intervention B: Burden-of-proof inversion.

  Current architecture: critic asserts, defender rebuts, adjudicator decides. The prior is guilty-until-proven-innocent.

  Reversed: the methodology is presumed sound. The critic must overcome a presumption of soundness, like a prosecution must overcome presumption of
  innocence. Concretely:

  ▎ Adjudicator prompt: "The methodology is presumed sound. The critic has raised objections. For each objection, determine: does the critic provide
  ▎ sufficient evidence that this flaw would materially affect the conclusions? If not, the objection is dismissed. If no objections survive, the verdict
  ▎ is defense_wins."

  This addresses mechanism #3. The adjudicator isn't weighing "who argued better" — it's asking "did the critique clear a bar?"

  Intervention C: Anti-sycophancy defender prompting.

  Current defender prompt produces conciliatory language. Replace with an explicitly adversarial framing:

  ▎ "Your job is to find EVERY reason the methodology is sound. The critic's findings are listed below. For each one, determine if it is: (a) incorrect —
  ▎ the methodology does not have this flaw, (b) immaterial — even if true, it doesn't affect conclusions, (c) already mitigated — the methodology already
  ▎  addresses this. Do NOT concede any point you can rebut. Concession without exhausting all counterarguments is a failure."

  This addresses mechanism #2. The defender is told that concession is failure, not politeness.

  The experiment design

  Benchmark: Defense cases with stratified difficulty:

  ┌───────────────────┬──────────────────────────────────────────────────────────────────────┬─────┐
  │      Stratum      │                             Description                              │  n  │
  ├───────────────────┼──────────────────────────────────────────────────────────────────────┼─────┤
  │ Obvious-sound     │ Clean methodology, no reasonable critique                            │ 30  │
  ├───────────────────┼──────────────────────────────────────────────────────────────────────┼─────┤
  │ Subtle-sound      │ Methodology that looks questionable but is actually correct          │ 30  │
  ├───────────────────┼──────────────────────────────────────────────────────────────────────┼─────┤
  │ Trap cases        │ Methodology with minor nits that look like flaws but aren't material │ 30  │
  ├───────────────────┼──────────────────────────────────────────────────────────────────────┼─────┤
  │ Regular (control) │ Actual flaws, to verify interventions don't break detection          │ 60  │
  └───────────────────┴──────────────────────────────────────────────────────────────────────┴─────┘

  Conditions: Test each intervention independently and in combination:

  ┌────────────────┬───────────────┬────────────┬──────────────┐
  │   Condition    │ A (threshold) │ B (burden) │ C (anti-syc) │
  ├────────────────┼───────────────┼────────────┼──────────────┤
  │ v7-baseline    │ -             │ -          │ -            │
  ├────────────────┼───────────────┼────────────┼──────────────┤
  │ threshold-only │ ✓             │ -          │ -            │
  ├────────────────┼───────────────┼────────────┼──────────────┤
  │ burden-only    │ -             │ ✓          │ -            │
  ├────────────────┼───────────────┼────────────┼──────────────┤
  │ anti-syc-only  │ -             │ -          │ ✓            │
  ├────────────────┼───────────────┼────────────┼──────────────┤
  │ full-stack     │ ✓             │ ✓          │ ✓            │
  └────────────────┴───────────────┴────────────┴──────────────┘

  Metrics:
  - Defense Exoneration Rate (DER): % of defense cases correctly receiving defense_wins
  - False Alarm Rate (FAR): % of defense cases incorrectly receiving critique_wins
  - IDR on regular cases: must not degrade (the intervention shouldn't break detection)
  - Cost-weighted FC: FC with asymmetric penalties per the table above

  Pre-registered hypothesis: Full-stack DER > 0.30 on defense cases while maintaining IDR ≥ 0.75 on regular cases. (v7 DER was 0.00.)

  Why this is a better v8

| | "Make debate beat ensemble" | "Make the system say defense_wins" |
  |---|---|---|
  | Circularity risk | Fatal — selecting for debate to win | None — optimizing for correct verdicts |
  | Practical value | Academic only | Directly improves ml-lab for real use |
  | Token confound | Unresolved | Intervention A is compute-neutral (one extra cheap call) |
  | Sycophancy | Accepted as limitation | Directly attacked (Intervention C) |
  | Novel? | Replicates v7 with harder cases | Nobody has shown how to get LLM review systems to exonerate |


  The defense-case problem is harder, more practical, and more novel than the debate-vs-ensemble question. And if you solve it — if you get the system to
  confidently say "this methodology is sound, don't waste time on experiments" — that's the kind of thing practitioners would actually use.
--------
That's the cleanest framing yet. Strip away the paper, the debate-vs-ensemble question, the GAN complexity. You have:

  - A system (ml-lab) with agent prompts
  - A benchmark (280 cases with ground truth)
  - A scoring pipeline (IDR, IDP, FVC, FC, cross-vendor scorer)
  - A known weakness (the defender is bad)

  That's a test suite and code under test. The v8 question isn't an experiment — it's TDD for prompt engineering.

  ★ Insight ─────────────────────────────────────
  The v2-v7 experiments compared architectures (ensemble vs. debate) on a fixed set of prompts. The next iteration should fix the architecture and compare
   prompts — specifically defender prompts — against the fixed benchmark. Same infrastructure, different independent variable.
  ─────────────────────────────────────────────────

  The framework: prompt iteration as software engineering

  1. Define test suite (cases with expected verdicts)
  2. Run current prompts → baseline scores
  3. Diagnose: WHERE does the defender fail? (not just that it fails)
  4. Hypothesize: what prompt change would fix that failure mode?
  5. Modify defender prompt
  6. Rerun on test suite → compare
  7. Accept if metrics improve without regressions
  8. Repeat

  Each iteration is a commit. The journal tracks what changed and why. The benchmark is the regression test. You never ship a defender prompt that hasn't
  been scored.

  What you need that you don't have yet

  1. A diagnostic layer — not just scores, but failure analysis.

  Current scoring tells you FC = 0.775 for multiround. It doesn't tell you why the defender failed on specific cases. You need:

  - Per-case failure classification: on each defense case, what did the defender actually do? Categories: full concession, partial concession, weak
  rebuttal that got overridden, strong rebuttal that got ignored by adjudicator, no rebuttal attempted
  - Failure attribution: was the problem the defender (bad argument), the adjudicator (ignored a good argument), or the critic (raised something
  unfalsifiable)?
  - Specific examples: pull the 5 worst defense-case failures, read the transcripts, understand the mechanism

  This is the equivalent of reading stack traces, not just checking exit codes.

  2. A fast feedback loop.

  Running 280 cases × 4 conditions × 3 runs = 3,360 evaluations for every prompt tweak is too slow and too expensive. You need a canary set — a small,
  representative subset that predicts full-benchmark performance.

  Something like:
  - 10 defense cases (the ones where the current defender fails most egregiously)
  - 10 regular cases (regression check — don't break detection)
  - 10 mixed cases (regression check — don't break ambiguity recognition)

  30 cases × 1 condition × 3 runs = 90 evaluations per iteration. Cheap enough to iterate multiple times per session. Run the full benchmark only when the
   canary set shows meaningful improvement.

  3. A prompt changelog.

  Not just "defender v2, defender v3" — a structured record of:

  Version: defender-v3
  Change: Added explicit anti-concession instruction
  Hypothesis: Partial concession is the primary failure mode;
              explicit instruction will reduce it
  Canary result: DER 0/30 → 4/30
  Full benchmark: [pending]
  Journal entry: [id]

  The journal system already supports this. Each prompt iteration gets a experiment entry with verdict/metric/linked_hypothesis.

  The iteration targets — in order

  Target 1: Can the defender produce a full rebuttal at all?

  Before optimizing, verify the basic capability exists. Take one defense case where the methodology is clearly sound. Hand-craft the perfect defender
  prompt for that one case. Does the model produce a strong rebuttal? Does the adjudicator accept it?

  If yes → the model CAN do this, the prompt is the bottleneck. Iterate on prompts.
  If no → the model fundamentally can't rebut a critique from the same model family. Prompt iteration won't help. You need cross-model defense (different
  model family as defender) or a different architecture.

  This is the existence proof. Don't build an iteration framework until you know the capability exists.

  Target 2: Diagnose the current defender's failure modes.

  Pull the v7 multiround transcripts for defense cases. Read them. Classify each failure:

| Failure mode | What it looks like | Prompt fix |
|---|---|---|
| Full concession | "The critic raises valid points..." | Anti-concession instruction |
| Partial concession | "While the critic is partially correct..." | Require point-by-point rebuttal |
| Weak rebuttal | Defender argues but doesn't address the specific claim | Require quoting the critique |
| Correct rebuttal, ignored | Defender makes a strong argument, adjudicator sides with critic anyway | Adjudicator prompt fix, not defender |
| Unfalsifiable critique | Critic raises something that can't be rebutted ("could have selection bias") | Critic prompt fix: require testable claims |

  The distribution across these categories tells you which prompt to fix first. If 80% of failures are full concession, you fix the defender. If 80% are
  "correct rebuttal ignored," you fix the adjudicator. Don't guess — read the transcripts.

  Target 3: Iterate on the highest-impact prompt.

  One prompt change at a time. Measure on the canary set. Accept or reject. Track in journal. Repeat.

  The discipline: one variable per iteration. Don't change the defender prompt and the adjudicator prompt and the scoring rubric simultaneously. You won't
   know what helped.

  What this gives you

  After N iterations, you have:

  - A defender prompt that actually defends (DER > 0 on defense cases)
  - A prompt changelog showing what worked and what didn't
  - A canary set validated against the full benchmark
  - Empirical evidence about why the current system fails — not just that it does

  And the v2-v7 benchmark isn't being used to prove debate beats ensemble. It's being used as what it actually is: a test suite for the ml-lab system.

-------------

I know that we have a suite of benchmark cases, already. But I wonder if we could improve that. Selected models for case generation, critic/defender
roles, and scoring will always be a criticized design decision. So let’s remove it. Well select a series of capable but cost efficient models and
randomly select on for each task/stage. No more designed bias.

--------
★ Insight ─────────────────────────────────────
  This is actually a statistical design choice masquerading as a bias-removal choice. Converting model selection from a fixed effect to a random effect is
   a principled experimental design move — it means findings generalize across the model distribution, not just "for model X."
  ─────────────────────────────────────────────────

  The core reframe: you're not removing the design decision, you're moving it one level up. Instead of "we chose Claude Sonnet for the critic," you're
  saying "we drew from a pool of capable models." That's still a designed pool — but it's a much more defensible one.

  What this actually buys you:

  If results hold across random model draws, your claims are stronger. "Debate beats ensemble" on a fixed model pair is a weak claim. "Debate beats
  ensemble across a random sample from the Sonnet-class model distribution" is a claim about an effect, not an artifact.

  The within-run diversity constraint is the interesting variant:

  Don't just randomize per stage — require critic and defender to draw from different models within a single run. Same-model debate is just one model
  arguing with itself. That's not adversarial structure, that's a coin flip. Forcing cross-model debate breaks the sycophancy loop more fundamentally than
   any prompt fix.

  This also connects directly to the v8 problem: if critic and defender are the same model family, the defender knows exactly how the critic thinks.
  Cross-model randomization makes the defense genuinely adversarial.

  The tensions worth sitting with:

  1. Pool definition is still a judgment call — which models are "capable but cost-efficient" is a design decision. You've moved the bias, not eliminated
  it. The pool needs a principled definition: probably Sonnet-class only, with some minimum benchmark score.
  2. Capability variance adds noise — some pool members will be systematically weaker. Results may vary more across runs, not because the protocol is
  inconsistent but because you drew a weaker model. You'd need enough runs to average this out, which raises costs.
  3. Scoring independence matters most — the place where model randomization gives the biggest lift is the scorer. If you always score with gpt-4o-mini,
  your results are "as judged by gpt-4o-mini." Random scoring draws mean the verdict isn't tied to one scorer's idiosyncrasies.
  4. Budget unpredictability — if you draw from a pool with different pricing tiers, costs become non-deterministic. Needs a cost ceiling per draw or a
  pool restricted to a narrow price band.

  The benchmark generation angle:

  Random model generation for cases means the benchmark isn't shaped by one model's blind spots or favorite critique styles. Cases generated by Claude
  will cluster differently than cases generated by GPT-4o-mini or Gemini Flash. A randomly-drawn case library is inherently more diverse — this is the
  closest thing to actually removing a design bias.

  Practical sketch:

  Pool (Sonnet-class, ~$1-3/M tokens):
    - claude-sonnet-4-6
    - gpt-4o-mini
    - gemini-1.5-flash
    - mistral-medium (or equivalent)

  Per run: draw without replacement → critic gets model A, defender gets model B, scorer gets model C
  Log model assignments → enables post-hoc sensitivity analysis

  The sensitivity analysis is the hidden value: after 3 runs per case, you can ask "did verdicts vary by model assignment?" If yes, your results are
  model-dependent. If no, you have strong evidence the effect is real.

------------
how many total cases would we need? to cover all the variety?

⏺ This is really a question about how many sources of variance you need to average across. Let me break down the dimensions:

  Pool of model assignments (if pool = 4 models):

  With 4 models drawing 3 without replacement (critic, defender, scorer): 4 × 3 × 2 = 24 possible ordered assignments. To see each assignment at least
  once you need ~75 total runs (birthday problem — naive 24 understates it badly). With 3 runs per case, that means a minimum of ~25 cases just to cover
  model combination space.

  Case variety (flaw taxonomy):

  From the v7 taxonomy — 9 regular flaw types + 6 ambiguity types + sound methodology (defense) = 16 distinct case categories. To get a reliable
  detection/exoneration estimate per category you need at least 10 cases per cell (5 is fragile — one outlier swings your rate by 20%).

  16 categories × 10 cases = 160 cases minimum

  But model randomization adds a wrinkle: with 3 random draws per case, your 160 cases × 3 runs = 480 evaluations — each using a different model combo.
  That's probably enough for the model variance to average out statistically.

  The honest ceiling:

  ┌───────────────────────────────────────────────┬───────────────┐
  │            What you want to cover             │ Minimum cases │
  ├───────────────────────────────────────────────┼───────────────┤
  │ Model combo space (4-model pool, 3 draws)     │ ~25           │
  ├───────────────────────────────────────────────┼───────────────┤
  │ Flaw taxonomy (16 types, 5 cases each)        │ 80            │
  ├───────────────────────────────────────────────┼───────────────┤
  │ Flaw taxonomy (16 types, 10 cases each)       │ 160           │
  ├───────────────────────────────────────────────┼───────────────┤
  │ Adequate defense case coverage (DER estimate) │ 30-40         │
  └───────────────────────────────────────────────┴───────────────┘

  The binding constraint is flaw coverage, not model coverage. 160 cases × 3 runs = 480 evaluations. Compare to v7's 3,360 (280 cases × 4 conditions × 3
  runs) — you'd cut evaluation count by ~85% by collapsing conditions and letting model randomization handle variance.

  The pool size problem:

  4 models gives you limited random effect diversity. The birthday math gets worse: 4-choose-3 ordered = 24 combinations, which is thin. 6-8 models in the
   pool is a much better target — roughly doubles the combination space (6 × 5 × 4 = 120 ordered triples), and you'd need far fewer cases per model combo
  to get coverage.

  Rough answer:

  ~150-200 cases, drawn from all 16 categories, run 3 times each with random model draws from a pool of 6-8 models. That's ~450-600 total evaluations —
  small enough to iterate fast, large enough that neither case-level nor model-level variance dominates the estimate.
  
  ------
