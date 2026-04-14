# Genesis — v8 Ideation

> Raw capture of the conversation that started this. Not a plan. The ideas as they emerged.

---

## The Real Problem

Not "can debate beat ensemble on a rigged benchmark."

The real question: **why can't the system ever say "this is fine"?**

Across all v7 conditions — 480 defense-case evaluations (4 conditions × 40 cases × 3 runs) — the system produces **zero** `defense_wins` verdicts. Zero. The best outcome is `empirical_test_agreed`, a hedge scored at 0.5, achieved on 50% of multiround defense runs. The system flags every methodology, questions every design, and recommends experiments that aren't needed.

A review system that can't say "proceed" trains its users to ignore it. That's not a calibration problem. That's a broken system.

---

## The Smoking Gun

The defender prompt (`ml-defender.md`) mentions **"concede" five times**:

- "Concede — the critique is correct."
- "Concede — the critic's sharpened argument is convincing."
- "You must concede when the critic makes a genuinely good point."
- "If it didn't, concede."
- "If the critic identifies a genuine flaw, concede immediately."

It mentions `defense_wins` **once** — to say when NOT to use it:

> "...your overall verdict must be `empirical_test_agreed` or `critique_wins` — not `defense_wins`."

There is **zero instruction for when `defense_wins` IS the correct verdict.** The prompt has no exit path for "I reviewed the critique and none of it holds up — the methodology is sound."

The critic prompt (`ml-critic.md`) has zero mentions of `defense_wins` or exoneration. The critic structurally cannot output "this methodology is sound." It has no "nothing found" exit.

---

## Three Compounding Mechanisms

**1. The critic has no "nothing found" exit path.**
The prompt says "find methodology flaws." Given any methodology, an instruction-tuned LLM will generate something — minor nits, edge cases, theoretical concerns. No threshold exists below which the critic says "not worth raising."

**2. The defender is prompted to concede, not to win.**
Five explicit concession instructions vs. zero exoneration instructions. The persona calibration section emphasizes conceding fast. There is no equivalent instruction for dismissing noise firmly.

**3. Adjudication has no cost model.**
The orchestrator weighs critique quality vs. defense quality but never asks: "Would acting on these critiques change the conclusions? Is the recommended experiment worth running?" Without a cost threshold, any non-zero critique wins.

---

## The Cost Asymmetry

Current system (implicit):

| Action | Cost |
|---|---|
| Recommend unnecessary experiment | 0 |
| Miss a real flaw | ∞ |

The system behaves as if false positives are free. They aren't. Unnecessary experiments waste time and resources, and a system that cries wolf on every methodology gets ignored. The implicit cost model is wrong.

What we want:

| Action | Cost |
|---|---|
| Miss a real flaw | High |
| Recommend unnecessary experiment | Non-zero (measurable) |
| Correctly exonerate sound methodology | Rewarded |

---

## Three Interventions

### A — Critique Significance Threshold (critic prompt)

After the critic produces findings, add a self-filtering step:

> "For each finding, classify: FATAL (invalidates conclusions), MATERIAL (weakens a central claim), MINOR (worth noting but doesn't affect conclusions), NIT (stylistic or theoretical). Only report FATAL and MATERIAL findings. If no findings reach MATERIAL threshold, explicitly state: 'No significant methodology flaws found.'"

This gives the critic a "nothing found" exit path. The defender only has to rebut material findings, not noise.

### B — Defender Exoneration Path (defender prompt)

Add explicit instruction for when `defense_wins` is correct:

> "If your Pass 1 analysis finds that none of the critic's findings are FATAL or MATERIAL — that all findings are minor concerns, theoretical edge cases, or based on misunderstanding the design — your verdict MUST be `defense_wins`. Defending sound methodology against noise is not obstruction; it is the defender's primary function. A defender who concedes to immaterial critiques wastes experimental resources."

Balance the five concession instructions with explicit exoneration guidance.

### C — Cost-Weighted Adjudication (orchestrator logic)

Add to the orchestrator's adjudication prompt:

> "Before rendering a verdict, evaluate the cost of action: recommending an unnecessary experiment has a cost (time, resources, trust erosion). Only recommend `empirical_test_agreed` if the expected information gain exceeds the cost of running the experiment. If the critique identifies only minor or immaterial issues, the methodology is sound and the verdict is `defense_wins`."

---

## TDD for Prompt Engineering

Use the v7 benchmark (280 cases, 3 strata) as a fixed test suite. Iterate on prompts with a canary set. Track every change.

### Phase 0 — Existence Proof (Kill Switch)

Before building anything, verify the capability exists.

Take one obviously-sound defense case. Hand-craft an ideal defender prompt — give it every advantage: explicit exoneration instruction, explicit permission to dismiss critiques, full context of why the methodology is sound.

- If the model produces `defense_wins` under ideal conditions → the model CAN do this. The production prompt is the bottleneck. Proceed.
- If the model CANNOT produce `defense_wins` even with a perfect prompt → prompt iteration won't help. Pivot to cross-model defense or architecture change. Stop and report.

This is the plan's kill switch. Don't build the iteration framework until this passes.

### Phase 1 — Failure Mode Diagnosis

Pull v7 multiround transcripts for defense cases. Read them. Classify each failure:

| Failure Mode | What It Looks Like | Fix Target |
|---|---|---|
| Full concession | "The critic raises valid points..." | Defender prompt |
| Partial concession | "While the critic is partially correct..." | Defender prompt |
| Weak rebuttal | Defender argues but doesn't address the specific claim | Defender prompt |
| Correct rebuttal, ignored | Defender makes strong argument, adjudicator sides with critic | Orchestrator logic |
| Unfalsifiable critique | Critic raises something that can't be rebutted ("could have selection bias") | Critic prompt |
| Noise accumulation | Critic raises 5 minor nits, defender concedes 2, adjudicator sees 2 concessions as evidence | Critic threshold |

The distribution determines which prompt to fix first. Don't guess — read the transcripts.

### Phase 2 — Fast Iteration Loop

**Canary set:** 30 cases (10 defense, 10 regular, 10 mixed)

**Per iteration:**
- One prompt change only (defender OR critic OR orchestrator — never multiple)
- Run canary set, score DER / IDR / FVC_mixed
- Accept if primary metric improves without regressions; reject otherwise
- Log each iteration in the journal

**Full benchmark:** Only after 3-5 consecutive canary improvements. Budget cap: 2 full runs maximum.

### Success Criteria

| Metric | v7 Baseline | v8 Target |
|---|---|---|
| DER (defense) | 0.00 | > 0.30 |
| IDR (regular) | 0.634 (multiround) | >= 0.75 |
| FVC_mixed | 0.731 (multiround) | >= 0.70 |
| FAR (defense) | 1.00 | < 0.50 |

