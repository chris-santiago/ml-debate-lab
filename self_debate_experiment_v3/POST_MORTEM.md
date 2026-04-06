# v3 Experiment Post-Mortem

Issues identified during and after execution of `claude_code_plan_v3_experiment.md`. Each issue is scoped to whether it affected current results (active) or should be fixed in a future run (future).

---

## Issue 1 — INVESTIGATION_LOG coverage is incomplete

**Scope:** Future fix  
**Severity:** Minor — audit quality, not result validity

The plan's logging directive (line 780) covers Phase 6 onward only. It defers to the ml-lab agent's `## Investigation Log` schema rather than embedding it, which means log quality depends on the executor consulting that section. Phases 0–5 (case validation, preregistration, scoring engine build, protocol self-review) and Phases 7–9 (stats, reports, peer review) have no explicit logging directives.

ml-lab's logging section specifies ~60 lines of rules covering all category codes (`gate`, `write`, `read`, `subagent`, `exec`, `decision`, `debate`, `review`, `audit`, `workflow`), entry timing, and per-step logging rhythm. The v3 plan has one paragraph.

**What to fix in v4:** Embed the full logging schema directly in the plan and add explicit logging directives to each phase, not just Phase 6.

---

## Issue 2 — Agents and subagents invoked `python` instead of `uv run`

**Scope:** Future fix  
**Severity:** Moderate — silent failures possible when scripts have PEP 723 inline dependencies

Several agents and subagents called scripts with `python` (or `python3`) directly rather than `uv run`. For scripts that rely only on the standard library this is harmless, but the v3 scripts use PEP 723 inline script metadata (`# /// script` blocks) to declare third-party dependencies. Invoking those scripts with bare `python` silently skips dependency resolution: the script either crashes on import or, worse, resolves against a stale environment that happens to have the package installed.

**Canonical rule:** every script invocation — whether from an agent, a subagent, or a one-liner — must use `uv run <script>`. This applies equally to inline `-c` one-liners: prefer `uv run python -c '...'` over `python3 -c '...'`.

**What to fix in v4:** Add an explicit enforcement note to the experiment plan and to any agent prompt that invokes scripts: "Always invoke Python scripts with `uv run`. Never use `python` or `python3` directly."

---

## Issue 3 — Isolation breaches not logged in INVESTIGATION_LOG

**Scope:** Active — confirmed gap in audit trail for this run  
**Severity:** Moderate — breach detection worked, but the event is absent from the log

`check_isolation.py` detected 2 isolation breaches at scoring time:

- `v3_raw_outputs/real_world_framing_002_isolated_debate_run1.json` — Defender output contained verbatim Critic issue text
- `v3_raw_outputs/real_world_framing_010_isolated_debate_run1.json` — same pattern

The orchestrator surface these in the console and re-ran the affected runs. However, inspection of all 7 batch INVESTIGATION_LOGs confirms neither the breach detection nor the re-run were logged. The batch7 entry for `real_world_framing_002` records normal completion and notes verdict variation as a "labeling" difference — no breach flag. The batch6 summary explicitly records `"isolation_violations": 0`.

This is a direct instance of the Issue 1 gap: because the plan has no explicit logging directive for breach detection or corrective re-runs, the orchestrator handled both silently. From the log alone, there is no record that two runs were contaminated and replaced.

**What to fix in v4:** Add explicit logging directives to the isolation check step: log a `decision` / `isolation_breach_detected` entry for each flagged file (with `meta` capturing the matched string and file path), and log a `workflow` / `rerun_triggered` entry before each corrective re-run and `workflow` / `rerun_complete` after.

---

## Issue 4 — Batch1 logging granularity and schema differ from all other batches

**Scope:** Active — inconsistent audit trail across batches in this run  
**Severity:** Moderate — batch1 data is present but informationally thin and structurally incompatible with other batches

Batch1 (`broken_baseline_*` cases, 7 cases) produced 84 log entries — one per individual run (12 per case). All other batches produced 7–9 entries total — one rich summary per case. Beyond the count difference, the schemas diverge: batch1 entries contain only `timestamp`, `type`, `case_id`, `condition`, `run`, and `note: "completed"`, with no verdict data, must-find coverage, or qualitative notes. Batches 2–7 entries include `verdicts`, `must_find_coverage`, `unanimous_verdict`, and substantive `notes` fields.

Comparison against the `ml-lab` logging spec reveals that **no batch is compliant**. The spec mandates six required fields; all batches deviate on multiple:

| Spec field | Batch1 | Batches 2–7 |
|---|---|---|
| `ts` | present as `timestamp` (wrong key) | present as `timestamp` (wrong key) |
| `step` | absent | absent |
| `seq` | absent | absent |
| `cat` | present as `type`; only `exec` used | absent entirely |
| `action` | absent | present, but no verb_noun convention |
| `detail` | absent | partially — folded into `notes` or `summary` |

The spec's 10-category `cat` taxonomy (`gate`, `write`, `read`, `subagent`, `exec`, `decision`, `debate`, `review`, `audit`, `workflow`) was never used. The monotonic `seq` counter was never maintained. The `step` field — which ties every entry to a phase of the experiment — is absent in all batches. Action-level granularity (one entry per meaningful action, with step boundaries, file I/O, and subagent dispatches each logged separately) was replaced by coarser run-level (batch1) or case-level (batches 2–7) summaries.

Batches 2–7 did add useful non-spec fields — `verdicts`, `must_find_coverage`, `unanimous_verdict` — which the spec would have placed in `meta`. The content is present but under non-standard keys, making uniform parsing unreliable.

The root cause is the same as Issue 1: the v3 plan referenced the ml-lab logging spec by pointer rather than embedding it, so orchestrators wrote something loosely inspired by the spec rather than actually following it.

**Investigation needed before v4:**
- Determine whether batch1's run-level format and batches 2–7's case-level format reflect different orchestrator agents or different prompting strategies within the same agent
- Decide whether the canonical granularity should be action-level (as spec requires), run-level, or case-level — and whether a two-tier format (fine-grained during execution, summary at case completion) is desirable
- Assess whether batch1's thin entries can be post-hoc enriched with verdict data from the raw output files, or whether that signal is simply missing from the log
- Determine whether to fix key names (`timestamp` → `ts`, `type` → `cat`) in the v4 schema or update the spec to match what orchestrators naturally produce

