---
name: verify-citations
description: >
  Audits LaTeX bibliography files to prove all citations are real, correctly attributed, and
  have no hallucinated authors or titles. Invoke this skill whenever the user asks to verify,
  check, audit, or prove citations — phrases like "verify citations", "check my bib",
  "audit references", "prove citations aren't hallucinated", "are my citations correct",
  "check my references.bib". Also invoke after any edit to a .bib file, or before submitting
  a paper. Two-part check: (1) structural key audit per venue, (2) live arXiv fetch to verify
  title and authors for every entry with an arxiv.org URL.
---

Two-part audit: structural key check, then live arXiv verification.

---

## Step 1 — Discover venues

Find all `main.tex` files under the paper root (default: `paper/`). For each, locate the
corresponding `.bib` file in the same directory. Each `tex/bib` pair is one **venue**.

```bash
find paper/ -name "main.tex"
```

State the venues found before proceeding.

---

## Step 2 — Structural key check (Python, not grep)

**Important:** macOS ships BSD grep with no `-P` flag. Always use Python for extraction.

Run `scripts/extract_keys.py` with the repo root as argument:

```bash
python3 .claude/skills/verify-citations/scripts/extract_keys.py paper/
```

The script prints a JSON report. For each venue it shows:
- `cited` — keys used in the `.tex`
- `defined` — keys defined in the `.bib`
- `missing` — cited but not in bib (will render `[?]` in PDF — **critical**)
- `orphaned` — in bib but never cited (harmless, flag for hygiene)

Report the counts and list any missing or orphaned keys.

---

## Step 3 — Extract arXiv entries from bib

Parse each `.bib` to collect every entry whose `url` field contains `arxiv.org`. For each,
capture:
- The cite key (e.g. `smit2024mad`)
- The arXiv ID (numeric part of URL, e.g. `2311.17371`)
- The `title` field as written in the bib
- The `author` field as written in the bib

Build the list across all venues, deduplicating by cite key (shared bib files will produce
duplicates).

---

## Step 4 — Fetch all arXiv pages in parallel

Issue all WebFetch calls **in a single message** — do not fetch sequentially.

For each entry, fetch `https://arxiv.org/abs/<arXiv-ID>` with the prompt:

> "Return the exact paper title and complete author list, preserving original spelling and order."

Fetching all at once is essential — 20+ sequential fetches would be extremely slow.

---

## Step 5 — Compare and report

For each entry compare the fetched data against the bib:

**Title check:** flag if the words differ (ignore capitalisation differences like title-case
vs. sentence-case — these are stylistic).

**Author check:** flag any of:
- Different first name or spelling
- Missing or extra authors
- Swapped author order (this affects rendered citations)
- `Anonymous` in the bib (placeholder from blind review — flag for update)

Output format:

```
★ STRUCTURAL CHECK
─────────────────
[emnlp2026]  21 cited / 21 defined  →  0 missing, 0 orphaned
[neurips2026] 12 cited / 21 defined  →  0 missing, 9 orphaned (unused, harmless)
[arxiv]      21 cited / 21 defined  →  0 missing, 0 orphaned

Missing keys : NONE
Orphaned keys: deepreview2025, irving2018debate, ... (neurips only)

★ ARXIV VERIFICATION  (21 entries)
────────────────────
✓  chan2024chateval    2308.07201  title ✓  authors ✓
✗  choi2025debate     2508.17536  AUTHORS WRONG
     bib:   Choi, Hannah K. / Zhu, Xiangyu / Li, Shuai
     arxiv: Choi, Hyeong Kyu / Zhu, Xiaojin / Li, Sharon
...

Result: 19/21 verified clean. 2 mismatches. Apply corrections? (y/n)
```

If mismatches are found, offer to apply corrections to all affected `.bib` files immediately.

---

## Notes

- arXiv abstract pages are author-submitted and are the canonical source for author names
- Author order matters — swapped co-authors render incorrectly in any citation style that
  abbreviates after the first author
- Missing middle initials (e.g. `Eric Xing` vs `Eric P. Xing`) are worth correcting
- If a bib file is shared across venues, apply fixes once and they propagate automatically
