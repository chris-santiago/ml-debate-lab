#!/usr/bin/env python3
"""
extract_keys.py — structural citation key audit for LaTeX projects.

Usage:
    python3 extract_keys.py [paper_root]

Walks paper_root (default: paper/) looking for main.tex / references.bib pairs.
For each venue, computes:
  - cited:    keys used via \\cite{}, \\citet{}, \\citep{} in main.tex
  - defined:  keys declared in references.bib
  - missing:  cited but not defined  (renders [?] in PDF — critical)
  - orphaned: defined but never cited (harmless, hygiene flag)

Outputs JSON to stdout.
"""

import json
import re
import sys
from pathlib import Path


def get_cited_keys(tex_path: Path) -> set[str]:
    text = tex_path.read_text(encoding="utf-8")
    groups = re.findall(r'\\cite[tp]?\{([^}]+)\}', text)
    keys: set[str] = set()
    for group in groups:
        for k in group.split(","):
            keys.add(k.strip())
    return keys


def get_bib_keys(bib_path: Path) -> set[str]:
    text = bib_path.read_text(encoding="utf-8")
    return set(re.findall(r'^@\w+\{(\w+),', text, re.MULTILINE))


def get_arxiv_entries(bib_path: Path) -> list[dict]:
    """Return list of {key, arxiv_id, title, author} for entries with arxiv URLs."""
    text = bib_path.read_text(encoding="utf-8")
    # Split into individual entries
    entries = re.split(r'\n(?=@)', text)
    results = []
    for entry in entries:
        # Get cite key
        key_match = re.match(r'@\w+\{(\w+),', entry)
        if not key_match:
            continue
        key = key_match.group(1)

        # Check for arxiv URL
        url_match = re.search(r'url\s*=\s*\{([^}]*arxiv\.org[^}]*)\}', entry, re.IGNORECASE)
        if not url_match:
            continue
        url = url_match.group(1)
        arxiv_id_match = re.search(r'arxiv\.org/abs/([^\s}]+)', url, re.IGNORECASE)
        if not arxiv_id_match:
            continue
        arxiv_id = arxiv_id_match.group(1)

        # Extract title and author from bib entry
        title_match = re.search(r'title\s*=\s*\{((?:[^{}]|\{[^{}]*\})*)\}', entry, re.IGNORECASE)
        author_match = re.search(r'author\s*=\s*\{([^}]+)\}', entry, re.IGNORECASE)

        results.append({
            "key": key,
            "arxiv_id": arxiv_id,
            "url": url,
            "bib_title": title_match.group(1).strip() if title_match else "",
            "bib_authors": author_match.group(1).strip() if author_match else "",
        })
    return results


def audit_venue(tex_path: Path, bib_path: Path) -> dict:
    cited = get_cited_keys(tex_path)
    defined = get_bib_keys(bib_path)
    missing = sorted(cited - defined)
    orphaned = sorted(defined - cited)
    return {
        "venue": tex_path.parent.name,
        "tex": str(tex_path),
        "bib": str(bib_path),
        "cited_count": len(cited),
        "defined_count": len(defined),
        "missing": missing,
        "orphaned": orphaned,
        "ok": len(missing) == 0,
    }


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("paper")
    if not root.exists():
        print(json.dumps({"error": f"Directory not found: {root}"}))
        sys.exit(1)

    venues = []
    arxiv_entries: dict[str, dict] = {}  # deduplicated by cite key

    for tex_path in sorted(root.rglob("main.tex")):
        bib_path = tex_path.parent / "references.bib"
        if not bib_path.exists():
            # Try any .bib in same directory
            bibs = list(tex_path.parent.glob("*.bib"))
            if not bibs:
                continue
            bib_path = bibs[0]

        venues.append(audit_venue(tex_path, bib_path))

        for entry in get_arxiv_entries(bib_path):
            arxiv_entries[entry["key"]] = entry  # last write wins (identical across shared bibs)

    output = {
        "venues": venues,
        "arxiv_entries": list(arxiv_entries.values()),
        "summary": {
            "total_venues": len(venues),
            "venues_with_missing_keys": [v["venue"] for v in venues if v["missing"]],
            "total_arxiv_entries": len(arxiv_entries),
        },
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
