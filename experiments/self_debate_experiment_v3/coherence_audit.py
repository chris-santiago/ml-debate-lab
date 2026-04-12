# coherence_audit.py
# /// script
# requires-python = ">=3.10"
# ///
import json, re, sys

errors = []

with open('sensitivity_analysis_results.json') as f:
    sens = json.load(f)
with open('stats_results.json') as f:
    stats = json.load(f)
with open('v3_results.json') as f:
    v3 = json.load(f)

computed_corrected_lift = sens['corrected_lift']['corrected_lift_isolated_DC05_DRQ_uncapped']
computed_raw_lift = sens['corrected_lift']['raw_lift_isolated_vs_baseline']
computed_isolated_mean = stats['bootstrap_cis']['isolated_debate_mean']['point']
computed_multiround_mean = stats['bootstrap_cis']['multiround_mean']['point']
computed_ensemble_mean = stats['bootstrap_cis']['ensemble_mean']['point']
computed_baseline_mean = stats['bootstrap_cis']['baseline_mean']['point']

def extract_floats(text, pattern):
    return [float(m) for m in re.findall(pattern, text)]

with open('CONCLUSIONS.md') as f:
    conclusions = f.read()

# Check isolated_debate benchmark mean — look for the summary line specifically
iso_line = re.search(r'Isolated debate mean.*?(\d\.\d{3,4})', conclusions)
if iso_line:
    val = float(iso_line.group(1))
    if abs(val - computed_isolated_mean) > 0.005:
        errors.append(f'CONCLUSIONS.md isolated_debate mean mismatch: found {val}, expected ~{computed_isolated_mean}')

with open('SENSITIVITY_ANALYSIS.md') as f:
    sensitivity = f.read()

corrected_mentions = extract_floats(sensitivity, r'corrected.*?([+-]?\d+\.\d{3,4})')
if corrected_mentions:
    mismatch = [v for v in corrected_mentions if abs(abs(v) - abs(computed_corrected_lift)) > 0.01]
    if mismatch:
        errors.append(f'SENSITIVITY_ANALYSIS.md corrected lift mismatch: found {mismatch}, expected ~{computed_corrected_lift}')

v3_pass_count = v3['debate_pass_count']
# Look specifically for "XX/49" pass count in the main benchmark section
pass_match = re.search(r'(\d+)/49\s*\(.*?pass', conclusions, re.IGNORECASE)
if pass_match:
    reported = int(pass_match.group(1))
    if reported != v3_pass_count:
        errors.append(f'Pass count mismatch: CONCLUSIONS says {reported}/49, v3_results says {v3_pass_count}/49')

if errors:
    print('COHERENCE AUDIT FAILED:')
    for e in errors:
        print(f'  {e}')
    print('\nFix these before drafting REPORT.md.')
    sys.exit(1)
else:
    print(f'Pre-report coherence audit passed — key numerical figures consistent across CONCLUSIONS.md and SENSITIVITY_ANALYSIS.md')
    print(f'  Note: full ml-lab Step 12 checks (claim consistency, README currency, peer review resolution) run in Phase 9.5')

import os
if os.path.exists('external_stats_summary.json'):
    with open('external_stats_summary.json') as f:
        ext_stats = json.load(f)
    published_iso = ext_stats.get('published_paper', {}).get('isolated_mean')
    if published_iso is not None and conclusions:
        ext_mentions = re.findall(r'published.paper.*?(\d+\.\d{3,4})', conclusions, re.IGNORECASE)
        bad_ext = [v for v in [float(m) for m in ext_mentions] if abs(v - published_iso) > 0.01]
        if bad_ext:
            print(f'  WARN: External published_paper mean in CONCLUSIONS ({bad_ext}) differs from computed ({published_iso:.4f})')
