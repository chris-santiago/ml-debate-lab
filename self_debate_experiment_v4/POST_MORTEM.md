# v4 Experiment Post-Mortem

Issues identified during and after execution of the v4 experiment plan. Each issue is scoped to whether it affected current results (active) or should be fixed in a future run (future fix).

---

## Issue 1 — Preflight Skill Bash Commands Use Relative Paths, Breaking When CWD Is Repo Root

**Scope:** Future fix
**Severity:** Moderate

### What Happened

The `/preflight` skill issued Bash tool calls using relative paths (e.g., `for f in plan/phases/*.md`) that assumed the working directory was `self_debate_experiment_v4/`. In practice the Bash tool's CWD is the repo root (`ml-debate-lab/`), so globs found no matches. When a bash glob expands to nothing, the loop variable receives the literal unexpanded pattern string rather than being skipped, causing downstream commands (`grep`, `awk`) to attempt to open that literal string as a filename and exit non-zero. Because parallel Bash tool calls share a failure-propagation model, the first failing call caused all remaining parallel calls in the same message to be cancelled, requiring multiple debug rounds before the root cause was identified.

### Root Cause

Bash glob patterns do not silently no-op when unmatched — by default the unexpanded pattern string is passed to the loop body as-is. Combined with the assumption that the Bash tool's CWD matches the experiment directory (it does not; it is always the repo root), every relative-path glob in the preflight checks silently misfired. The failure cascaded because parallel tool calls in a single message are cancelled when any one call exits non-zero.

### Impact

Preflight execution stalled repeatedly, producing misleading failures that appeared to be logic errors in the checks themselves. Multiple debug rounds were required to identify the CWD mismatch as the true cause. Experimental results were not affected.

### What to Fix

All path references in the `/preflight` skill should use absolute paths (constructed from a known repo-root anchor, e.g., `REPO="$(git rev-parse --show-toplevel)"`) or begin each Bash call with an explicit `cd` into the experiment root before any glob or file operation. Additionally, checks that are likely to fail independently should not be issued as parallel Bash tool calls; sequential calls should be used so that one failing check does not cascade-cancel unrelated checks.
