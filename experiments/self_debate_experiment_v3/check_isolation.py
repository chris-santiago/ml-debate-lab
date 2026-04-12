# check_isolation.py
# /// script
# requires-python = ">=3.10"
# ///
# Scans all defender_raw outputs from isolated_debate runs to detect isolation breaches.
# A breach means the Defender saw Critic content before forming its position.
# Note: multiround runs are NOT checked — the Defender intentionally sees the Critique there.
import json
from pathlib import Path

raw_dir = Path('v3_raw_outputs')
breaches = []

for path in sorted(raw_dir.glob('*_isolated_debate_run*.json')):
    with open(path) as f:
        run = json.load(f)
    defender_raw = run.get('defender_raw', '')
    critic_raw = run.get('critic_raw', '')

    # Extract first substantive Critic claim (first numbered issue or first sentence after "Issue")
    # and check if it appears verbatim in Defender output
    import re
    critic_claims = re.findall(r'(?:Issue \d+|^\d+\.)[^\n]+', critic_raw, re.MULTILINE)
    for claim in critic_claims[:3]:  # check first 3 critic claims
        snippet = claim.strip()[:60]
        if len(snippet) > 20 and snippet.lower() in defender_raw.lower():
            breaches.append({
                'file': str(path),
                'case_id': run['case_id'],
                'run': run['run'],
                'matched_snippet': snippet
            })
            break  # one breach per file is enough

if breaches:
    print(f'ISOLATION BREACHES DETECTED: {len(breaches)}')
    for b in breaches:
        print(f'  {b["file"]}: matched "{b["matched_snippet"]}"')
    raise SystemExit('Fix isolation breaches before scoring — results are contaminated')
else:
    print(f'Isolation check passed — {len(list(raw_dir.glob("*_isolated_debate_run*.json")))} isolated debate runs clean')