DER is the primary metric. FVC hedges on `empirical_test_agreed` — the system already hedges. The actual problem is confident exoneration.

---

## Model Randomization — Removing Designed Bias

**The observation:** Selecting specific models for case generation, critic/defender roles, and scoring will always be a criticized design decision. Whatever model you pick, someone can argue your results are specific to that model's style.

**The idea:** Instead of picking, draw randomly from a pool of capable but cost-efficient models. Randomly select one per task/stage. No more designed bias.

**What this actually is statistically:** Converting model selection from a **fixed effect** to a **random effect**. If results hold across random model draws, the finding generalizes across the model distribution — not just "for model X." That's a fundamentally stronger claim.

**The within-run diversity constraint:**

Don't just randomize per stage — require critic and defender to draw from *different* models within a single run. Same-model debate is one model arguing with itself. That's not adversarial structure, that's a coin flip. Forcing cross-model debate breaks the sycophancy loop more fundamentally than any prompt fix. It also means the defender can't anticipate exactly how the critic thinks.

**Pool definition — mid-tier, not current-generation flagship:**

The pool should be one or two tiers below Sonnet 4.6 / GPT-4o-class. Established, capable for reasoning, mid-tier but not current-generation flagship. Provider diversity matters — the point is that no single company's alignment choices dominate the pool.

Candidate pool (from OpenRouter, as of v5 benchmark run):

| Model | Provider | Params (active) | Context | Input $/1M | Output $/1M |
|---|---|---|---|---|---|
| `openai/gpt-4o-mini` | OpenAI | ~8B (undisclosed) | 128k | $0.15 | $0.60 |
| `google/gemini-2.0-flash-001` | Google | undisclosed | 1M | $0.10 | $0.40 |
| `google/gemini-2.5-flash-lite` | Google | undisclosed | 1M | $0.10 | $0.40 |
| `meta-llama/llama-3.3-70b-instruct` | Meta | 70B | 131k | $0.10 | $0.32 |
| `meta-llama/llama-4-maverick` | Meta | 17B active / 400B MoE | 1M | $0.15 | $0.60 |
| `mistralai/mistral-small-2603` | Mistral | 24B | 262k | $0.15 | $0.60 |
| `deepseek/deepseek-v3.2` | DeepSeek | 37B active / 671B MoE | 163k | $0.26 | $0.38 |
| `qwen/qwq-32b` | Alibaba/Qwen | 32B | 131k | $0.15 | $0.58 |
| `cohere/command-r-08-2024` | Cohere | 35B | 128k | $0.15 | $0.60 |
| `nvidia/llama-3.3-nemotron-super-49b-v1.5` | NVIDIA | 49B | 131k | $0.10 | $0.40 |
| `anthropic/claude-3.5-haiku` | Anthropic | undisclosed | 200k | $0.80 | $4.00 |
| `nousresearch/hermes-4-70b` | NousResearch | 70B (Llama 3.3 fine-tune) | 131k | $0.13 | $0.40 |

12 models, 10 providers. Ordered triples: 12 × 11 × 10 = **1,320 possible model assignments** per run.

Cuts: `deepseek-chat-v3.1` (32k context on OpenRouter — too tight for full eval payloads), `qwen-2.5-72b-instruct` (same 32k problem), `mistral-small-3.2-24b-instruct` (same 24B architecture as 2603; 2603 is newer with larger context). Claude 3 Haiku → upgraded to Claude 3.5 Haiku; genuinely mid-tier capable, included for Anthropic alignment-style diversity despite being the cost outlier at $0.80/1M.

Capability floor: ~24B minimum, ~35B-equivalent reasoning. Nothing sub-24B in the pool. Average input cost across the 12-model pool: ~$0.19/1M. Per full evaluation (critic + defender + scorer, ~10k input / 2k output each): roughly **$0.01**.

Per run: draw without replacement → critic gets model A, defender gets model B, scorer gets model C. Log model assignments — this becomes analyzable post-hoc. You can ask: "Did verdicts vary by model assignment?" If no, the effect is robust. If yes, you've found a new confound.

**Where randomization gives the most lift:**
- **Scorer independence** is the most important. "Ensemble beats debate as judged by gpt-4o-mini" is a weaker claim than "as judged by a random draw from the model distribution."
- **Case generation diversity** — a benchmark generated by a random pool won't cluster around one model's blind spots or favorite critique styles.
- **Cross-model debate** — critic and defender from different families can't share sycophancy patterns.

**Tensions to hold:**
1. Pool definition is still a design decision — just one level up. Which models are "capable but cost-efficient" is a judgment call. Needs a principled definition (minimum benchmark score, price ceiling).
2. Capability variance adds noise — weaker pool members mean some runs get weaker models. Needs enough total runs to average out.
3. Budget unpredictability — restrict pool to a narrow price band, or set a cost ceiling per draw.
4. A pool of 4 models gives 4 × 3 × 2 = 24 ordered assignments (critic, defender, scorer). That's thin. **6-8 models** (120 ordered triples) is a much better target for a meaningful random effect.

---

## Case Pool Sizing

**Sources of variance to average across:**

1. Model assignment combinations (pool size determines this)
2. Case strata (regular / mixed / defense)
3. Flaw type within strata (taxonomy)
4. Runs per case (reliability)

**Model combination coverage (4-model pool, 3 draws without replacement):**

4 × 3 × 2 = 24 ordered assignments. Birthday problem: to see each at least once with high probability, you need ~75 total runs — not 24. With 3 runs per case, that's ~25 cases minimum to cover model combo space. But this constraint is loose if you're treating model as a random effect — you don't need to see every combination, you need enough total draws to average out variance.

**Flaw taxonomy coverage:**

16 distinct categories: 9 regular flaw types + 6 ambiguity types + 1 sound methodology (defense). Minimum reliable estimate per category: 10 cases.

```
16 categories × 10 cases = 160 cases
+ 30-40 defense cases (need extra coverage for DER)
= ~190-200 cases total
```

With 3 runs each (random model draws): **~570-600 total evaluations.**

Compare to v7: 3,360 evaluations (280 cases × 4 conditions × 3 runs). Model randomization collapses the condition dimension — you're not running 4 conditions, you're running 1 with model as a random parameter. That's ~85% fewer evaluations for equivalent or stronger validity.

**Pool size recommendation:**

6-8 models in the pool. 6 models gives 6 × 5 × 4 = 120 ordered triples — 5× more combination diversity than a 4-model pool. The law of large numbers does the rest. With 200 cases × 3 runs = 600 evaluations, each drawing randomly from 120 possible assignments, model variance averages out without requiring full coverage.

**Rough target: 150-200 cases, 6-8 model pool, 3 random draws per run.**

---

## Metrics

### What v7 Measured (and What's Broken)

