# Monitor for Spec Drift

`/intent-watch` detects when code changes conflict with a source-of-truth document (typically `HYPOTHESIS.md` or a pre-registration spec). It's used at two points in the ml-lab workflow.

## Gate 1: one-time clean pass

Before Step 6 (experiment execution), ml-lab requires a clean `/intent-watch` pass:

```shell
/intent-watch <experiment_dir> HYPOTHESIS.md
```

Any HIGH or CRITICAL conflict blocks the experiment. Resolve conflicts before proceeding.

## Step 6: continuous monitoring

During experiment scripting, run `/intent-watch` in a loop to catch drift as it happens:

```shell
/loop 2m /intent-watch <experiment_dir> HYPOTHESIS.md
```

This checks every 2 minutes for changes that violate the pre-registration constraints.

## What it checks

The `intent-monitor` agent:

1. Indexes binding constraints from the source-of-truth document
2. Detects recent git changes in the experiment directory
3. Evaluates diffs for introduced conflicts

## Handling conflicts

When a conflict is detected, you have two options:

1. **Fix the code** — revert the change that caused the drift
2. **Amend the spec** — if the drift is justified, update the source-of-truth document and log the amendment in the spec's amendment log

Always log amendments with `/log-entry` so the audit trail captures *why* the spec changed.

## You have now...

Set up pre-registration compliance monitoring using `/intent-watch` at Gate 1 and during experiment execution.
