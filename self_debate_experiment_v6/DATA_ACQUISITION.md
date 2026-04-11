# v6 Data Acquisition — RC Reports as Ground Truth

## Motivation

v3/v5 cross-experiment analysis revealed that the planted-corruption benchmark measures
**corruption detection**, not methodology review — the protocol's actual use case. v3's
+0.341 raw lift was largely measurement artifact (structural penalties on DC/DRQ); the
corrected fair-comparison lift was +0.0913, driven almost entirely by ETD — the one
dimension requiring genuine open-ended judgment. v5 removed ETD by design (no mixed cases)
and the fair-comparison lift collapsed to +0.0113.

The validity gap: planted corruptions are known-legible bugs with exact ground truth, whereas
real methodology review involves arguable, implicit, or combinatorial flaws where adversarial
debate structure should add the most value. v6 replaces the synthetic corruption pipeline
with **ML Reproducibility Challenge (RC) reports** — post-hoc documented flaws from an
independent reproducer who did not know the answer in advance.

---

## Sources

### Source 1: OpenReview API — RC submissions (primary)

RC challenge reports are submitted to OpenReview. No authentication required.

**Estimated yield:** 40–100 usable cases with specific documented methodology flaws
across 2020–2023 editions.

```python
import requests

def fetch_rc_submissions(venue_year: str):
    """e.g. venue_year = 'ML_Reproducibility_Challenge/2022'"""
    resp = requests.get(
        "https://api.openreview.net/notes",
        params={"invitation": f"{venue_year}/Paper/Submission", "limit": 1000}
    )
    submissions = resp.json()['notes']

    for s in submissions:
        reviews = requests.get(
            "https://api.openreview.net/notes",
            params={"forum": s['id'], "invitation": f"{venue_year}/Paper/Review"}
        )
        s['reviews'] = reviews.json().get('notes', [])

    return submissions

# Run for all available editions
venues = [
    "ML_Reproducibility_Challenge/2020",
    "ML_Reproducibility_Challenge/2021",
    "ML_Reproducibility_Challenge/2022",
    "ML_Reproducibility_Challenge/2023",
]
```

Each submission record contains: `title`, `abstract`, `pdf` (URL), and linked review notes
with the full report text.

---

### Source 2: ReScience C — curated published reports (gold standard)

The highest-quality subset (~10/year that passed editorial review). The entire journal is
a public GitHub repo. These are the cases with clearest, most specific flaw documentation.

```bash
git clone https://github.com/ReScience/RESCIENCE-C.git
# Each published paper: articles/<vol>/<issue>/article.md + YAML front matter
find articles -name "article.md"
```

**Estimated yield:** 30–40 cases. Use as the primary test set.

---

### Source 3: Papers with Code data dump (supplementary)

A JSON release artifact on their GitHub covering the broader challenge pool. No API needed.

- Repo: `https://github.com/paperswithcode/papers-with-code-data`
- Download the latest release JSON
- Less structured than OpenReview; use for case discovery, not ground truth

---

## Extraction Pipeline

Raw report text → LLM extraction pass → structured `planted_issues` equivalent

The reproducer's "what failed" section is extracted into the same schema used in v5,
replacing the synthetic corruption step. The rest of the evaluation pipeline
(`self_debate_poc.py`, scoring, stats) is reused unchanged.

### Target schema per extracted flaw

```json
{
  "issue_id": "rc_flaw_001",
  "flaw_type": "...",
  "description": "...",
  "severity": "high | moderate | low",
  "source": "reproducer",
  "ground_truth_type": "post_hoc_documented",
  "rc_report_id": "...",
  "original_paper_title": "..."
}
```

### Extraction prompt (draft)

```
You are extracting structured methodology flaw records from an ML reproducibility report.

REPORT TEXT:
{report_text}

Identify every specific methodology flaw the reproducer documented — issues that prevented
replication or revealed a gap between the paper's claims and its experimental setup.
For each flaw, output:
- flaw_type: one of [data_leakage, evaluation_mismatch, baseline_broken,
  distribution_shift, metric_mismatch, hyperparameter_tuning, scope_overclaim, other]
- description: one paragraph, specific enough that an independent reviewer could check
  whether a methodology critique raised this concern
- severity: high / moderate / low (based on reproducer's framing)
- reproducible: true if the flaw was confirmed to affect results, false if only suspected

Return a JSON array. If no specific methodology flaw is documented, return [].
```

---

## Filtering Criteria

Not all RC reports yield usable benchmark cases. Filter out:

| Exclusion criterion | Reason |
|---|---|
| "Results didn't match" with no root cause | Not a methodology flaw — could be environment/randomness |
| Environment/compute failures only | Not a design flaw |
| Flaw description < 2 sentences | Too vague to use as ground truth |
| Original paper not publicly accessible | Can't construct task_prompt |
| Flaw is purely implementation bug in released code | Tests code review, not methodology review |

**Target**: cases where the reproducer identified a flaw in the *experimental design* —
something that would be visible in a methodology description, not just in the code.

---

## Comparison to v5 Pipeline

| Step | v5 | v6 |
|---|---|---|
| Case source | Synthetic LLM-generated designs | Real RC-reported papers |
| Flaw insertion | Corruption pipeline plants known bugs | Reproducer documents flaw post-hoc |
| Ground truth origin | Known in advance (by construction) | Discovered post-publication |
| IDR scoring target | Planted issue description | Extracted flaw description |
| Benchmark validity | Corruption detection | Methodology review recall |
| ETD applicability | N/A (no mixed cases) | TBD — depends on case composition |

---

## Open Questions for v6 Design

1. **Scoring**: IDR measures whether the debate finds the documented flaw. But the reproducer
   may have found only one of several real flaws. Do we score recall against documented flaws
   only, or also reward novel valid concerns the debate surfaces that the reproducer missed?

2. **Case difficulty calibration**: RC reports span a wide range of flaw subtlety. The
   proxy_mean filter from v5 doesn't apply directly — need a new difficulty proxy (e.g.,
   number of reproducibility challenge participants who caught the same flaw).

3. **Mixed cases**: RC reports sometimes document "paper is mostly sound but X is
   overstated" — these are the mixed cases v5 lacked. ETD becomes applicable again.

4. **OpenReview as validation stratum**: If annotation effort is available, the broader
   OpenReview peer review pool (~5,000–18,000 usable cases after filtering) can serve as
   a larger development/validation set alongside the RC gold standard test set.