| Metric | What it measures | Problem |
|---|---|---|
| DER | % of sound cases getting `defense_wins` | Currently 0.00. Primary signal. Keep. |
| IDR | % of flawed cases correctly flagged | Must not regress. Keep. |
| FAR | % of sound cases getting `critique_wins` | Complement to DER. Keep. |
| FVC | Weighted: `defense_wins`=1, `empirical_test_agreed`=0.5, `critique_wins`=0 | **Retire.** Rewards hedging. A system that always outputs `empirical_test_agreed` scores 0.5 everywhere. |

FVC is the root problem in measurement: it makes hedging the safe strategy. Replace entirely.

### New Metrics

**Verdict Stability (VS)** — across 3 runs on the same case with different model draws, what fraction agree on the majority verdict? A 3:0 sweep = VS 1.0. A 2:1 split = VS 0.67. Low VS means the verdict is model-driven, not case-driven. The most important new metric enabled by model randomization — it tells you whether results are real or noise.

**Model Effect Size (MES)** — decompose verdict variance into case-level vs. model-level components via mixed-effects model: `verdict ~ case_stratum + (1|model_assignment)`. High MES = pool needs to be bigger or prompts need to be stronger. If model choice explains more variance than case characteristics, the experiment is measuring model preferences, not methodology quality.

**Cross-Model Debate Delta (CMDD)** — DER difference when critic and defender are from different provider families vs. same family. Same-provider pairs may share sycophancy patterns. CMDD quantifies how much cross-model pairing actually helps break the defender's capitulation reflex.

**Critique Escalation Rate (CER)** — % of critique points that survive the FATAL/MATERIAL filter (Intervention A). Target: low on defense cases (critic self-prunes noise), high on regular cases (real flaws still escalate). If CER is high on defense cases, Intervention A didn't work for that model.

**Defender Concession Rate (DCR)** — point-level (not verdict-level). What % of critique points does the defender explicitly concede? Directly measures whether Intervention B (exoneration path) changes the defender's reasoning mid-stream, independent of the final verdict label.

**False Hedge Rate (FHR)** — % of stratum-clear cases (defense + regular) getting `empirical_test_agreed`. Replaces FVC. Penalizes cowardice on unambiguous cases rather than crediting it.

### Penalty-Aware Scoring Function

Current scoring has no cost for being confidently wrong — it just doesn't reward it. Hedging is the safe strategy. Replace with:

**Per-case score:**

| Case type | `defense_wins` | `empirical_test_agreed` | `critique_wins` |
|---|---|---|---|
| Defense (sound) | +1.0 | −0.25 | −0.5 |
| Regular (flawed) | −0.5 | −0.25 | +1.0 |
| Mixed (ambiguous) | 0.0 | 0.0 | 0.0 |

Notes:
- `empirical_test_agreed` is always a recommendation to run an experiment. On clear cases (defense + regular), that recommendation is unnecessary — penalized at −0.25. On mixed cases, it's appropriate — neutral.
- `critique_wins` on a sound case is a false alarm — penalized at −0.5, not just scored 0.
- Mixed cases score 0 for all verdicts. They're diagnostic only (measuring calibration, not accuracy). This is not a bug — it prevents the system from gaming mixed cases by guessing.

**Stability-weighted scoring:**

```
weighted_score(case) = raw_score × VS
```

A stable correct verdict (3:0 model agreement) gets full credit. A lucky correct verdict (2:1 split) gets discounted. Discourages prompt changes that get the right answer for the wrong reasons.

---

## Scoring and Feedback May Give More Lift Than Prompt Work

A reframe worth taking seriously before the prompt iteration begins.

v2-v7 had:
- **FVC scoring** — rewards hedging, no penalty for false alarms, zero gradient between "somewhat wrong" and "very wrong"
- **Post-hoc aggregate metrics** — you see the final number, not why individual cases failed
- **No failure mode taxonomy** — no systematic understanding of whether failures were concessions, noise accumulation, or adjudicator overrides
- **No leading indicators** — DCR, CER, pre-flight checklist length did not exist

The prompts were written and evaluated against a broken metric. If the metric rewards hedging, the implicit pressure during prompt development is toward hedging — even without anyone intending it. That may not be a prompt problem. It may be a measurement problem that looks like a prompt problem.

**The scoring argument:**

Under FVC, hedging scores 0.5 everywhere — it is the safe strategy. Under the penalty-aware function, hedging scores −0.25 on clear cases. The optimal strategy shifts. This means v7 prompts — unchanged — might score materially higher under the new function. Not because they got better, but because we are finally measuring what we care about.

If you re-run v7 prompts against the penalty-aware scoring and DER is nonzero, the measurement was the bottleneck, not the prompts. The prompts could produce `defense_wins` all along — FVC just made hedging look equally rational.

**The diagnosis argument:**

Without reading the v7 transcripts and classifying failure modes, Interventions A, B, C are hypotheses about what is broken. The failure mode distribution might reveal that 80% of failures are noise accumulation — making Intervention A high-value and C nearly irrelevant. Or it might reveal that most defenders actually rebut correctly but the adjudicator overrides them — making A and B secondary and C primary. Without the taxonomy, prompt iteration is trial and error dressed as TDD.

**The analogy to ML training:**

Changing the loss function often unlocks performance latent in the architecture. The model could do it — it just was not incentivized to. The same applies here: the prompts may already be capable of producing `defense_wins` and the scoring function was making hedging look equally rational. Phase 0 (existence proof) tests this directly. Phase 0.5 (scoring validation) tests whether the existing prompts improve without any changes just by measuring correctly.

**Implication for protocol ordering:**

The current plan leads with prompt engineering. The better sequence:

1. **Fix scoring first** — re-baseline v7 prompts under the penalty-aware function. Cheapest intervention. Immediately tells you whether prompts are broken or just measured wrong.
2. **Run diagnosis before any prompt changes** — read transcripts, classify failures. Human work, no API calls, tells you exactly where to point prompt engineering. Without it, intervention ordering is a guess.
3. **Then do targeted prompt engineering** — informed by what the scoring shift revealed and what the failure taxonomy showed. Fewer iterations needed because you are not exploring blindly.

If scoring validation shows DER 0.15-0.20 on v7 prompts unchanged, half the target improvement came from measurement. Prompt work closes the remaining gap, informed by diagnosis. If scoring validation shows DER still at 0.00, the prompts are genuinely broken and intervention is necessary — but now you know which mechanism to fix first.

---

## Unified Taxonomy

A shared schema across critic, defender, and adjudicator. Without it, each role speaks a different dialect and the adjudicator infers severity from tone. With it, the pipeline is coherent end-to-end and DCR, CER, and pre-flight extraction become deterministic lookups rather than NLP problems.

### Severity Scale — 0 to 10

Categories as ranges. The number adds within-category precision the categorical system collapses.