**Proposed fix for v4:** Replace prose-based logging with a dedicated `log_entry.py` script (PEP 723, invoked via `uv run`). The script accepts structured CLI arguments, enforces required fields, validates `cat` against the allowed taxonomy, auto-generates `ts`, and increments `seq` by reading the last line of the log. The orchestrator is explicitly instructed to call it for every loggable action:
```
uv run log_entry.py --step 6 --cat exec --action run_case --case_id foo --detail "ran isolated_debate run 1, verdict: critique_wins"
```
Schema compliance moves out of LLM text generation and into code — the same pattern as `check_isolation.py`. The v4 plan must include an explicit directive: "never write log entries manually; always use `uv run log_entry.py`."

---

## Issue 5 — Orchestrator reads agent source files from `agents/` despite agents being installed

**Scope:** Active — observed during this run  
**Severity:** Minor — functionally harmless, but wastes context and suggests the orchestrator doesn't trust its installed agents

The experiment orchestrator was observed reading agent source files directly from the repo's `agents/` directory (e.g. `agents/ml-critic.md`, `agents/ml-defender.md`) during execution. All agents are already installed in the Claude Code environment at `~/.claude/agents/` and are invoked by name via the Agent tool — the source files in `agents/` are reference copies, not the active definitions.

The cause is unclear. Possible explanations:
- The v3 plan explicitly references `agents/` paths, prompting the orchestrator to read them for context before dispatching
- The orchestrator is verifying agent behavior before dispatch, not trusting the installed version
- The orchestrator conflates "reading the spec to understand what the agent will do" with "dispatching the agent"

This is wasteful (consumes context window) and potentially risky: if the repo copy and the installed copy have diverged, the orchestrator is reading stale or incorrect behavior descriptions.

**Investigation needed before v4:** Audit the v3 plan for any explicit references to `agents/` file paths that might prompt reading behavior. Add a directive clarifying that agents are invoked by name only and their source files must not be read during execution. Determine whether this is plan-driven or spontaneous orchestrator behavior, as the fix differs in each case.

---

## Issue 6 — Several real_world_framing cases marked failed despite issues found and verdict matching ground truth

**Scope:** Active — both patterns are scorer bugs; all ETD scores are invalid and must be re-computed  
**Severity:** Critical — the ETD dimension is entirely unreliable in the current results; any analysis that uses ETD scores or pass/fail outcomes for `empirical_test_agreed` cases must be treated as provisional until re-scored

Several `real_world_framing` cases in `v3_results_eval.json` are marked `pass_fail: fail` despite having all planted issues found, valid resolution, and final verdict matching ground truth. Investigation identified two distinct scorer bugs.

### Pattern A — ETD=0.0 floor failures (rwf_005, rwf_006, rwf_007, rwf_008, rwf_009) — scorer schema mismatch

**This is a scorer bug, not agent failure.**

These five cases each score ETD=0.0 with all other dims at 1.0 (except DRQ=0.5 on rwf_005 and rwf_008). Initial hypothesis was that ETD should be `null` — but inspection of `benchmark_cases_verified.json` confirmed all five have `ideal_debate_resolution.type: empirical_test_agreed`, making ETD fully applicable. Further investigation of the raw output files confirmed that **empirical test designs were produced** across isolated_debate, multiround, and ensemble conditions in all five cases. For example, `real_world_framing_006_isolated_debate_run1.json` contains a fully-specified empirical test with condition, success criterion, and failure criterion.

The root cause is a **schema mismatch** between `compute_etd()` in `self_debate_poc.py` and the actual raw output format. The scorer checks for three keys:

```python
has_m = bool(empirical_test.get('measure'))
has_s = bool(empirical_test.get('success_criterion'))
has_f = bool(empirical_test.get('failure_criterion'))
```

But the raw outputs use a different schema:
```json
{
  "condition": "...",
  "supports_critique_if": "...",
  "supports_defense_if": "...",
  "ambiguous_if": "..."
}
```

None of the scorer's expected keys (`measure`, `success_criterion`, `failure_criterion`) are present in any raw output. Every `empirical_test` block evaluates to `has_m=False, has_s=False, has_f=False` → ETD=0.0, regardless of content quality. The only reason rwf_002 and rwf_010 score ETD=1.0 is a separate anomaly (Pattern B below) — the ETD=1.0 there is also suspect.

**This is a critical finding for experiment analysis.** All ETD scores in `v3_results_eval.json` are invalid. Cases scored ETD=0.0 may have produced high-quality empirical test designs; cases scored ETD=1.0 did not earn that score through `compute_etd()` as written. The entire ETD dimension must be re-scored after aligning the scorer schema with the actual output schema.

**Fix required before v4:** Reconcile the `compute_etd()` key expectations with the output format agents actually produce. Either update the scorer to read `condition`/`supports_critique_if`/`supports_defense_if`/`ambiguous_if`, or update the agent output format to emit `measure`/`success_criterion`/`failure_criterion` — and re-score all cases for ETD from the raw outputs.

### Pattern B — All dims 1.0 but still marked fail (rwf_002, rwf_010)

Both cases score 1.0 on every dimension including ETD, have all planted issues found, valid resolution, verdict matching ground truth, and `failure_attribution: "none"`. By every rubric criterion these should be passing cases. Given the Pattern A finding that `compute_etd()` cannot return 1.0 from the actual output schema, the ETD=1.0 scores on rwf_002 and rwf_010 are themselves anomalous — they may reflect a hardcoded or manually overridden score rather than a valid scorer output.

**This is a scorer bug.** Something in `case_passes()` or upstream result aggregation is marking these cases failed despite no failing dimension. The isolation breach on rwf_002 run1 and rwf_010 run1 (Issue 3) is a candidate cause — if the scorer aggregated pre-rerun results at the case level, it may have carried a stale failure flag that persisted even after the contaminated runs were replaced.

**Fix required before v4:** Audit `case_passes()` logic and result aggregation for rwf_002 and rwf_010. Verify that re-run outputs were correctly written and read by the scorer. Re-score both cases from corrected raw outputs after the ETD schema fix is applied.

