#!/bin/bash
# sync-plugin-cache.sh
# PostToolUse hook: syncs plugin source to Claude Code cache after any edit.
# Also warns on version mismatches across plugin.json and marketplace.json.
# Fires on Edit or Write tool calls; no-ops for unrelated files.

REPO_ROOT="/Users/chrissantiago/Dropbox/GitHub/ml-debate-lab"
PLUGINS_JSON="$HOME/.claude/plugins/installed_plugins.json"

# Read tool input from stdin and extract file_path
FILE_PATH=$(python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    print(d.get('tool_input', {}).get('file_path', ''))
except Exception:
    print('')
")

# Resolve installPath from Claude Code's plugin registry — no hardcoded versions
get_install_path() {
    python3 -c "
import json, sys
try:
    with open('$PLUGINS_JSON') as f:
        d = json.load(f)
    entries = d.get('plugins', {}).get('$1', [])
    print(entries[0].get('installPath', '') if entries else '')
except Exception:
    print('')
"
}

# Warn if plugin.json and marketplace.json versions are out of sync
check_versions() {
    python3 -c "
import json

market_path = '$REPO_ROOT/.claude-plugin/marketplace.json'
plugins = [
    ('ml-lab',     '$REPO_ROOT/plugins/ml-lab/.claude-plugin/plugin.json'),
    ('ml-journal', '$REPO_ROOT/plugins/ml-journal/.claude-plugin/plugin.json'),
]

try:
    with open(market_path) as f:
        market = json.load(f)
    market_versions = {p['name']: p['version'] for p in market.get('plugins', [])}
except Exception as e:
    print(f'WARNING: Could not read marketplace.json: {e}')
    raise SystemExit(0)

mismatches = []
for name, path in plugins:
    try:
        with open(path) as f:
            pv = json.load(f).get('version', '?')
        mv = market_versions.get(name, '?')
        if pv != mv:
            mismatches.append(f'  {name}: plugin.json={pv}  marketplace.json={mv}')
    except Exception as e:
        mismatches.append(f'  {name}: could not read plugin.json ({e})')

if mismatches:
    print('VERSION MISMATCH — update marketplace.json to match plugin.json (or vice versa):')
    for m in mismatches:
        print(m)
"
}

# Sync cache
case "$FILE_PATH" in
  *plugins/ml-journal/*)
    DEST=$(get_install_path "ml-journal@ml-debate-lab")
    [ -n "$DEST" ] && rsync -a --exclude='.orphaned_at' \
      "$REPO_ROOT/plugins/ml-journal/" "$DEST/"
    ;;
  *plugins/ml-lab/*)
    DEST=$(get_install_path "ml-lab@ml-debate-lab")
    [ -n "$DEST" ] && rsync -a --exclude='.orphaned_at' \
      "$REPO_ROOT/plugins/ml-lab/" "$DEST/"
    ;;
esac

# Version check — only when a version-bearing file is touched
case "$FILE_PATH" in
  *plugins/*/.claude-plugin/plugin.json|*.claude-plugin/marketplace.json)
    check_versions
    ;;
esac