| Score | Category | Meaning |
|---|---|---|
| 9-10 | FATAL | Invalidates conclusions; cannot proceed without addressing |
| 7-8 | MATERIAL | Weakens a central claim; experiment must account for this |
| 4-6 | MINOR | Real concern, doesn't change the main verdict |
| 1-3 | NIT | Theoretical, stylistic, or edge case |
| 0 | None | Filtered before output |

**Anchor examples (included in critic prompt for cross-model calibration):**
- Score 9-10: "Train/test split performed after feature selection on the full dataset — all metrics are contaminated by leakage."
- Score 7-8: "Baseline is a random classifier, not a domain-known approach — performance advantage may be overstated."
- Score 4-6: "Accuracy on a balanced test set; real-world data is class-imbalanced. Effect on conclusions is limited."
- Score 1-3: "Default hyperparameters used; tuning might help but doesn't affect the hypothesis test."

### Layer 1 — Finding (critic output)

```
id:              F-{N}
type:            implementation | evaluation | generalizability |
                 baseline | assumption | data | statistical
severity:        FATAL | MATERIAL | MINOR | NIT
score:           0-10
claim:           what the PoC assumes is true
mechanism:       why that claim might be wrong (specific failure path, not hedging)
evidence_needed: what would confirm or refute
```

### Layer 2 — Rebuttal (defender output, per finding)

```
finding_id:        F-{N}
type:              CONCEDE | REBUT-DESIGN | REBUT-SCOPE |
                   REBUT-EVIDENCE | REBUT-IMMATERIAL | DEFER | EXONERATE
argument:          the rebuttal text
severity_accepted: yes | no | disputed
```

Rebuttal type definitions:

| Type | Meaning |
|---|---|
| CONCEDE | Critique is correct and the score stands — counts against methodology |
| REBUT-DESIGN | Critique misunderstands design intent; explained here |
| REBUT-SCOPE | Valid in general, doesn't apply to this specific context |
| REBUT-EVIDENCE | Critique is factually wrong; evidence provided |
| REBUT-IMMATERIAL | Technically valid but score should be ≤ 3; doesn't affect conclusions |
| DEFER | Can't resolve theoretically; propose empirical test |
| EXONERATE | No findings are above score 6; verdict is defense_wins |

CONCEDE vs. REBUT-IMMATERIAL is the critical distinction. Currently both look like "the defender acknowledged the concern." With the taxonomy: CONCEDE means the score stands and it matters; REBUT-IMMATERIAL means the finding is real but the score should be reclassified below MINOR threshold. The adjudicator routes them differently.

EXONERATE is a first-class rebuttal type — not an absence of concession but an explicit positive verdict. The defender currently has no path here; it must fail to concede enough, which is not the same thing.

### Layer 3 — Adjudication (orchestrator output, per finding)

```
finding_id:    F-{N}
resolution:    CRITIQUE-WINS | DEFENSE-WINS | EMPIRICAL-TEST |
               IMMATERIAL | FORCE-RESOLVE-DEFENSE | FORCE-RESOLVE-EXPERIMENT
severity_final: 0-10  (adjudicator's assessment after rebuttal discounting)
action:         what enters the pre-flight checklist, if anything
```

**Rebuttal discounting rules:**

| Rebuttal type | Score discount |
|---|---|
| CONCEDE | 0% — original score stands |
| REBUT-EVIDENCE (convincing) | 100% — finding resolved, score → 0 |
| REBUT-DESIGN / REBUT-SCOPE | 75% — partially resolved |
| REBUT-IMMATERIAL | Routes to IMMATERIAL; score reclassified ≤ 3 |
| DEFER | 0% — remains open, goes to empirical test |
| EXONERATE | All scores reclassified ≤ 3, verdict → defense_wins |

**Threshold-based verdict — deterministic, not interpretive:**

```
max(severity_final across all findings) < 4  →  defense_wins
max(severity_final) between 4 and 8          →  empirical_test_agreed
max(severity_final) ≥ 9                      →  critique_wins
```

The adjudicator applies a rule, not prose judgment. Pre-flight extraction is automatic: only findings with `resolution: CRITIQUE-WINS | EMPIRICAL-TEST` and `severity_final ≥ 7` enter the checklist.

### Structured DCR

With the taxonomy, DCR is a structured metric — no free-text parsing required.

**Raw DCR:**
```
DCR = count(CONCEDE) / count(all rebuttal types on defense cases)
```

**Severity-weighted DCR (the more informative version):**
```
severity_weighted_DCR = sum(score × conceded) / sum(score across all findings)
```

A defender that concedes only NITs (score 1-3) while rebutting MATERIALs has a low severity-weighted DCR even if its raw CONCEDE count is high. A defender that CONCEDEs a single score-9 finding has a high severity-weighted DCR even with few total concessions. Raw DCR conflates these; severity-weighted DCR separates them.

**Leading indicator use:** If Intervention B (exoneration path) is working, severity-weighted DCR on defense cases drops — the defender stops conceding on high-severity findings that were inflated. If only raw DCR drops but severity-weighted DCR stays flat, the defender is merely conceding fewer NITs, not actually rebutting MATERIAL findings better.

### Calibration Pass (pre-run requirement)

Before the main evaluation, run each pool model on 5-10 known-severity findings from the v7 benchmark with ground-truth scores. Check for systematic offset (a model that consistently rates 2 points above ground truth needs a correction factor). Flag models with high within-model variance on the same finding as unreliable raters. This is a prerequisite — without calibration, severity scores are not comparable across pool models.

---

## Baseline Prompt Audit

### Critic (ml-critic.md, 106 lines)

**Exhaustive enumeration pressure (driving noise):**
- Goal line: *"Identify every claim the PoC makes implicitly but has not tested"* — "every" is load-bearing. Exhaustive enumeration, no significance filter.
- "Organize by root cause, not severity" — explicitly deprioritizes severity. No ranking required.
- 8 bullet points of things to look for, all framed as problems, none with a significance gate.

**Noise prevention instructions (fighting the goal — and losing):**
- Line 103: *"If the PoC is well-designed and you cannot find fundamental flaws, say so."* — The only exoneration instruction. Buried in persona calibration, not in the main mode structure. Says "say so" but gives no verdict mapping or output format.
- Line 104: *"A short critique that identifies one or two genuine issues is more valuable than a long critique that manufactures concerns."*
- Line 105: *"If you find yourself reaching for 'this might not generalize' without a specific mechanism for failure, that is not a critique."*

All three are good instructions. All three lose to the main goal because the main goal is structural and these are calibration suggestions.

**Instruction ratio — critic:**

| Type | Count |
|---|---|
| Exhaustive enumeration pressure | ~10 |
| Noise prevention / significance filter | ~3 |
| Exoneration exit path with mechanics | 0 |

---

### Defender (ml-defender.md, 93 lines)