### Remediation applied (v3)

**Root cause confirmed:** `compute_etd()` in `self_debate_poc.py` expected keys `measure` / `success_criterion` / `failure_criterion`, but agents naturally produced `condition` / `supports_critique_if` / `supports_defense_if` / `ambiguous_if`. Every output using the agent-native schema scored ETD=0.0 regardless of content quality.

**Fix:** `compute_etd()` updated to detect which schema is present (discriminating key: `measure` vs `condition`) and map both to the same three-component logic: `condition` → measure, `supports_critique_if` → success criterion, `supports_defense_if` → failure criterion. An `isinstance(empirical_test, dict)` guard was also added to handle two string-valued `empirical_test` fields in `defense_wins_009` raw outputs (no score impact — already short-circuited by the `defense_wins` early return).

**Re-scoring results:** All 49 main benchmark cases and 16 external cases re-scored. Only the 8 `real_world_framing` cases were affected — the only cases that produced condition-schema outputs. 5 changed from FAIL to PASS: rwf_002, rwf_006, rwf_007, rwf_009, rwf_010. The remaining 3 still fail for legitimate reasons: rwf_003's isolated debate returned `mixed` (not in acceptable resolutions); rwf_005 and rwf_008's isolated debate returned `critique_wins` without an empirical test, so ETD=0.0 is correct (ideal resolution is `empirical_test_agreed`, making ETD applicable regardless of actual verdict). External results unchanged — no condition-schema files in external outputs.

**Artifacts updated:** `v3_results.json`, `v3_results_eval.json`, `stats_results.json`, `external_stats_summary.json`, `sensitivity_analysis_results.json`, `within_case_variance_results.json`, `difficulty_validation_results.json`. No raw output files were modified — fix was entirely in the scorer.

**Pattern B fully explained:** The ETD=1.0 on run1 for rwf_002 and rwf_010 was not anomalous — it was coincidental. Run1 for both cases was the isolation breach re-run (original run1 contaminated and replaced, Issue 3). The replacement agent happened to emit the old `measure`/`success_criterion`/`failure_criterion` schema, which `compute_etd()` could correctly read → ETD=1.0. Runs 2 and 3 were original batch outputs using the condition-schema → ETD=0.0. Case-level aggregation required ≥2 passes; each case had only 1, so both were marked fail. The post-mortem description of "all dims 1.0" was describing run1 in isolation, not the case aggregate — there was no scorer bug in `case_passes()` itself. After the ETD schema fix, run2 and run3 now score correctly: rwf_002 reaches 2/3 passes (run3 still fails — verdict was `critique_wins` with no empirical test, ETD=0.0 correct); rwf_010 reaches 3/3 passes.

**Commit status — verify before closing:** As of the time this post-mortem was written, the scorer fix (`self_debate_poc.py`) and all re-scored artifacts (`v3_results.json`, `v3_results_eval.json`, `stats_results.json`, `external_stats_summary.json`, `sensitivity_analysis_results.json`, `within_case_variance_results.json`, `difficulty_validation_results.json`) are untracked in git. The remediation is functionally complete but not committed. The orchestrator may have its own commit plan for these files — verify that all remediation artifacts are committed before treating Issue 6 as closed.

**Open items carried forward to v4:**
- `ambiguous_if` is silently dropped in the mapping; a three-outcome test and a two-outcome test score identically — worth addressing in v4 schema design
- The dual-schema detection approach in `compute_etd()` is v3-only technical debt; v4 should standardize on a single canonical output schema so branching logic is not needed

---

## Issue 7 — Raw outputs not committed after Phase 6 completion

**Scope:** Future fix  
**Severity:** Moderate — raw outputs are ground truth for all downstream scoring; untracked files are vulnerable to inadvertent modification

The `v3_raw_outputs/` directory is never committed to git during the experiment run. All downstream scoring, ETD evaluation, bootstrap CIs, and sensitivity analysis read directly from these files. If any file is modified after scoring — whether by a re-run, a tool call, or an accidental overwrite — there is no way to detect the change or recover the original. The isolation breach re-runs in this experiment (Issue 3) are a concrete example: the re-run outputs replaced the contaminated files with no git record of what was overwritten or when.

**What to fix in v4:** Add explicit directives to the experiment plan for two commits:

1. **After Phase 6 (main benchmark):** Once all benchmark cases are complete and `check_isolation.py` passes clean, commit `v3_raw_outputs/` before any scoring begins. Commit message should record isolation check result and benchmark run count.
2. **After Phase 6b (external cases):** Once all external cases are complete and isolation check passes, commit `v3_raw_outputs/` again to snapshot the full dataset including external cases.

Each commit creates a tamper-evident checkpoint that scoring and analysis can be traced back to. The two-commit structure also makes it easy to identify which files belong to the main benchmark vs. the external benchmark by comparing the two snapshots.

---

## Issue 8 — Post-mortem process is entirely manual; consider automation


**Scope:** Future improvement — implement after v3 experiment is fully complete  
**Severity:** Low — process works, but does not scale and requires concurrent human attention during experiment execution

