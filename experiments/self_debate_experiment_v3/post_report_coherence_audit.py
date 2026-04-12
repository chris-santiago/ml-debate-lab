# post_report_coherence_audit.py
# /// script
# requires-python = ">=3.10"
# ///
# Full ml-lab Step 12 coherence audit — runs after REPORT.md and peer review are complete.
# Covers 5 checks not covered by Phase 8.5's numerical pre-report audit.
import json, re, sys
from pathlib import Path

errors = []
warnings = []

# --- Check 1: Claim consistency across CONCLUSIONS, REPORT, ENSEMBLE_ANALYSIS ---
docs = {}
for fname in ['CONCLUSIONS.md', 'REPORT.md', 'ENSEMBLE_ANALYSIS.md']:
    p = Path(fname)
    if p.exists():
        docs[fname] = p.read_text()
    else:
        errors.append(f'Missing required document: {fname}')

if len(docs) == 3:
    def extract_lifts(text):
        return [float(m) for m in re.findall(r'(?:lift|improvement).*?([+-]?\d+\.\d{3,4})', text, re.IGNORECASE)]

    lifts_c = extract_lifts(docs.get('CONCLUSIONS.md', ''))
    lifts_r = extract_lifts(docs.get('REPORT.md', ''))
    if lifts_c and lifts_r:
        max_c = max(abs(x) for x in lifts_c)
        max_r = max(abs(x) for x in lifts_r)
        if abs(max_c - max_r) > 0.01:
            errors.append(f'Headline lift inconsistency: CONCLUSIONS max={max_c:.4f}, REPORT max={max_r:.4f}')

# --- Check 2: README currency ---
readme = Path('README.md')
if readme.exists():
    readme_text = readme.read_text()
    if 'v3' not in readme_text.lower() and 'version 3' not in readme_text.lower():
        warnings.append('README.md does not mention v3 experiment — may be stale')
    if 'CONCLUSIONS' not in readme_text and 'REPORT' not in readme_text:
        warnings.append('README.md does not reference CONCLUSIONS.md or REPORT.md — artifact links may be missing')
else:
    errors.append('README.md missing — required artifact')

# --- Check 3: Peer review resolution ---
for pr_file in ['PEER_REVIEW.md', 'PEER_REVIEW_R1.md']:
    pr = Path(pr_file)
    if pr.exists():
        pr_text = pr.read_text()
        if '## Response' not in pr_text:
            errors.append(f'{pr_file}: missing ## Response section — peer review findings not addressed')
        major_unresolved = re.findall(r'(?:MAJOR|major issue).*?(?:unresolved|not addressed|still open)', pr_text, re.IGNORECASE)
        if major_unresolved:
            errors.append(f'{pr_file}: {len(major_unresolved)} potentially unresolved MAJOR issues — review manually')
        break

# --- Check 4: Hypothesis closure ---
for fname in ['CONCLUSIONS.md', 'REPORT.md', 'FINAL_SYNTHESIS.md']:
    doc = Path(fname)
    if not doc.exists():
        errors.append(f'{fname} missing — cannot verify hypothesis closure')
        continue
    text = doc.read_text()
    has_verdict = any(kw in text.lower() for kw in [
        'hypothesis', 'primary hypothesis', 'verdict', 'supported', 'rejected',
        'confirmed', 'not supported'
    ])
    if not has_verdict:
        errors.append(f'{fname}: no hypothesis verdict found — hypothesis closure incomplete')

# --- Check 5: Full quantitative re-check across REPORT.md ---
with open('stats_results.json') as f:
    stats = json.load(f)
with open('v3_results.json') as f:
    v3 = json.load(f)

report_text = docs.get('REPORT.md', '')
if report_text:
    iso_mean = stats['bootstrap_cis']['isolated_debate_mean']['point']
    # Look for the table row pattern: "| isolated_debate | 0.XXXX |"
    iso_table = re.search(r'isolated_debate\s*\|\s*(\d\.\d{3,4})', report_text, re.IGNORECASE)
    if iso_table:
        val = float(iso_table.group(1))
        if abs(val - iso_mean) > 0.005:
            errors.append(f'REPORT.md: isolated_debate mean mismatch — table says {val}, authoritative={iso_mean:.4f}')

    pass_count = v3.get('debate_pass_count', 0)
    pass_mentions = re.findall(r'(\d+)/49.*?pass', report_text)
    if pass_mentions:
        reported = int(pass_mentions[0])
        if reported != pass_count:
            errors.append(f'REPORT.md: pass count mismatch — says {reported}/49, v3_results says {pass_count}/49')

# --- Output ---
if errors or warnings:
    if errors:
        print('POST-REPORT COHERENCE AUDIT FAILED:')
        for e in errors:
            print(f'  ERROR: {e}')
    if warnings:
        print('Warnings (non-blocking):')
        for w in warnings:
            print(f'  WARN: {w}')
    if errors:
        print('\nFix all errors before proceeding to Phase 9.75.')
        sys.exit(1)
else:
    print('Post-report coherence audit passed — all 5 cross-document checks clean.')
    print('Combined with Phase 8.5, full ml-lab Step 12 coherence audit complete.')

import os
if os.path.exists('external_stats_summary.json'):
    with open('external_stats_summary.json') as f:
        ext_stats = json.load(f)
    published_iso = ext_stats.get('published_paper', {}).get('isolated_mean')
    if published_iso is not None and report_text:
        ext_mentions = re.findall(r'published.paper.*?(\d+\.\d{3,4})', report_text, re.IGNORECASE)
        bad_ext = [v for v in [float(m) for m in ext_mentions] if abs(v - published_iso) > 0.01]
        if bad_ext:
            print(f'  WARN: External published_paper mean in REPORT ({bad_ext}) differs from computed ({published_iso:.4f})')