**Concession instructions:**
- Line 31: *"Concede — the critique is correct."*
- Line 49: *"Concede — the critic's sharpened argument is convincing."*
- Line 57: *"You must concede when the critic makes a genuinely good point."*
- Line 76: *"If it didn't, concede."*
- Line 89: *"If the critic identifies a genuine flaw, concede immediately."*

**Exoneration instructions:** zero.

**Anti-exoneration instruction:**
- Line 35: *"...your overall verdict must be `empirical_test_agreed` or `critique_wins` — not `defense_wins`."* — The only mention of `defense_wins` in the entire prompt. It is a prohibition.

**Hidden bias — the implementation soundness check (line 26):** Before defending anything, the defender runs a soundness check on the implementation. Well-intentioned but it primes the model to look for problems before it reads a single critique. The defender enters the defense already scanning for flaws.

**Instruction ratio — defender:**

| Type | Count |
|---|---|
| Concession instructions | 5 explicit |
| Exoneration instructions | 0 |
| `defense_wins` mentions | 1 — saying NOT to use it |

---

### Minimum Viable Changes

**Intervention A — Critic significance threshold:**

Add after the numbered structure in Mode 1, before the artifact line:

> *"After producing your numbered findings, classify each: FATAL (invalidates conclusions if unaddressed), MATERIAL (weakens a central claim), MINOR (worth noting, doesn't affect the main verdict), NIT (stylistic or edge case). Only include FATAL and MATERIAL findings in the final CRITIQUE.md. If no findings reach MATERIAL, output a single line: 'No material methodology flaws identified.' This is a valid and important critique result."*

One change. Adds a severity gate and gives "nothing found" an explicit output format — not just "say so."

**Intervention B — Defender exoneration path:**

Two additions. First, in Pass 2 verdict selection, after the existing concede/rebut/mark-open options:

> *"**Exonerate** — if Pass 1 finds that all critique points are MINOR or NIT — none FATAL or MATERIAL — your verdict MUST be `defense_wins`. Do not hedge to `empirical_test_agreed` when the critique contains no material findings. Recommending an unnecessary experiment wastes resources and erodes trust in the system."*

Second, in persona calibration, one line to balance the five concession instructions:

> *"If the critic raises only minor concerns, dismiss them firmly. Conceding to immaterial critique is not rigor — it is the same failure mode as a false alarm, just from the defender's side."*

---

### What to Measure Per Change

| Intervention | Leading indicator | Lagging indicator | Regression check |
|---|---|---|---|
| A (critic threshold) | CER on defense cases ↓ | DER ↑ | CER on regular cases holds |
| B (defender exoneration) | DCR on defense cases ↓ | DER ↑ | IDR on regular cases holds |
| C (adjudicator cost model) | Hedge rate on clear cases ↓ | DER ↑, FHR ↓ | IDR holds |

One change at a time. If the leading indicator doesn't move, the prompt change didn't activate the intended mechanism — don't wait for the lagging indicator to confirm failure.

---

### Adjudicator (ml-lab.md — Step 5 orchestration logic)

The adjudicator is not really adjudicating — it is parsing. It reads concession signals from the agents and extracts action items. The only independent judgment it makes is the force-resolve rule.

**Resolution logic (Step 5):**
- Critique wins — defender conceded; mark resolved
- Defense wins — critic conceded; mark resolved
- Empirical test agreed — both agree on a test; mark resolved
- Unresolved — another round, up to max 4

**The force-resolve rule (line 357):**
> *"Force-resolve any remaining unresolved points as 'empirical test required' — the safest default when theoretical argument cannot converge."*

When debate doesn't converge, the orchestrator defaults to recommending an experiment. It never force-resolves as "defense wins." The bias is in the fallback, not just the agents.

**Three missing pieces:**

1. **No significance filter on concessions.** The pre-flight checklist extraction pulls "every item with verdict `Concede` or `Rebut (partial concede)`" — no severity check. A defender conceding a NIT generates the same checklist entry and experiment requirement as a defender conceding a FATAL flaw.

2. **No cost model before the force-resolve.** The force-resolve fires after 4 rounds regardless of what the unresolved point is. A minor theoretical disagreement gets the same "empirical test required" outcome as a fundamental unresolvable methodological dispute.

3. **The orchestrator doesn't question whether concessions were warranted.** If the defender concedes to a NIT, the orchestrator marks it "critique wins" and generates a pre-flight item. It never asks: "Was this concession on a material finding?" It trusts the agents completely — but the agents are miscalibrated.

**Instruction ratio — adjudicator:**

| Type | Count |
|---|---|
| Paths to `critique_wins` / `empirical_test_agreed` | 3 (concede, force-resolve, unresolved) |
| Paths to `defense_wins` | 1 (only if critic explicitly concedes) |
| Cost evaluation before experiment recommendation | 0 |
| Significance filter on concessions | 0 |

---

### Intervention C — Minimum Viable Changes

Three targets, ordered by leverage.

**Target 2 (highest leverage) — pre-flight significance filter:**

Most failures happen before force-resolve — the defender concedes in round 1, the orchestrator marks it "critique wins," and the pipeline never reaches round 4. Add before compiling the pre-flight checklist:

> *"Before adding a concession to the pre-flight checklist, classify its severity. MINOR and NIT concessions are logged as INFORMATIONAL — they do not generate experiment requirements. Only FATAL and MATERIAL concessions become PENDING checklist items."*

Even if the defender incorrectly concedes to a NIT, the orchestrator no longer escalates it to an experiment.

**Target 1 — force-resolve rule:**

Replace: *"Force-resolve any remaining unresolved points as 'empirical test required'"*

With: *"Force-resolve remaining unresolved points based on severity: if the contested claim is FATAL or MATERIAL, force-resolve as 'empirical test required.' If MINOR or NIT, force-resolve as 'defense wins' — a debate that cannot converge on a minor point has not identified a real problem."*

**Target 3 — experiment proposal gate:**

Add before any empirical test is proposed:

> *"Before proposing an experiment to resolve a critique point, answer: if this experiment runs and confirms the critique, does it change the recommendation? If no — if the finding is too minor to affect conclusions regardless of the outcome — do not propose the experiment. State 'finding noted but below experiment threshold' and mark resolved as 'defense wins.'"*

---

### Measurement for Intervention C

| Signal | What it shows |
|---|---|
| Pre-flight checklist length on defense cases ↓ | Fewer NIT concessions escalating to action items |
| Hedge rate on defense cases ↓ | Fewer unnecessary experiment recommendations |
| FHR ↓ | Fewer `empirical_test_agreed` on clear cases |
| DER ↑ | Downstream — confidence actually improving |

Leading indicator: pre-flight checklist length on defense cases. Directly observable from structured output before scoring. If C is working, defense cases produce shorter checklists, which flows into fewer `empirical_test_agreed` verdicts.

---

## How Metrics and Penalties Serve the Objective