The v3 post-mortem was produced by manually cross-referencing logs, raw outputs, scorer source, benchmark case metadata, and git history in real time alongside the running experiment. Most items required synthesizing evidence across multiple artifacts (e.g. Issue 6 Pattern B required connecting the isolation breach, the re-run's coincidental output schema, run-level aggregation logic, and scorer source). This is high-effort and easy to miss things.

Three automation options to evaluate and implement in combination after the experiment is complete:

**Option 1 — Post-run audit agent**
After all phases complete, spawn a general-purpose agent with the raw outputs, scorer source, results eval JSON, and a checklist of known failure modes (schema mismatches, isolation flags, pass/fail anomalies). The agent produces a structured anomaly report — not a finished post-mortem, but a set of flagged items for human review and promotion. Lower bar than full automation, high signal.

**Option 2 — Inline orchestrator anomaly logging**
The orchestrator already notices unexpected events (isolation breaches, re-runs, non-zero scorer exits). A plan directive to log `decision` / `anomaly_detected` entries whenever something unexpected occurs would make the orchestrator self-documenting during the run. These entries could feed a post-run summarizer. Builds directly on the `log_entry.py` improvement from Issue 4 and is the highest-leverage near-term change.

**Option 3 — Dedicated post-mortem skill**
A skill that knows the experiment structure: reads a post-mortem template, runs structured checks (ETD validity, isolation status, schema consistency, pass/fail vs. ground-truth agreement), and drafts post-mortem items for each anomaly. Human reviews and edits rather than discovers and writes. Highest leverage long-term but requires the most upfront design and should wait until the experiment protocol is stable — a skill built on v3 assumptions would need rework for v4.

**Recommendation:** Options 1 and 2 are complementary and low-risk; implement both for v4. Option 3 is worth building after v4 when the protocol has stabilized. Priority for v4 is Option 2 — getting orchestrators to log anomalies inline is where the diagnostic signal already lives.

---

## Issue 9 — Near-ceiling scores limit interpretability of v3 results

**Scope:** Active — affects interpretation of all v3 findings  
**Severity:** High — the experiment cannot support several claims that the results superficially suggest

Post-fix results show all three debate conditions at 0.975–0.993 and a 93.9% pass rate (46/49). These numbers look strong but have limited interpretive value for four distinct reasons.

**1. The pass rate improvement is partially a scorer artifact.** Five of the six newly-passing cases (post-ETD fix) were failures caused by a scorer bug, not by agents underperforming. Treating 93.9% as evidence of benchmark difficulty would be incorrect — it reflects a correct fix, not a hard benchmark being cleared.

**2. The ETD fix may have introduced rubric leniency.** The corrected `compute_etd()` awards ETD=1.0 if `condition`, `supports_critique_if`, and `supports_defense_if` are present — it checks field presence, not content quality. Any three-field empirical test object clears the bar. The original intent was to assess whether the test was well-specified; the schema fix may have inadvertently lowered that bar, contributing to the ceiling effect.

**3. Conditions are indistinguishable at this score level.** 0.975 vs. 0.986 vs. 0.993 is within noise — the experiment cannot support any claim about whether multiround or ensemble adds value over isolated debate. Differential performance between protocol variants requires cases hard enough to separate the conditions. V3 does not have enough of those.

**4. The fair-comparison lift of +0.053 is the most defensible number.** After controlling for cases where baseline was also tested, debate adds approximately 5 points over baseline. At that margin, the experiment barely supports the claim that debate outperforms baseline at all, let alone that more elaborate debate structures add incremental value.

**5. Difficulty labels do not predict performance.** `difficulty_validation_results.json` shows baseline means of easy=0.698, medium=0.655, hard=0.676 — a 4-point spread with hard cases scoring *higher* than medium. Spearman rho=-0.069, p=0.68: no detectable relationship between difficulty labels and baseline scores. If the labels don't track actual difficulty, any claim that debate adds more value on hard cases than easy ones is built on unreliable ground. This reinforces the ceiling finding: the benchmark's internal structure isn't working, not just the score distribution.

**Implication for v4 case design:** The benchmark needs cases that genuinely stress-test the conditions against each other — ambiguous scenarios where a single-pass critic misses something that a multiround exchange surfaces, or where ensemble synthesis resolves a contested point that isolated debate leaves open. High-difficulty cases with nuanced `empirical_test_agreed` resolutions are the most likely candidates. Difficulty labels should be validated against baseline performance before the experiment runs — if hard cases don't score lower on baseline, the labels need revision. A 93.9% pass rate on a well-designed benchmark should be a warning sign, not a headline result.

---

## Issue 10 — Orchestrator does not commit artifacts at phase boundaries

**Scope:** Future fix  
**Severity:** Moderate — artifacts produced during the experiment are untracked until the orchestrator or user manually commits, creating windows where work can be lost or silently overwritten

Beyond the raw outputs (Issue 7), no other experiment artifacts are committed at phase boundaries. Scripts, results files, analysis outputs, and logs accumulate as untracked files throughout the run. If the experiment is interrupted, re-run, or if a later phase overwrites an earlier output, there is no git record of the intermediate state.

Issue 7 addressed raw outputs specifically because they are ground truth. This issue generalizes the principle: every phase should end with a commit of all artifacts it produced.

**What to fix in v4:** Add an explicit commit directive at the conclusion of each plan phase. Suggested checkpoints:

- **Phase 0–2 (setup, preregistration):** Commit benchmark cases, preregistration JSON, and rubric before any agent runs begin
- **Phase 5 (scoring engine):** Commit scorer scripts (`self_debate_poc.py`, analysis scripts) before Phase 6 begins
- **Phase 6 (raw outputs):** Two commits as specified in Issue 7
- **Phase 7 (scoring and stats):** Commit all results JSON files immediately after scoring completes
- **Phase 8–9 (analysis):** Commit sensitivity, variance, and difficulty validation results
- **Phase 10+ (reporting):** Commit report artifacts as they are produced

Each commit message should identify the phase and note any anomalies flagged during that phase. This gives the experiment a complete, auditable trail and makes it possible to reconstruct the state at any point in the run.

---

## Issue 11 — MiniMax-M2.7 cross-vendor validation yielded 82% parse failures

**Scope:** Active — cross-vendor Phase 10 results are inconclusive for 31/38 cases; `cross_model_scorer.py` corrected for v4 re-run  
**Severity:** Low — the partial results (7 valid cases) are directionally consistent with the main benchmark; the validation goal was to rule out same-company bias, which it partially achieved

Phase 10 ran `cross_model_scorer.py` against MiniMax-M2.7 via the Anthropic SDK compatible endpoint. 31 of 38 cases (82%) failed to parse:

- **25 cases:** `No text block in response; content types: ['ThinkingBlock']` — MiniMax-M2.7 returned only a ThinkingBlock with no accompanying text via the Anthropic SDK endpoint. The scorer's defensive fix (`next(b for b in response.content if hasattr(b, 'text'), None)`) correctly detected this, but had no text to parse.
- **6 cases:** JSON parse errors (`Unterminated string`, `Expecting value`) — malformed or empty JSON in the text response.

**What the 7 valid cases showed:** All 7 returned external_IDR=1.000, matching isolated_debate_IDR=1.000. Delta=0.000, not material. Consistent with the main benchmark finding that IDR=1.0 across all conditions. The same-company bias concern is not supported by the available data, though the sample is too small (7/38) to be conclusive.

**Root cause:** MiniMax-M2.7 via the Anthropic-compatible SDK endpoint unreliably emits text blocks — on most prompts it returns only the ThinkingBlock with no final text response. This is an SDK compatibility issue: the Anthropic SDK maps MiniMax's thinking output to ThinkingBlock objects but the model does not reliably produce a subsequent TextBlock.

**Fix identified (not yet applied to results):** MiniMax's OpenAI-compatible API (`https://api.minimax.io/v1`) resolves this. Without `reasoning_split=True`, the response comes back via `choices[0].message.content` with thinking embedded as `<think>...</think>` tags, which can be stripped cleanly. Probing confirmed all 4 test cases returned valid, parseable JSON. **Phase 10 should be re-run in v4 using this approach.** `cross_model_scorer.py` has not been updated — the corrected pattern is documented here only.

```python
# Correct pattern for MiniMax via OpenAI-compatible API:
import re
from openai import OpenAI

client = OpenAI(api_key=EXTERNAL_API_KEY, base_url="https://api.minimax.io/v1")

response = client.chat.completions.create(
    model=EXTERNAL_MODEL, max_tokens=500,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt}
    ]
)
raw = response.choices[0].message.content or ""
raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
# Then parse raw as JSON as before
```

---

## Issue 12 — Report leads with raw lift; most representative metric is buried

**Scope:** Future fix — report presentation issue; applies to v3 report and any future experiment reports  
**Severity:** Moderate — the ordering creates an anchoring effect that misrepresents the experiment's most honest finding

The v3 report leads with raw lift (+0.341), which is the least representative of the three lift metrics computed. The decomposition to corrected lift (+0.127) and fair-comparison lift (+0.053) exists in the sensitivity analysis but is not prominent. Most readers will anchor on +0.341 before reaching the corrections.

The three metrics measure different things:
- **Raw lift (+0.341):** Includes structural penalties on baseline (DC hardcoded to 0.0, DRQ capped at 0.5) that reflect real architectural differences but are not measures of epistemic value. Debate's apparent advantage here is partly definitional.
- **Corrected lift (+0.127):** Removes the structural penalties, leaving only genuine performance differences on equally-applicable dimensions.
- **Fair-comparison lift (+0.053):** Restricts to dimensions where baseline has equal structural agency — the most honest answer to "does debate outperform baseline on a level playing field?"

The rubric design is pre-registered and defensible. The penalties are not wrong — DC and DRQ measure things baseline genuinely cannot do. But a report that answers "does debate help?" should lead with the number that measures debate's value under equal conditions (+0.053), not the number inflated by structural asymmetries (+0.341).

**What to fix in v4:** Lead with fair-comparison lift as the primary metric in the abstract and findings summary. Present raw lift in the decomposition table as supplementary context with an explicit note that it includes structural penalties. The sensitivity analysis ordering should mirror this: most representative first, least representative last.

---

## Issue 13 — DC scored 0.0 for baseline instead of N/A; inflates raw lift

**Scope:** Active — affects all v3 lift calculations; must be corrected in v4 rubric  
**Severity:** High — DC=0.0 for baseline is the single largest contributor to raw lift inflation and is indefensible on methodological grounds

The rubric scores DC (Defender Correctness) as 0.0 for baseline because baseline has no Defender. This is wrong. DC should be N/A for baseline for the same reason ETD is N/A when `ideal_resolution` is `critique_wins` or `defense_wins` — the dimension is structurally inapplicable, not failed. Baseline doesn't play the Defender role; penalizing it for not performing a role it never had is not a legitimate comparison.

The consequence is material. DC=0.0 for baseline vs. DC≈1.0 for debate conditions is the single largest per-dimension gap in the rubric, and it drives the majority of the raw lift (+0.341). The corrected lift (+0.127) and fair-comparison lift (+0.053) both implicitly acknowledge this by removing or restricting DC from the comparison — but the damage is done if the raw lift number leads.

The rubric's own precedent makes this inconsistency visible: ETD is scored N/A when inapplicable, not 0.0. DC should follow the same logic. There is no principled argument for treating "role not present" as a failure on DC while treating "case type not applicable" as N/A on ETD.

A secondary observation: in v3, DC = FVC empirically for all non-baseline conditions (the report states this explicitly). This means DC added no independent signal over FVC for the conditions where it was actually scored. Combined with the baseline inflation, DC contributed inflated lift without contributing information.

**What to fix in v4:**
- Score DC as N/A for baseline, consistent with ETD's N/A treatment for inapplicable cases
- Re-derive expected lift metrics with this correction applied before preregistering targets
- Evaluate whether DC provides independent signal over FVC in v4 (harder cases may produce Defender/Judge divergence, which would validate DC as a genuine independent dimension)
- Pre-register an explicit rationale for DC's treatment of baseline in the v4 rubric so it cannot be attacked as a post-hoc choice

---

## Issue 14 — Multiround condition was never meaningfully exercised

**Scope:** Active — affects v3 interpretation of multiround results; v4 design response decided  
**Severity:** Moderate — multiround is presented as a distinct condition but was functionally identical to isolated_debate in 91.5% of runs

Multiround averaged 1.03 rounds in v3, with 91.5% of runs resolving in a single round. A multiround run that resolves in one round is structurally identical to isolated_debate — the Critic and Defender exchange once, the Judge decides, and no additional rounds occur. The multi-round mechanism requires genuine contested territory to activate; the v3 benchmark's easy cases provided none.

The consequence: the score difference between multiround (0.986) and isolated_debate (0.975) is not measuring "what additional rounds contribute." It is noise plus the occasional second round on the 8.5% of runs that exercised the mechanism. Any claim about multiround's relative performance is ungrounded. This is related to but distinct from Issue 9 (near-ceiling scores) — a harder benchmark could still show near-ceiling scores across conditions while genuinely exercising the multiround mechanism.

**V4 design response:** Add a **forced multiround condition** (2-round minimum) run on all hard cases only. The Critic must respond to the Defender's response at least once, even if all points appeared conceded in round 1. This guarantees the mechanism is exercised at least once beyond the opening exchange without manufacturing artificial debate on easy cases where early resolution is correct. Limiting to hard cases keeps compute cost manageable.

The 2-round minimum is the smallest intervention that validates the mechanism. Running it alongside natural multiround on hard cases enables a direct comparison: if forced multiround outperforms natural multiround, Defenders are conceding too quickly and the additional exchange surfaces real signal. If they perform the same, natural multiround is validated as sufficient for cases with genuine complexity.

**ML-lab design question — revisit after v4:** If v4 hard cases produce natural multiround averaging 2+ rounds, the v3 result (1.03 rounds) was a benchmark difficulty artifact and the current ml-lab protocol is sound. If v4 hard cases still produce ~1 round naturally but forced multiround scores higher, that is a protocol finding: ml-lab should enforce a minimum of 2 rounds in its debate design. Do not resolve this question before v4 results are in.

---

## Issue 15 — ETD scored for ensemble and baseline; creates an illegitimate comparison

**Scope:** Active — affects all v3 ETD comparisons involving ensemble and baseline; v4 redesign decided  
**Severity:** High — the ensemble ETD result (mean 1.000) is an artifact of the evaluation design, not evidence that ensemble produces better empirical tests than debate

### Background: the ensemble's original purpose

The ensemble condition was designed as a compute-matched non-adversarial baseline: three independent Critic passes synthesized into a verdict, using the same total token budget as isolated_debate. The intent was to isolate the effect of adversarial role structure — does debate's critic/defender/judge exchange improve reasoning, or does simply running more independent passes achieve the same thing?

### How ETD entered the ensemble

The ETD dimension (Empirical Test Design) measures whether the final verdict includes a well-specified, actionable empirical test for contested claims. In v3, the scoring prompt instructed all conditions — including ensemble and baseline — to produce an empirical test if any contested claims existed. This was added as a structural prompt constraint because early runs showed the debate protocol without the instruction produced ETD=0.0 nearly universally (the agents never spontaneously produced structured test designs).

### Why both naive options fail

Once ETD is a prompt constraint applied uniformly, the comparison is broken in two ways depending on what you do:

**Option A — Give ensemble the ETD instruction:** The ensemble agents receive the same ETD prompt constraint as debate agents. This means ensemble ETD is scored against the same rubric as debate ETD. But this is testing ml-lab's prompt engineering against itself: the ETD signal reflects whether the synthesizer followed a formatting instruction, not whether adversarial role structure produces better empirical reasoning. The ensemble's ETD=1.000 result is exactly this artifact. No debate occurred; the synthesizer simply formatted its output correctly.

**Option B — Withhold the ETD instruction from ensemble:** The ensemble is set up to fail on ETD before the first token is generated. This is not a fair comparison either — it measures "who had the instruction" not "who reasoned better."

Both options conflate instruction compliance with reasoning quality. ETD cannot be used to compare debate vs. non-debate conditions when the dimension is instruction-dependent rather than structure-dependent.

### Resolution: ETD is a debate-internal metric in v4

ETD will be scored N/A for ensemble and baseline in v4. This is not a workaround — it reflects what ETD actually measures. An empirical test is meaningful as a debate output because it represents what the Judge determined could resolve a contested point after the Critic and Defender have both argued it. For ensemble and baseline, there is no contested point structure — only a single-pass verdict (or a synthesis of single-pass verdicts). The concept of "test that resolves a contested claim" does not exist in those conditions.

This treatment is consistent with the existing N/A precedent: ETD is already scored N/A for cases where `ideal_resolution` is `critique_wins` or `defense_wins`, because those cases have no contested territory to test. The same logic extends to conditions with no adversarial exchange.

### V4 comparison structure

Two clean comparisons replace the previous undifferentiated all-conditions table:

1. **Debate vs. ensemble** — scored on IDR, IDP, DRQ, FVC only (the dimensions both can legitimately produce). ETD excluded from this comparison. This answers: "does adversarial role structure improve issue identification and verdict quality beyond compute-matched parallel passes?"

2. **Debate conditions vs. each other** (isolated_debate, multiround, forced_multiround) — scored on IDR, IDP, DRQ, FVC, ETD. ETD included here because all three conditions involve the same adversarial exchange; the dimension is structurally applicable. This answers: "does additional debate structure improve outcomes within the adversarial paradigm?"

Baseline (single-pass, no synthesis) remains in the result tables for orientation, but is excluded from formal lift calculations. Its role is to anchor the scale, not to compete on dimensions it was never designed to exercise.

**This must be disclosed in the v4 experiment report.** The v3 ensemble ETD=1.000 result should be reported as a measurement artifact and the redesign rationale — including the Option A / Option B analysis — should appear in the methods section. Reviewers will ask why ETD is excluded from the debate vs. ensemble comparison; the answer must be pre-emptive, not defensive.

---

## Issue 16 — Closed-loop evaluation: case-source confound addressed, scoring-model confound unquantified

**Scope:** Active — affects interpretation of all v3 results; partially mitigated but residual confound unquantified  
**Severity:** High — this is the most structurally fundamental critique of the experiment design; must be addressed openly in the v4 report  
**Related:** Issue 11 (MiniMax cross-model scorer failure)

The experiment has two closed-loop risks. Cases were generated by GPT and scored by Claude Sonnet 4.6. The concern is that the experiment measures "did Claude recognize what GPT planted?" rather than "does debate improve ML reasoning review under general conditions?"

### Two mitigations were attempted; both were compromised

**Mitigation 1 — Cross-model scorer (Issue 11):** MiniMax-M2.7 was used as an independent scorer. 82% of cases failed to parse due to SDK compatibility issues. The 7 valid cases showed IDR delta=0.0, which is directionally consistent with no same-family scorer bias for IDR, but the sample is too small and covers only one dimension. See Issue 11 for the corrected API pattern to use in v4.

**Mitigation 2 — External benchmark cases:** 16 cases drawn from real published ML papers (13) and grounded synthetic constructions (3) were run through the full protocol. These cases were created independently of the GPT case generator.

### What the external results do and don't address

The external results address the **case-source** half of the confound. The 13 published-paper cases are genuine independent instances of ML methodological failures — not GPT's synthetic constructions. Debate scoring 1.000 on those cases is cross-corpus evidence that the protocol is not narrowly tuned to GPT's framing of what ML failures look like. The baseline consistency (external 0.628 vs. main benchmark 0.634) confirms the external cases are not systematically easier or harder on non-structural dimensions — they are a real independent stratum.

The external results do **not** address the **scoring-model** half of the confound. The scorer is still Claude judging Claude's debate output against Claude's rubric interpretation. Whether Claude scores Claude's outputs more favorably than it would score an equivalent output from a different model family is unknown and untested.

### The ceiling problem prevents quantification

All debate conditions scored 1.000 on external cases, identical to the main benchmark. This means the external stratum cannot discriminate between isolated, multiround, and ensemble — nor can it reveal any scoring bias that might favor one condition over another. The confound exists in a region where there is no variance to analyze.

### What can be honestly stated

- **Case-source confound:** Addressed. Published-paper external cases rule out "model only recognizes GPT-generated patterns."
- **Scoring-model confound:** Not addressed. The scorer-model closed loop is intact. The 7-case MiniMax result provides a directional bound (IDR delta=0.0) but is not sufficient to claim the confound is quantified.
- **Net status:** The experiment is partially open-loop on case source, fully closed-loop on scoring. The report must present this distinction explicitly rather than treating "we ran external cases" as a complete response to the closed-loop critique.

### What to fix in v4

- Run MiniMax cross-model scoring using the corrected OpenAI-compatible API (Issue 11) across all 50+ benchmark cases
- Compute per-dimension deltas (not just IDR) between Claude scorer and MiniMax scorer
- If deltas are near-zero across dimensions, quantify the bound ("scoring bias contributes at most X to reported lift")
- If deltas are material, report them as a sensitivity range alongside the main results
- Human evaluation of a stratified sample (e.g., 10–15 cases across difficulty tiers) would close the remaining loop; this is the only way to validate the rubric interpretation itself

---

## Issue 17 — Report artifact contains prompt leakage; limitations framed as design properties

**Scope:** Active — affects v3 report credibility; must be corrected in v4 plan and reporting agent  
**Severity:** High — prompt leakage is an implementation failure; dishonest limitation framing is an intellectual integrity failure

### Part 1: Prompt leakage

The v3 report opens with: *"Results mode. Findings stated as facts. Limitations framed as design properties."* This is internal guidance directed at the reporting agent — it is not a methodological statement and has no place in a technical report artifact. It appeared in the final report because the agent echoed its own directive into its output rather than acting on it silently.

**What to fix in v4:** The v4 plan must explicitly instruct the reporting agent not to emit internal mode declarations or prompt directives in report output. Any preamble of the form "Mode: X" or "Framing: Y" is agent-internal and must be stripped before the artifact is written. The report should begin with the executive summary, not with instructions to itself.

### Part 2: Framing norm — limitations are threats to validity, not design properties

Independently of the leakage, framing genuine methodological failures as "design properties" is intellectually dishonest. A design property is an intentional architectural choice with a defensible rationale (e.g., ETD=N/A for defense_wins cases — the dimension is structurally inapplicable). A limitation is a threat to validity that a reader must weigh when interpreting results.

The v3 report conflates these. The ceiling problem (Issue 9), the closed-loop scoring confound (Issue 16), and the uncomputed convergence metric (Issue 8, see below) are threats to validity. Labeling them as design properties forecloses the scrutiny they deserve and misrepresents the experiment's evidentiary weight to any reader who doesn't dig into the sensitivity analysis.

**What to fix in v4:** The v4 plan must include an explicit norm for the reporting agent:

- **Design property:** An intentional choice with a stated rationale that does not undermine the validity of the reported results (e.g., ETD=N/A for inapplicable case types; DC=N/A for baseline).
- **Limitation / threat to validity:** Any factor that could cause the reported results to be wrong, overstated, or non-generalizable (e.g., benchmark ceiling, closed-loop scoring, pre-registered metric not computed).

Limitations must be presented with their threat-to-validity label in the report. Each limitation entry should state: what the threat is, what evidence bears on its magnitude, and what was done to mitigate it. The "design property" label is reserved for intentional choices only — it may never be applied to a failure mode.

---

## Issue 18 — Pre-registered convergence metric misconceived relative to the ml-lab protocol

**Scope:** Active — metric was never computable; reported as N/A in v3 conclusions  
**Severity:** Moderate — the metric gap is a pre-registration failure, but the underlying concept it was meant to capture can be replaced with a computable analog in v4

### What was pre-registered

```json
"convergence_metric": {
    "definition": "1.0 if critic_verdict == defender_verdict; 0.5 if they diverge",
    "source_fields": "critic_raw verdict vs defender_raw verdict extracted from v3_raw_outputs/"
}
```

The metric was intended to measure whether the Critic and Defender independently converged on the same overall verdict per isolated_debate run.

### Root cause: doubly wrong

The metric was not merely missing fields — it was misconceived relative to the ml-lab protocol it was designed to measure.

**Problem 1 — Neither agent produces a verdict field.** The Critic produces `CRITIQUE.md`: a list of critique points. No `critic_verdict` field exists anywhere in the protocol or the raw output schema. The Defender produces `DEFENSE.md`: per-point labels (`concede` / `rebut` / `empirically_open`). No global `defender_verdict` field exists. The raw output confirms this — `critic_raw` and `defender_raw` are full prose text; `verdict` is the Judge's synthesized output only. There was never going to be a `critic_verdict` or `defender_verdict` field to compare.

**Problem 2 — The metric concept doesn't match how ml-lab defines convergence.** The ml-lab protocol uses "convergence" to mean *debate convergence*: whether contested points in `DEBATE.md` reach resolution (concession or empirical agreement) across rounds. This is a per-point resolution concept tracked at the debate level, not a global agent-vs-agent verdict comparison. The pre-registered metric conflated two different things: whether two agents independently agree (a coincidence measure) vs. whether the debate process successfully resolves contested territory (a protocol quality measure). The former is not a natural output of the ml-lab protocol; the latter is.

### Consequence

The metric was reported as N/A with no further analysis. Under Issue 17's framing norm, this should have been reported as a pre-registration failure — a metric committed to before the experiment that could not be computed. Instead it was categorized alongside inapplicable dimensions (ETD on defense_wins cases), which implied it was a design choice rather than a failure.

### What a computable analog looks like in v4

Point resolution rate from `DEBATE.md` is a natural, protocol-aligned convergence measure: what fraction of contested points reached concession or empirical agreement vs. remained open after the final debate round? This is already tracked implicitly in the debate structure and requires no new output fields from the agents.

For the isolated_debate condition specifically, a secondary computable signal exists: does the Judge's final `verdict` field match the Critic's implied position (`critique_wins`) or the Defender's implied position (`defense_wins`)? This requires inferring each agent's implied position from prose, which is error-prone — but it is at least grounded in fields that exist. If pursued, it should be extracted by a dedicated scorer pass, not by hand.

**What to fix in v4:** Pre-register only metrics that are verified to be computable against the actual raw output schema before the experiment runs. For convergence specifically, replace the critic/defender verdict comparison with point resolution rate derived from `DEBATE.md`. Define the field names and extraction logic in the pre-registration document itself, not as a post-hoc extraction plan.

---

## Issue 19 — Phase 4 protocol self-review gate was bypassed

**Scope:** Active — the pre-execution gate produced a valid conditional verdict that was not enforced before the experiment ran  
**Severity:** High — several post-mortem issues in this document were pre-identified by the Phase 4 critique and could have been prevented

### What the Phase 4 gate produced

`CRITIQUE.md` and `DEFENSE.md` are the Phase 4 Protocol Self-Review artifacts from v3. The ml-critic reviewed `HYPOTHESIS.md`, `PREREGISTRATION.json`, and `evaluation_rubric.json` and identified 10 design issues before any agent runs. The ml-defender responded point-by-point and issued an overall verdict of **empirical_test_agreed** — the design was conditionally approved for execution, but only after four specific gaps were confirmed closed:

| Pre-execution requirement | Outcome |
|---|---|
| ETD instruction text committed verbatim in EXECUTION_PLAN.md | Not locked → ETD comparison confounded (post-mortem Issue 15) |
| `category` field confirmed stripped from agent context | Not confirmed → leakage risk unresolved |
| DRQ filter pre-specified in scoring engine for H4 test | Not enforced → multiround DRQ comparison confounded |
| Convergence metric added to scoring engine or locked post-processing schema | Not implemented → metric unreportable (post-mortem Issue 18) |

The experiment ran without any of these being confirmed closed. The Phase 4 gate was not a blocking gate — it produced a verdict and was ignored.

### What the Phase 4 critique correctly predicted

The Critic pre-identified the following issues that independently appeared in this post-mortem:

- **DC=0.0 for baseline is structurally unfair** (CRITIQUE Issue 5) → post-mortem Issue 13
- **DC=FVC double-counting inflates scores** (CRITIQUE Issue 1) → post-mortem Issue 13  
- **Convergence metric not implemented in scoring engine** (CRITIQUE Issue 10) → post-mortem Issue 18
- **ETD constraint not operationally locked** (CRITIQUE Issue 6) → post-mortem Issue 15

These were caught before execution, documented in the design review, and then not acted on. The protocol self-review worked. The enforcement mechanism did not.

### Root cause: two distinct failures

**ml-lab structural gap:** The ml-lab protocol's Gate 1 (after Step 5) is a *user approval* gate on the experiment plan — it is not a verdict-enforcement gate. ml-lab has no instruction to read the Defender's overall verdict and treat its conditions as blocking requirements. The Defender's `empirical_test_agreed` verdict and its associated conditions are left for the orchestrator to notice and act on. The protocol trusts the user gate to catch everything; it does not close the loop from Defender output to gated conditions.

**v3 plan execution failure:** The v3 plan does have a specific approval checkpoint at the end of Phase 4 with explicit conditions to verify before proceeding:

- Isolation is explicit: Critic and Defender each get only task_prompt
- ETD constraint pre-applied to ensemble synthesizer
- Structural overrides match PREREGISTRATION.json
- All conditions use `benchmark_cases_verified.json`

These four conditions were written before the self-review ran. They were never updated after the Defender produced its Pass 2 table. The Defender conceded six issues and flagged four as pre-execution blockers — category field stripping, DRQ filter pre-specification, convergence metric implementation, and ETD instruction verbatim lock. None of those appear in the v3 plan's approval checklist. The checklist was static and pre-authored; there was no step requiring the orchestrator to read `DEFENSE.md` after the review completed and extend the checklist with the Defender's actual conditions.

The v3 plan treated Phase 4 as a ceremony: run the review, check four pre-written boxes, proceed. The Defender's output was produced but not read for its gating implications.

### What to fix in v4

**Fix 1 — ml-lab (structural):** Add an explicit instruction after the Defender dispatch: read the Defender's overall verdict from `DEFENSE.md`. If the verdict is `empirical_test_agreed`, extract every conceded item and every pre-execution requirement from the Pass 2 table and add them to the Gate 1 approval checklist. Gate 1 may not be presented to the user until this extraction is complete.

**Fix 2 — v4 plan (procedural):** The Phase 4 approval checkpoint must be dynamically constructed from the Defender's actual Pass 2 output, not pre-written. The v4 plan should instruct the orchestrator to:

1. After receiving `DEFENSE.md`, parse the Pass 2 verdict table
2. Extract all `Concede` and `Rebut (partial concede)` items — each conceded item is a known gap that must be addressed or documented before execution
3. Identify any items the Defender flagged as requiring pre-execution action
4. Write the complete resolved-items list to `EXECUTION_PLAN.md` as a pre-flight checklist
5. Log a `gate` / `phase4_cleared` entry in `INVESTIGATION_LOG.jsonl` with the resolved items in `meta`
6. Do not proceed to Phase 5 until the gate entry is written

The Defender's verdict is not advisory — it is the experiment's own pre-registered quality check. A static pre-written checklist cannot substitute for reading the review output.

---
