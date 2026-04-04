"""
Within-case variance estimation — Issue 8 (remaining).

Estimates LLM stochasticity by re-running the full debate protocol
3-5 times on a representative subset of cases and computing per-case
score variance across runs.

REQUIRES: Claude Code with agent dispatch capability.
Run from within a Claude Code session using:
    python within_case_variance.py --dry-run    # prints run plan, no API calls
    python within_case_variance.py              # executes runs (requires Claude API)

The script dispatches subagents for each run using the claude CLI.
Each run dispatches: 1 Critic + 1 Defender + 1 Judge + 1 Baseline = 4 calls per case.
Total for 5 cases × 3 runs: ~60 API calls.

Selected cases (representative of difficulty/category spread):
  - broken_baseline_001 (easy, critique)
  - metric_mismatch_003 (hard, critique)
  - hidden_confounding_002 (hard, critique)
  - defense_wins_001 (medium, defense)
  - real_world_framing_002 (hard, critique)

Outputs: within_case_variance_results.json
"""

import json
import os
import sys
import subprocess
import argparse
import statistics

# ---------------------------------------------------------------------------
# Representative subset
# ---------------------------------------------------------------------------

SUBSET_CASES = [
    "broken_baseline_001",
    "metric_mismatch_003",
    "hidden_confounding_002",
    "defense_wins_001",
    "real_world_framing_002",
]

N_RUNS = 3

AGENT_ROLES = {
    "critic": "ml-critic",
    "defender": "ml-defender",
}


def load_json(path):
    with open(path) as f:
        return json.load(f)


def get_task_prompt(case_id, cases):
    for c in cases:
        if c["case_id"] == case_id:
            return c.get("task_prompt", f"[See BENCHMARK_PROMPTS.md for {case_id}]")
    return None


def dry_run_plan():
    print("=== Within-Case Variance Estimation — Dry Run Plan ===\n")
    print(f"Cases: {SUBSET_CASES}")
    print(f"Runs per case: {N_RUNS}")
    print(f"Calls per case per run: 4 (Critic + Defender + Judge + Baseline)")
    total = len(SUBSET_CASES) * N_RUNS * 4
    print(f"Total API calls: {total}")
    print(f"\nFor each case × run:")
    print("  1. Dispatch Critic (task_prompt only)")
    print("  2. Dispatch Defender (task_prompt only, isolated)")
    print("  3. Dispatch Judge (task_prompt + critic_output + defender_output)")
    print("  4. Dispatch Baseline (task_prompt only, single-pass)")
    print("  5. Score outputs against rubric")
    print("\nOutputs: per-run scores, per-case mean ± std, aggregate variance table")
    print("\nTo execute: python within_case_variance.py")


def run_variance_estimation(results_json_path, benchmark_prompts_path):
    """
    NOTE: This function requires the claude CLI to be available and
    authenticated. It dispatches subagents for each role.

    In practice, this is best run interactively via Claude Code rather
    than as a standalone script, since it requires spawning Claude subagents.

    The script structure is provided to document the intended experiment design.
    Replace the subprocess calls with actual claude CLI invocations or
    Agent tool calls from within a Claude Code session.
    """
    data = load_json(results_json_path)
    cases_lookup = {c["case_id"]: c for c in data["cases"]}

    all_run_results = {}

    for case_id in SUBSET_CASES:
        case = cases_lookup.get(case_id)
        if not case:
            print(f"WARNING: {case_id} not found in results JSON")
            continue

        task_prompt = case.get("task_prompt", "")
        run_scores = []

        for run_idx in range(N_RUNS):
            print(f"  {case_id} — run {run_idx + 1}/{N_RUNS}")

            # In a Claude Code session, replace these with Agent tool dispatches:
            # critic_output = dispatch_agent("ml-critic", task_prompt)
            # defender_output = dispatch_agent("ml-defender", task_prompt)
            # judge_output = dispatch_agent("ml-lab-judge", task_prompt + critic + defender)
            # baseline_output = dispatch_agent("single-pass-baseline", task_prompt)
            # scores = score_outputs(...)

            # Placeholder — replace with actual agent dispatches:
            scores = {
                "IDR": None, "IDP": None, "DC": None,
                "DRQ": None, "ETD": None, "FVC": None,
                "debate_mean": None, "baseline_mean": None,
            }
            run_scores.append(scores)

        all_run_results[case_id] = {
            "runs": run_scores,
            "original_debate_mean": case["debate_mean"],
            "per_run_debate_means": [r["debate_mean"] for r in run_scores if r["debate_mean"] is not None],
        }

    # Compute variance across runs
    variance_results = {}
    for case_id, data in all_run_results.items():
        means = data["per_run_debate_means"]
        if len(means) >= 2:
            variance_results[case_id] = {
                "original_mean": data["original_debate_mean"],
                "run_means": means,
                "std_dev": round(statistics.stdev(means), 4),
                "range": round(max(means) - min(means), 4),
            }

    output = {
        "n_cases": len(SUBSET_CASES),
        "n_runs_per_case": N_RUNS,
        "cases": variance_results,
        "note": "Placeholder results — run agent dispatches to populate with real scores.",
    }

    out_path = os.path.join(os.path.dirname(results_json_path), "within_case_variance_results.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"Template saved to {out_path}")
    print("NOTE: Populate by running actual agent dispatches from a Claude Code session.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Print run plan without executing")
    args = parser.parse_args()

    if args.dry_run:
        dry_run_plan()
        return

    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_path = os.path.join(base_dir, "self_debate_results.json")
    prompts_path = os.path.join(base_dir, "BENCHMARK_PROMPTS.md")

    print("=== Within-Case Variance Estimation ===")
    print("NOTE: This script requires Claude Code agent dispatch capability.")
    print("Replace placeholder calls in run_variance_estimation() with actual Agent tool dispatches.")
    print("Running in template mode — outputting experiment structure without live API calls.\n")

    run_variance_estimation(results_path, prompts_path)


if __name__ == "__main__":
    main()