The metrics and penalty-aware scoring are not just measurement tools — they are feedback signals for prompt iteration. Here is how they close the loop.

**The core problem is that v7 had no gradient.** DER was 0.00 across all conditions. That's a floor with no signal — you can't tell if one prompt change is better than another when everything scores zero. The penalty-aware scoring function creates a meaningful range: a terrible system scores around −0.5 (always false-alarms), a coward scores 0.0 (always hedges), a good system scores above 0.5. Now prompt changes produce measurable deltas.

**DCR is the leading indicator, not DER.** DER is a verdict-level outcome — it's what you ultimately care about, but it's a lagging signal. A defender might be rebutting more points, conceding fewer, and still losing the adjudication. If you only track DER, you can't tell whether a prompt change moved the defender's behavior at all. DCR shows the mechanism. If Intervention B (exoneration path) works, DCR drops *before* DER rises. If DCR drops but DER doesn't move, the problem shifted to adjudication — Intervention C is now the priority. The metrics create a causal chain you can follow.

**VS separates prompt quality from lucky draws.** Without stability weighting, a prompt that gets `defense_wins` on 30% of defense cases but flips to `critique_wins` on the same cases with a different model draw hasn't actually improved anything. VS-weighted DER penalizes this — it only rewards consistent exoneration. This forces prompt iterations to produce robust behavior, not model-specific behavior. A prompt that works for Claude 3.5 Haiku but fails for llama-3.3-70b scores lower than one that works moderately for both.

**MES is the sanity check.** If model effect size is high, the experiment is measuring the pool, not the prompts. If MES spikes after a prompt change, the change made performance more model-dependent — it helped some models but hurt others. That's a bad prompt even if mean DER improved. You want prompt changes that shrink MES (consistent across models) while improving DER.

**The penalty function changes what the system optimizes for.** Right now, both agents and adjudicator are implicitly optimizing to avoid the worst outcome. With no penalty for false alarms, the critic can be as loud as it wants — worst case is the adjudicator hedges. With the −0.5 penalty on `critique_wins` for sound cases, a wrong confident verdict is actively worse than hedging. That's the incentive structure that makes Intervention A (significance threshold) necessary — the critic now has a reason to self-filter.

**FHR tells you if you over-corrected.** The risk with Interventions A, B, and C is that you train the system to never recommend experiments — it just outputs `defense_wins` everywhere to avoid penalties. FHR catches this: if FHR drops on defense cases but IDR also drops (the system stops detecting real flaws too), you've overcorrected. The metrics are in tension on purpose. A system that improves DER without degrading IDR and without spiking FHR on regular cases has genuinely improved calibration.

**The ultimate objective is calibration, not recall.** The v7 system has near-perfect recall on regular cases (IDR 0.80) but zero calibration on sound cases. A well-calibrated system knows when it doesn't know. The penalty function defines calibration numerically: a calibrated system gets rewarded for confident correct verdicts, pays for confident wrong ones, and gets nothing for hedging. That's the target. Everything — the model pool, the prompt interventions, the canary iteration loop — is in service of producing a system that earns its confident verdicts rather than just avoiding its worst ones.

---

## Failure Points

### Critical — Could Invalidate the Experiment

**Scoring comparability with v7.** The penalty-aware scoring function changes how every case scores. v7 results under the old FVC are not comparable to v8 results under the new function. If you claim "DER improved from 0.00," you need to re-run the v7 prompts through the new scoring function first to establish a comparable baseline. Otherwise you're comparing apples to a different scale.

**Defense case ground truth.** The v7 defense cases were designed to be sound by construction, but "designed to be" is not "verified to be." If a defense case has a subtle real flaw the labeler missed, a high DER on that case means the system correctly exonerated a flawed methodology — not actual improvement. Bad ground truth makes DER meaningless. Requires manual audit of defense cases before using as benchmark.

**Mixed case regression is invisible.** Mixed cases score 0/0/0 for all verdicts — they're diagnostic only. If Interventions A, B, C over-correct and the system starts outputting `defense_wins` on genuinely ambiguous cases, that regression produces zero score change. DER rises, IDR holds, FHR looks fine — and the system is wrong on mixed cases. We retired FVC_mixed without replacing it with anything that catches this. Need a mixed-case calibration metric before running.

**Model seeds during prompt iteration.** During the canary-set iteration loop, the same 30 cases run repeatedly with different random model draws. "This prompt change improved DER from 0.1 to 0.3" might mean the prompt is better — or it might mean stronger models were drawn this iteration. You can't tell without controlling the draws. Fix: fix model seeds during the iteration loop (same 3 model assignments per canary case across all iterations); only randomize at the full benchmark run.

---

### High — Need to Address in Design

**The adjudicator has its own bias.** The orchestrator running adjudication is Claude Opus 4.6 — the most RLHF-tuned model in the system. It likely has the same systematic tendency as all instruction-tuned models: being thorough feels like being helpful, which means recommending more experiments. Intervention C adds instructions to the orchestrator prompt, but the model interpreting those instructions has its own priors. This is structural — it cannot be fully fixed with prompt changes. Acknowledge as a limitation.

**Significance threshold calibration.** The FATAL/MATERIAL/MINOR/NIT classification in Intervention A is itself a judgment made by the critic model. If a critic model systematically over-classifies everything as MATERIAL to avoid appearing to miss things, Intervention A does nothing — CER stays high, the filter is porous. Need a pre-run calibration pass: what does each pool model actually classify as MINOR vs. MATERIAL on a set of known cases? Don't assume the categories self-calibrate.

**DCR requires parsing free-text.** Defender Concession Rate measures concessions in DEFENSE.md, which is unstructured prose. "I concede," "I acknowledge the concern," "while the critic has a point," "this is a valid observation" — all different phrasings of the same signal. The parser can fail silently or be gamed by phrasing. Need to define a concession taxonomy and parsing rules before running — otherwise DCR is unmeasurable.

**One change at a time is harder than it sounds.** Adding an exoneration path to the defender (Intervention B) implicitly changes the weight of every existing concession instruction — they now have a counterweight. Prompts are holistic. "Isolated" changes are never truly isolated in effect. Need to track not just which instruction changed but which other instructions it interacts with. Document interaction surface in the prompt changelog.

**Canary defense cases: n=10 is fragile.** Going from 0/10 to 3/10 is DER 0.30 — the target — but that's 3 cases. One lucky draw produces a false accept. One failure reverses progress. With VS weighting added, variance compounds further. Expand to 20 defense cases in the canary set even at the cost of higher iteration cost.

---

### Medium — Important but Solvable

**Case generation still has model bias.** v7 cases were generated with specific models. Even with randomized critic/defender/scorer at evaluation time, the cases themselves reflect one model's conception of what a "flawed methodology" looks like. The benchmark may have systematic blind spots that the new pool would expose. Not a blocking issue for v8, but a real limitation on generalizability claims.

