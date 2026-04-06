#!/usr/bin/env python3
"""
External validation benchmark runner for v3 experiment.
Runs all 4 conditions x 3 runs for the 14 missing external cases.
"""
import json
import os
import subprocess
import sys

OUTPUT_DIR = "/Users/chrissantiago/Dropbox/GitHub/ml-debate-lab/self_debate_experiment_v3/v3_raw_outputs"
CASES_FILE = "/Users/chrissantiago/Dropbox/GitHub/ml-debate-lab/self_debate_experiment_v3/external_cases_v3.json"

def file_exists(case_id, condition, run_n):
    fname = f"{case_id}_{condition}_run{run_n}.json"
    return os.path.exists(os.path.join(OUTPUT_DIR, fname))

def write_output(data, case_id, condition, run_n):
    fname = f"{case_id}_{condition}_run{run_n}.json"
    fpath = os.path.join(OUTPUT_DIR, fname)
    with open(fpath, "w") as f:
        json.dump(data, f, indent=2)
    print(f"  Written: {fname}")

def main():
    with open(CASES_FILE) as f:
        cases = json.load(f)

    missing = []
    for case in cases:
        cid = case["case_id"]
        for condition in ["isolated_debate", "multiround_debate", "ensemble", "baseline"]:
            for run_n in [1, 2, 3]:
                cond_key = condition.replace("_debate", "").replace("multiround", "multiround")
                if not file_exists(cid, condition if condition != "multiround_debate" else "multiround", run_n):
                    missing.append((cid, condition, run_n))

    print(f"Missing outputs: {len(missing)}")
    for m in missing[:20]:
        print(f"  {m[0]} | {m[1]} | run{m[2]}")

if __name__ == "__main__":
    main()
