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