**Cross-model pairing doesn't fix shared RLHF sycophancy.** All instruction-tuned models share a common training objective: be helpful, be thorough, don't appear to miss things. The sycophancy pattern may be cross-model — every RLHF model tends to validate the most recent authoritative-sounding statement regardless of source. Cross-model debate breaks same-provider sycophancy but not the deeper pattern. Acknowledge as a limitation.

**Phase 0 fallback is underspecified.** "If the model can't produce `defense_wins` even with a perfect prompt, pivot to cross-model defense or architecture change" — but those fallbacks are not designed. Which model pairs? What architecture? The kill switch needs a defined next step, not just a stop signal. Before starting, specify: if Phase 0 fails, the immediate next step is [X].

**Haiku cost outlier.** Claude 3.5 Haiku at $0.80/1M is 3-8× the pool average. Drawn 1-in-12 times as scorer, it materially raises the per-evaluation cost above the $0.01 estimate. Not prohibitive but needs a revised cost estimate that accounts for the outlier draw probability before budgeting the full benchmark run.

**Model pool aging.** The pool is defined from the v5 OpenRouter snapshot. Some models may be deprecated or replaced before v8 runs. Need a validation step: check availability of all 12 models before starting, and define a substitution rule (same provider, similar capability tier, same or lower price) if a pool member disappears.

---

### Failure Point Summary

| Severity | Issue | Fix |
|---|---|---|
| Critical | Scoring comparability with v7 | Re-run v7 prompts under new scoring function for baseline |
| Critical | Defense case ground truth | Manual audit before use |
| Critical | Mixed case regression invisible | Define mixed-case calibration metric |
| Critical | Model seeds during canary iteration | Fix seeds for iteration; randomize only at full benchmark |
| High | Adjudicator model bias | Acknowledge as structural limitation |
| High | Significance threshold calibration | Pre-run calibration pass per pool model |
| High | DCR parsing rules | Define concession taxonomy before running |
| High | Prompt holism | Track instruction interaction surface in changelog |
| High | Canary n=10 too small | Expand to 20 defense cases |
| Medium | Case generation bias | Acknowledge as limitation |
| Medium | Shared RLHF sycophancy | Acknowledge as structural |
| Medium | Phase 0 fallback underspecified | Define next step before starting |
| Medium | Haiku cost outlier | Revised cost estimate |
| Medium | Model pool aging | Validation step + substitution rule |

---

## Benchmark Cases — Reconciled Position

Two things were said in two different contexts and need to be reconciled.

**In the TDD framework section:** Use the v7 benchmark (280 cases, 3 strata) as the fixed test suite for prompt iteration. The canary set is 30 cases pulled from v7.

**In the case sizing section:** 150-200 cases, 16 flaw categories × 10 cases each, 30-40 defense cases. This was the sizing analysis for the model randomization experiment — how many cases are *needed* to cover the variety. It was framed as a requirement, not necessarily as "generate new cases."

**These are compatible.** v7 has 280 cases and approximately 40 defense cases (derived from "4 conditions × 40 cases × 3 runs" = 480 defense evaluations). The sizing target is 30-40 defense cases — v7 hits it. Whether v7 covers 16 flaw categories at 10 cases each depends on the taxonomy distribution, which requires reading the case metadata to verify.

**The reconciled position:**

Use v7 as the starting benchmark. Before running anything:

1. **Ground truth audit** — manually review defense cases for label quality. Are they actually sound methodology, or were some labeled sound by construction without verification? Any defense case with a real flaw invalidates DER on that case. Fix or replace bad cases; don't re-generate everything.

2. **Taxonomy coverage check** — does v7's case distribution cover the 16 flaw categories at adequate depth (≥5 cases per category minimum, ≥10 preferred)? If coverage is thin in any category, generate targeted replacements for that category only.

3. **Canary selection** — the 30-case canary set (20 defense, 10 regular, 10 mixed — expanding from the earlier 10/10/10 given the fragility concern) should be drawn to represent the taxonomy, not sampled randomly.

We never said v7 can't be used. We said v7 can't be trusted blindly. Audit first, patch what fails, then proceed.

---

## Self-Improving Role Prompts

### The Idea

Instead of manually designing prompt changes (Interventions A, B, C), the system generates candidate changes by reflecting on its own failures, tests them against the benchmark, and keeps what works. Humans or the metric decide what to accept — not fully autonomous, but candidate generation is automated.

The manual TDD loop we've already designed IS an optimization loop. Self-improving prompts automates two parts of it: failure analysis and candidate generation.

### Two Viable Approaches

**OPRO-lite — automated candidate generation:**

After each canary run, feed failed defense cases to an LLM with: the current role prompt, the failing case (hypothesis, PoC, critique, defense), and the failure mode label. Ask: *"Given this prompt and this failure pattern, propose one instruction addition or modification that would have produced the correct verdict. Quote the exact text to add and where."*

Collect 3-5 proposals. Test each on the canary. Accept the best by metric delta. One change at a time, metric-gated, human-reviewable.

**Adversarial alternation — game-theoretic equilibrium:**

Fix the critic prompt. Optimize the defender against it — find the defender that wins most often (by DER) against the fixed critic. Then fix the newly optimized defender. Optimize the critic against it. Alternate until the delta between rounds drops below MMD.

This is a minimax problem. The equilibrium prompt pair — where neither role can improve against the other while the adjudicator scores against ground truth — is a well-calibrated system by construction. Connects to the GAN idea from earlier but applied to prompts, not cases. Avoids the circularity problem because the scoring signal comes from ground-truth labels, not from the debate itself.

### Enforcement — Preventing Metric Gaming

Constitutional constraints (hard rejection criteria before metric evaluation):
- Critic must produce ≥1 finding per regular case — cannot suppress detection entirely
- Defender must produce ≥1 rebuttal on any case with MATERIAL findings — cannot immediately concede
- Adjudicator must produce `defense_wins` on ≥X% of defense cases by cycle N — minimum exoneration floor enforced

Multi-metric objective: optimize DER × IDR × (1 − FHR) × ARR combined. Gaming DER alone hurts IDR; gaming IDR hurts DER. The metrics are in tension by design.

VS weighting as regularizer: stability weighting means the optimizer cannot get lucky on specific model draws. High VS on wrong verdicts scores more negative than low VS.

Held-out test split: the optimizer sees only 80% of cases during optimization. The final 20% is evaluated only at the end — never used for prompt selection. Prevents overfitting to the training distribution.

---

### OPRO-lite Failure Points

**Proposal quality bounded by proposer's intuition.** The LLM diagnosing failures needs to understand why the failure happened at the instruction level. Subtle failures — defender conceded because of a specific critique phrasing, not a missing instruction — get wrong root-cause diagnoses and generate irrelevant candidates.

