"""
Cross-model scorer validation — Issue 5.

Tests whether the debate protocol's high IDR scores reflect genuine issue
detection or same-model self-consistency bias (the scorer is the same model
family that generated the transcripts).

REQUIRES: An external model API key (OpenAI or Google). Set one of:
    export OPENAI_API_KEY=...        # uses gpt-4o
    export GOOGLE_API_KEY=...        # uses gemini-1.5-pro

The scorer is given each case's debate transcript (Critic + Defender outputs)
and the task prompt, but NOT the must_find labels. It must independently
identify which issues were found and score IDR.

Outputs: cross_model_scores.json

Usage:
    cd self_debate_experiment_v2/
    OPENAI_API_KEY=sk-... python cross_model_scorer.py
"""

import json
import os
import sys

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OPENAI_MODEL = "gpt-4o"
GEMINI_MODEL = "gemini-1.5-pro"

SCORER_PROMPT_TEMPLATE = """You are an objective rubric scorer evaluating an ML hypothesis investigation.

## Task prompt that was given to the investigating agents:
{task_prompt}

## Critic output:
{critic_output}

## Defender output:
{defender_output}

## Scoring instructions:
Score the following rubric dimension for the DEBATE PROTOCOL (not the baseline):

**IDR (Issue Discovery Recall):** What fraction of the critical methodological issues in the task prompt did the agents collectively identify? Score:
- 1.0 = all critical issues identified
- 0.5 = some critical issues identified, some missed
- 0.0 = no critical issues identified

Do NOT reference any answer key. Score based solely on whether the agents' outputs identify genuine methodological problems with the work described in the task prompt.

Respond in JSON format:
{{
  "IDR": <0.0 | 0.5 | 1.0>,
  "issues_found": ["<brief description of each issue the agents identified>"],
  "reasoning": "<1-2 sentences explaining your score>"
}}
"""

# ---------------------------------------------------------------------------
# API clients (lazy import — only the one that's configured)
# ---------------------------------------------------------------------------

def get_openai_score(prompt):
    try:
        import openai
    except ImportError:
        print("ERROR: openai package not installed. Run: pip install openai")
        sys.exit(1)
    client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0,
    )
    return json.loads(response.choices[0].message.content)


def get_gemini_score(prompt):
    try:
        import google.generativeai as genai
    except ImportError:
        print("ERROR: google-generativeai package not installed. Run: pip install google-generativeai")
        sys.exit(1)
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    model = genai.GenerativeModel(GEMINI_MODEL)
    response = model.generate_content(prompt)
    return json.loads(response.text)


def get_score(prompt):
    if os.environ.get("OPENAI_API_KEY"):
        return get_openai_score(prompt), OPENAI_MODEL
    elif os.environ.get("GOOGLE_API_KEY"):
        return get_gemini_score(prompt), GEMINI_MODEL
    else:
        print("ERROR: Set OPENAI_API_KEY or GOOGLE_API_KEY before running.")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data = load_json(os.path.join(base_dir, "self_debate_results.json"))
    benchmark_prompts = load_json(os.path.join(base_dir, "benchmark_prompts.json")) \
        if os.path.exists(os.path.join(base_dir, "benchmark_prompts.json")) \
        else None

    # Non-defense_wins cases only (IDR applies)
    cases = [c for c in data["cases"] if c["correct_position"] != "defense"]

    results = []
    original_idr_scores = []
    cross_model_idr_scores = []

    for case in cases:
        case_id = case["case_id"]
        print(f"Scoring {case_id}...")

        # Get transcript text from the results JSON
        critic_output = case.get("transcripts", {}).get("critic", "[Transcript not available — re-run agents]")
        defender_output = case.get("transcripts", {}).get("defender", "[Transcript not available — re-run agents]")

        # Task prompt: try benchmark_prompts.json, else use case description
        task_prompt = case.get("task_prompt", f"[See BENCHMARK_PROMPTS.md for {case_id}]")

        prompt = SCORER_PROMPT_TEMPLATE.format(
            task_prompt=task_prompt,
            critic_output=critic_output,
            defender_output=defender_output,
        )

        score_result, model_used = get_score(prompt)
        cross_model_idr = score_result.get("IDR", None)
        original_idr = case["debate_scores"].get("IDR")

        results.append({
            "case_id": case_id,
            "original_IDR": original_idr,
            "cross_model_IDR": cross_model_idr,
            "delta": round(cross_model_idr - original_idr, 4) if cross_model_idr is not None and original_idr is not None else None,
            "issues_found": score_result.get("issues_found", []),
            "reasoning": score_result.get("reasoning", ""),
            "scorer_model": model_used,
        })

        if original_idr is not None:
            original_idr_scores.append(original_idr)
        if cross_model_idr is not None:
            cross_model_idr_scores.append(cross_model_idr)

    # Aggregate
    n = len([r for r in results if r["delta"] is not None])
    mean_original = sum(original_idr_scores) / len(original_idr_scores) if original_idr_scores else None
    mean_cross = sum(cross_model_idr_scores) / len(cross_model_idr_scores) if cross_model_idr_scores else None
    mean_delta = (mean_cross - mean_original) if (mean_original and mean_cross) else None

    output = {
        "scorer_model": results[0]["scorer_model"] if results else None,
        "n_cases": n,
        "original_mean_IDR": round(mean_original, 4) if mean_original else None,
        "cross_model_mean_IDR": round(mean_cross, 4) if mean_cross else None,
        "mean_delta": round(mean_delta, 4) if mean_delta else None,
        "bias_material": abs(mean_delta) > 0.1 if mean_delta is not None else None,
        "interpretation": (
            f"IDR shifted by {mean_delta:+.4f}. "
            + ("Self-scoring bias is MATERIAL (|delta| > 0.1)." if abs(mean_delta) > 0.1 else "Self-scoring bias is NOT material (|delta| <= 0.1).")
        ) if mean_delta is not None else "Could not compute — check transcripts",
        "cases": results,
    }

    out_path = os.path.join(base_dir, "cross_model_scores.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n=== Cross-Model Scorer Results ===")
    print(f"Original IDR mean:     {mean_original:.4f}")
    print(f"Cross-model IDR mean:  {mean_cross:.4f}" if mean_cross else "N/A")
    print(f"Delta:                 {mean_delta:+.4f}" if mean_delta else "N/A")
    print(f"Bias material:         {output['bias_material']}")
    print(f"\nSaved to {out_path}")


def load_json(path):
    with open(path) as f:
        return json.load(f)


if __name__ == "__main__":
    main()
