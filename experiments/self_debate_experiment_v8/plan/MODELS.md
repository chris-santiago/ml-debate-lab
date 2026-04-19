# Model Pool

## The 12-Model Pool

Target: mid-tier capable models, one or two generations below current flagship (Sonnet 4.6 / GPT-4o class). Price band: $0.08–$0.80/1M input. Provider diversity is the point — no single company's alignment choices should dominate.

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

10 providers. Capability floor: ~24B minimum. Ordered triples: 12 × 11 × 10 = 1,320 possible model assignments per run.

Average input cost across pool: ~$0.19/1M. Estimated cost per full evaluation (critic + defender + scorer at ~10k input / 2k output each): **~$0.01** (excluding Haiku draws — see cost outlier below).

---

## Technical Architecture — Decision: Path B ✓

**Confirmed.** Build a standalone Python evaluation pipeline that calls OpenRouter directly via the OpenAI SDK, bypassing ml-lab agents entirely. All three roles — critic, defender, and adjudicator — draw from the 12-model pool. The ml-lab plugin is not modified for this experiment.

**Why Path B:**
- ml-lab plugin is a production artifact; modifying dispatch for an experiment introduces unacceptable risk
- Standalone pipeline is fully reproducible and independently testable
- Generalizable lessons first: tune the pipeline until the debate protocol works broadly, then port winning prompts back to ml-lab agents
- All three roles drawing from the pool (including adjudicator) removes the Anthropic-model bias that would exist if adjudication were locked to Opus 4.6

**What the pipeline replicates in code:**
- Critic call: pool model receives `HYPOTHESIS.md` + `POC.md`, outputs structured CRITIQUE.md with taxonomy fields
- Defender call: pool model receives CRITIQUE.md + case context, outputs structured DEFENSE.md with rebuttal labels
- Adjudicator call: pool model receives CRITIQUE.md + DEFENSE.md, assigns point verdicts and case verdict
- Scorer: evaluates case verdict against ground truth label, computes all metrics per evaluation

**What it does NOT replicate:**
- Multi-round debate (Step 5 in ml-lab) — v8 runs single-round critic → defender → adjudicator. Multi-round is a separate experiment dimension.
- INVESTIGATION_LOG.jsonl tooling — logging handled by pipeline's own results JSON

**Alternatives considered (rejected):**
- Path A (OpenRouter dispatch layer inside ml-lab): modifies the plugin under test — confounds the experiment
- Path C (Anthropic-only pool): eliminates provider diversity — defeats the purpose of randomization

---

## Seed Control

**During prompt iteration (canary loop):** Fix model seeds. Assign the same 3 model draws to each canary case across all iterations. This ensures that a DER improvement between iteration N and N+1 reflects the prompt change, not different model draws.

**At full benchmark run:** Fully randomize. Each of the 3 runs per case draws independently from the pool without replacement. No fixed assignments.

**Seed assignment format:**
```json
{
  "case_id": "def_042",
  "run_1": {"critic": "meta-llama/llama-3.3-70b-instruct", "defender": "openai/gpt-4o-mini", "scorer": "deepseek/deepseek-v3.2"},
  "run_2": {"critic": "mistralai/mistral-small-2603", "defender": "google/gemini-2.0-flash-001", "scorer": "cohere/command-r-08-2024"},
  "run_3": {"critic": "anthropic/claude-3.5-haiku", "defender": "qwen/qwq-32b", "scorer": "nousresearch/hermes-4-70b"}
}
```

Seed file is generated once before the canary loop begins and held constant.

---

## qwq-32b — Reasoning Model Quirks

`qwen/qwq-32b` is a chain-of-thought reasoning model. It emits extended thinking traces before its final answer. In the critic or defender role this creates three problems:

1. **Cost.** Reasoning traces can be 5,000–10,000 tokens before the actual output. At $0.15/1M input and $0.58/1M output, a long reasoning trace is 3–5× more expensive than a non-reasoning model at the same context length. The $0.01/evaluation estimate does not hold when qwq-32b is drawn.

2. **Output parsing.** CRITIQUE.md or DEFENSE.md content appears after the reasoning trace. The parser must strip the trace and extract only the final output. Define the parsing boundary before running.

3. **Behavior difference.** qwq-32b's critique style will be more structured and explicit than non-reasoning models — it will enumerate reasoning steps before conclusions. This may produce longer, more detailed critiques regardless of flaw significance. Monitor CER when qwq-32b is the critic; it may systematically inflate CER.

**Mitigation options:** (a) remove qwq-32b from the pool and use `qwen/qwen-2.5-72b-instruct` instead (no reasoning overhead, but 32k context limit on OpenRouter), (b) keep it and handle parsing explicitly, (c) restrict qwq-32b to the scorer role only (less sensitive to reasoning traces). Decision needed.

---

## Adjudicator Model Assignment

Under Path B, the adjudicator is no longer locked to Claude Opus 4.6. It draws from the same 12-model pool as critic and defender, subject to the "no replacement" constraint (all three roles in a given run draw distinct models).

**Implication:** The Anthropic-RLHF bias in adjudication — previously unavoidable — is now diluted across 12 models. The adjudicator's prior toward "thorough = helpful = recommend experiments" is a per-model effect, not a structural constant. MES will capture how much adjudicator model identity drives the final verdict.

**Monitoring note:** Track adjudicator-model-specific DER. If one provider's models consistently produce `empirical_test_agreed` as adjudicator regardless of debate outcome, that's a model-level alignment artifact worth reporting separately.

**Caveat for v8 prompt work:** Intervention C (adjudicator cost-weighted logic) is now evaluated across 12 different models following the same prompt. Prompt changes that work for Opus 4.6 may not activate on smaller models. Monitor per-model compliance with the threshold rule — if compliance is bimodal (works on ≥70B, fails on ≤35B), that's a finding about model capability requirements, not a prompt failure.

---

## Cost Estimate with Haiku Outlier

Claude 3.5 Haiku at $0.80/1M input is the pool outlier — 3–8× the pool average. Drawn 1-in-12 times for each role, expected share of evaluations: ~8.3%.

**Revised cost estimate per evaluation:**
- Non-Haiku draw (11/12 chance): ~$0.008 per evaluation
- Haiku draw (1/12 chance for each role): adds ~$0.05 per evaluation when Haiku is the scorer; less when critic or defender (shorter outputs)
- Expected cost per evaluation: ~$0.015 (roughly 1.5× the naive estimate)

At 600 evaluations: ~$9 for model API calls. Still negligible. At 3,360 (full v7 scale): ~$50. Well within budget.

---

## Pool Validation and Aging

The pool is defined from the v5 OpenRouter snapshot. Before running:

1. **Validate availability:** Check that all 12 models are currently listed and callable on OpenRouter.
2. **Substitution rule:** If a model is deprecated, substitute with: same provider → similar parameter count → same or lower price → same or longer context. Document the substitution.
3. **Context validation:** Confirm context limits match the table. OpenRouter occasionally changes context limits for the same model ID.