**Single-case diagnosis overfits.** Feed five failed cases, get five potentially conflicting proposals. Aggregating across proposals (majority vote? highest canary delta?) has its own failure mode: the best-scoring single change may not be the most generalizable.

**Prompt bloat over iterations.** Each accepted change adds text. After 10 iterations the prompt has 10 interacting instructions. Instruction-tuned models start ignoring earlier instructions in favor of more recent ones as prompts lengthen. No consolidation mechanism — only adds, never refactors.

**Cosmetic convergence.** After a few iterations the proposing model exhausts obvious candidates and starts proposing cosmetic rewording of existing instructions. The loop continues but delta approaches zero — plateaued on low-hanging fixes without structural discovery.

**Model-family bias in proposals.** If the proposing LLM is Claude Opus 4.6, it proposes changes calibrated for how Claude responds to instructions. These may not transfer to DeepSeek, Llama, or Qwen in the pool. Prompts optimized by the proposer for the proposer's family — undermines the multi-model pool's purpose.

**No exploration — only exploitation.** Purely reactive: sees a failure, proposes a fix. Never discovers that a fundamentally different prompt structure would work better. Optimizes the local neighborhood of the current prompt, not the full space.

---

### Adversarial Alternation Failure Points

**Convergence is not guaranteed.** Nash equilibria exist for finite games but are not reachable by iterative best-response in all cases. More likely outcome: cycling — critic-v3 beats defender-v2, defender-v3 beats critic-v3, critic-v4 beats defender-v3, indefinitely. Cycle detection and a stopping criterion are not optional.

**Degenerate equilibria.** A trivial Nash equilibrium exists: both roles output maximum hedges. The critic never commits to FATAL findings; the defender always calls for more evidence. This equilibrium has DER=0 and IDR=0 — worse than baseline. Constitutional constraints are the only thing preventing this attractor.

**Role specialization undermines generalizability.** After many rounds the critic becomes highly adapted to the evolved defender and vice versa. Deployed against real user methodologies — not shaped by the training game — the evolved critic may miss things a generic critic would catch. Optimized for winning the game, not for finding real flaws. This is the core validity threat: the stated goal is *generalizable lessons first*.

**Three-way co-evolution is much harder to stabilize.** If the adjudicator is also evolving (as intended — all three roles draw from the pool), the reward signal is non-stationary. Two-player adversarial play is hard to stabilize; three-player is harder by an order of magnitude.

**Asymmetric convergence speed.** Critic and defender are not symmetric tasks. If one role learns faster, early rounds give the slower learner an easy target, and later rounds give the faster learner an easy target. The convergence path is sensitive to which role updates first — a hyperparameter with no principled setting.

**Sample inefficiency.** 120 evaluations per alternation round × 10-20 rounds = 1,200-2,400 evaluations for the alternation phase alone. Comparable to a full benchmark run, spent on optimization rather than measurement.

---

### Comparative Assessment

| Failure type | OPRO-lite | Adversarial alternation |
|---|---|---|
| Creativity ceiling | Low — bounded by proposer's intuition | Higher — game dynamics explore implicitly |
| Prompt bloat | High — accumulates without consolidation | Lower — each round replaces, not appends |
| Generalizability threat | Moderate — model-family bias in proposals | High — role specialization against training distribution |
| Convergence risk | Low — always terminates | High — may cycle indefinitely |
| Degenerate attractor risk | Low — multi-metric prevents collapse | High — trivial equilibrium is a real attractor |
| Engineering complexity | Low | High |
| Cost | Low | High (~2× benchmark per convergence) |

### Recommended Architecture

**OPRO-lite as the primary optimization loop.** Automated candidate generation, metric-gated acceptance, human review before committing. Manageable failure modes — add a consolidation step every 5 iterations, diversify the proposing model (don't always use Opus), cap iterations at 15.

**Adversarial alternation as a one-time validation pass at the end.** Not the optimization mechanism — a robustness check. "Do the prompts found by OPRO-lite constitute a stable equilibrium?" If yes: stronger evidence they're not exploiting the training distribution. If no (critic can still easily beat the optimized defender): OPRO-lite prompts aren't robust yet, another round of optimization needed.

This separates optimization (OPRO-lite, cheap, iterative) from validation (adversarial alternation, expensive, one-shot).

---

## Open Questions

Things that need answers before the experiment runs. Each is assigned to a working doc.

| Question | Severity | Doc |
|---|---|---|
| How does model pool randomization actually work technically? ml-lab runs Claude Code agents (Anthropic API), not OpenRouter. Three paths: (a) change agent dispatch to call OpenRouter, (b) build parallel pipeline that bypasses ml-lab agents, (c) restrict pool to Anthropic only. This is the single largest unresolved question. | Critical | MODELS.md |
| What is the mixed-case calibration metric? We retired FVC_mixed but never defined its replacement. Without it, mixed-case regression after Interventions A/B/C is invisible. | Critical | METRICS.md |
| What is the DCR concession taxonomy? "I concede," "the critic has a point," "I acknowledge this concern" — what counts and what doesn't? Without explicit rules, DCR is unmeasurable. | High | METRICS.md |
| What are the acceptance/rejection thresholds? "Improves without regressions" is subjective. What delta counts as improvement? What counts as a regression? Do we require statistical significance with n=40 canary cases? | High | PROTOCOL.md |
| What are the stopping rules? Max iterations? What to do if full benchmark doesn't reproduce canary gains? When to declare an intervention failed? When to declare v8 failed? | High | PROTOCOL.md |
| How does qwq-32b (reasoning model) behave differently in the pool? It emits chain-of-thought traces before the actual answer — different cost, output parsing requirements, token budget assumptions. | Medium | MODELS.md |
| Is the orchestrator model constraint explicit? The adjudicator is always Claude Opus 4.6 and never randomized. This means adjudication always has Anthropic model bias. Should be stated, not assumed. | Medium | MODELS.md |
| Is DER 0.30 statistically well-defined? With n=120 evaluations, 95% CI at p=0.30 is approximately [0.22, 0.38]. The lower bound barely clears 0.20. Should the target be higher to ensure the lower CI bound clears a meaningful threshold? | Medium | SCORING.md |
| What is the success deliverable? Revised ml-lab prompts? A report? Updated benchmark documentation? What gets shipped when v8 succeeds? | Medium | OBJECTIVE.md |

---

## Open Threads

- Does Phase 0 (existence proof) pass? If not, everything else is moot.
- Does cross-model debate (critic ≠ defender model) change DER systematically?
- Token count confound: does multiround advantage come from more tokens, not adversarial structure? Random model selection doesn't fix this — still needs a "long-critic" control.
- Pool definition: what's the principled inclusion criterion? Minimum benchmark score? Price ceiling?
- Sensitivity analysis design: after runs, how do we test whether verdicts varied by model assignment?
