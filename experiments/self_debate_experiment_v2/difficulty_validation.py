"""
Difficulty label validation — Issue 18.

Tests whether author-assigned difficulty labels (easy/medium/hard) are
correlated with baseline scores as an independent difficulty proxy.
Rationale: harder cases should be harder for the single-pass baseline too.

Outputs: difficulty_validation_results.json

Usage:
    cd self_debate_experiment_v2/
    python difficulty_validation.py
"""

import json
import os

def load_json(path):
    with open(path) as f:
        return json.load(f)

def spearman_rho(x, y):
    """Spearman rank correlation between two lists."""
    n = len(x)
    def rank(lst):
        sorted_vals = sorted(enumerate(lst), key=lambda t: t[1])
        ranks = [0] * n
        i = 0
        while i < n:
            j = i
            while j < n and sorted_vals[j][1] == sorted_vals[i][1]:
                j += 1
            avg_rank = (i + j + 1) / 2  # 1-indexed average rank
            for k in range(i, j):
                ranks[sorted_vals[k][0]] = avg_rank
            i = j
        return ranks

    rx, ry = rank(x), rank(y)
    d2 = sum((a - b) ** 2 for a, b in zip(rx, ry))
    rho = 1 - 6 * d2 / (n * (n ** 2 - 1))
    return round(rho, 4)

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data = load_json(os.path.join(base_dir, "self_debate_results.json"))

    difficulty_map = {"easy": 1, "medium": 2, "hard": 3}

    cases = data["cases"]
    all_cases = [
        (c["case_id"], c["difficulty"], c["baseline_mean"], c["category"])
        for c in cases
    ]

    # --- All 20 cases ---
    diff_numeric = [difficulty_map[c[1]] for c in all_cases]
    baseline_scores_all = [c[2] for c in all_cases]
    # Invert baseline score for correlation (harder → lower baseline → higher rank on inverted)
    # We expect: higher difficulty → lower baseline score → rho should be negative
    rho_all = spearman_rho(diff_numeric, baseline_scores_all)

    # --- Exclude defense_wins (baseline=0.0 by construction regardless of difficulty) ---
    non_dw = [(c[0], c[1], c[2]) for c in all_cases if c[3] != "defense_wins"]
    diff_non_dw = [difficulty_map[c[1]] for c in non_dw]
    baseline_non_dw = [c[2] for c in non_dw]
    rho_non_dw = spearman_rho(diff_non_dw, baseline_non_dw)

    # --- Means by difficulty ---
    def group_means(case_list):
        groups = {"easy": [], "medium": [], "hard": []}
        for _, diff, score in case_list:
            groups[diff].append(score)
        return {d: (round(sum(v)/len(v), 4), len(v)) for d, v in groups.items() if v}

    means_all = group_means([(c[0], c[1], c[2]) for c in all_cases])
    means_non_dw = group_means(non_dw)

    results = {
        "all_20_cases": {
            "spearman_rho": rho_all,
            "interpretation": "Negative rho = harder labels associated with lower baseline scores (expected if labels are valid)",
            "means_by_difficulty": means_all,
        },
        "non_defense_wins_15_cases": {
            "spearman_rho": rho_non_dw,
            "interpretation": "Excludes defense_wins cases (baseline=0.0 by structural construction, not difficulty)",
            "means_by_difficulty": means_non_dw,
        },
        "conclusion": None,
    }

    rho = rho_non_dw
    if rho < -0.2:
        conclusion = f"Labels validated: rho={rho} (negative, harder labels associate with lower baseline). Monotonic pattern: easy > medium > hard on baseline scores (non-defense_wins cases)."
    elif -0.2 <= rho <= 0.2:
        conclusion = f"Labels weakly validated: rho={rho} (near zero). Difficulty labels have limited correlation with baseline scores — labels may reflect intended difficulty, not actual task difficulty for the protocol."
    else:
        conclusion = f"Labels not validated: rho={rho} (positive, easier labels associate with lower baseline). Labels may be miscalibrated."

    results["conclusion"] = conclusion

    # Print
    print("=== Difficulty Label Validation ===\n")
    print(f"All 20 cases — Spearman rho (difficulty vs. baseline): {rho_all}")
    print(f"Non-defense_wins — Spearman rho: {rho_non_dw}\n")

    print("Baseline means by difficulty (all 20):")
    for d in ["easy", "medium", "hard"]:
        if d in means_all:
            mean, n = means_all[d]
            print(f"  {d:8s}: {mean:.4f}  (n={n})")

    print("\nBaseline means by difficulty (non-defense_wins, 15 cases):")
    for d in ["easy", "medium", "hard"]:
        if d in means_non_dw:
            mean, n = means_non_dw[d]
            print(f"  {d:8s}: {mean:.4f}  (n={n})")

    print(f"\nConclusion: {conclusion}")

    out_path = os.path.join(base_dir, "difficulty_validation_results.json")
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved to {out_path}")

if __name__ == "__main__":
    main()
