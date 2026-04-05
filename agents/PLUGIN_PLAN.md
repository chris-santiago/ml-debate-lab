# claude-ml-lab — Plugin Distribution Plan

**Plugin name:** `claude-ml-lab`
**Marketplace name:** `ml-debate-lab`
**Scope:** All six agents — ml-lab, ml-critic, ml-defender, research-reviewer, research-reviewer-lite, readme-rewriter. All six are runtime dependencies of ml-lab (Steps 3–5, 10, 13) and must be installed together.
**Distribution:** Claude Code native plugin system via `marketplace.json` hosted in this GitHub repo

---

## How it works

Claude Code has a built-in plugin system. A **marketplace** is a git repo containing a `.claude-plugin/marketplace.json` catalog. Users add your marketplace once, then install individual plugins from it. Claude Code handles all file management natively — no custom install scripts needed.

This repo is both the plugin source and the marketplace.

---

## What users get after install

```
~/.claude/agents/
  ml-lab.md
  ml-critic.md
  ml-defender.md

~/.claude/agent-memory/ml-lab/
  MEMORY.md   (created by ml-lab on first investigation run)
```

Claude Code picks up the agents automatically. Users invoke the workflow by describing an ML hypothesis — Claude Code routes to `ml-lab` via the description field.

---

## Repository layout (new files only)

```
ml-debate-lab/
├── agents/
│   ├── ml-lab.md
│   ├── ml-critic.md
│   ├── ml-defender.md
│   ├── research-reviewer.md
│   ├── research-reviewer-lite.md
│   ├── readme-rewriter.md
│   └── ...
└── .claude-plugin/
    ├── plugin.json              (plugin manifest)
    └── marketplace.json         (marketplace catalog)
```

No `plugin/` directory. No Node.js. No npm publish step. The repo itself is the distribution artifact.

---

## ~~Step 1 — `.claude-plugin/plugin.json`~~ ✓ DONE

**File exists at `.claude-plugin/plugin.json`.** The plugin manifest declares what gets installed.

```json
{
  "name": "claude-ml-lab",
  "description": "Structured ML hypothesis investigation for Claude Code — adversarial critique, empirical testing, peer review, coherence audit, and README rewrite.",
  "version": "1.4.0",
  "license": "MIT",
  "agents": [
    "./agents/ml-lab.md",
    "./agents/ml-critic.md",
    "./agents/ml-defender.md",
    "./agents/research-reviewer.md",
    "./agents/research-reviewer-lite.md",
    "./agents/readme-rewriter.md"
  ]
}
```

The `agents` paths are relative to the plugin root (the repo root, which is also where `.claude-plugin/` lives). Claude Code copies these files to `~/.claude/agents/` on install.

---

## ~~Step 2 — `.claude-plugin/marketplace.json`~~ ✓ DONE

**File exists at `.claude-plugin/marketplace.json`.** The marketplace catalog lists the plugin and where to find it. Since the plugin lives in the same repo as the marketplace, `source` is `"./"`.

```json
{
  "name": "ml-debate-lab",
  "owner": {
    "name": "chris-santiago"
  },
  "metadata": {
    "description": "ML hypothesis investigation agents for Claude Code"
  },
  "plugins": [
    {
      "name": "claude-ml-lab",
      "source": "./",
      "description": "Structured ML hypothesis investigation — adversarial critique, empirical testing, peer review, coherence audit, and README rewrite.",
      "version": "1.4.0",
      "license": "MIT",
      "keywords": ["ml", "hypothesis-testing", "agents", "research"]
    }
  ]
}
```

---

## Step 3 — User install

```shell
# In Claude Code:
/plugin marketplace add chris-santiago/ml-debate-lab
/plugin install claude-ml-lab@ml-debate-lab
```

Or from the CLI:

```bash
claude plugin marketplace add chris-santiago/ml-debate-lab
claude plugin install claude-ml-lab@ml-debate-lab
```

---

## Step 4 — Uninstall

```shell
/plugin uninstall claude-ml-lab@ml-debate-lab
```

Agent memory at `~/.claude/agent-memory/ml-lab/` is NOT removed. Delete it manually to clear investigation history.

---

## Step 5 — Version management

When agent files change:

1. Update the relevant `.md` file(s) in `agents/` (source of truth)
2. Bump version in `.claude-plugin/plugin.json` (semver: patch for prompt tweaks, minor for new modes, new steps, or new agents, major for protocol changes — e.g., adding a new step = minor bump)
3. Push to GitHub

Users update by running:

```shell
/plugin marketplace update ml-debate-lab
/plugin install claude-ml-lab@ml-debate-lab
```

No publish step. No npm. The git push is the release.

---

## Testing and CI

**Official support is limited.** The docs document two mechanisms:

**`--plugin-dir` flag (recommended for local testing)**
Load the plugin from a local path without installing it — nothing touches `~/.claude/agents/`, no cleanup required:
```bash
claude --plugin-dir /path/to/ml-debate-lab
```
Use `/reload-plugins` inside the session to pick up file changes without restarting. This is the safest way to run the checklist smoke tests — fully isolated, no side effects.

**`claude plugin validate .` (suitable for CI)**
Validates JSON syntax, schema, and frontmatter across all plugin files. Non-interactive, so it can run in a GitHub Actions workflow:
```yaml
- name: Validate plugin
  run: claude plugin validate .
```

**What does not exist (as of April 2026):**
- No official GitHub Action for plugin testing or validation
- No documented isolated sandbox or container approach
- No CI/CD workflow templates for plugins

The `claude-code-action` GitHub Action (`anthropics/claude-code-action@v1`) exists but is for running Claude in PR/issue workflows — not for plugin testing.

**Minimal CI recommendation:** A GitHub Actions workflow that runs `claude plugin validate .` on every push covers what is formally supported. For deeper smoke testing (agent dispatch, subagent invocation), use `--plugin-dir` locally before each release.

---

## A note on npm

npm is supported as a plugin *source type* within a marketplace entry (alongside `github`, `url`, `git-subdir`). It is NOT a replacement for the marketplace mechanism — the user-facing install is always `/plugin install`, regardless of the underlying source. Publishing to npm could be useful for private registries or enterprise deployments, but adds no benefit for a public GitHub-hosted plugin. The git-based approach here is simpler and gets automatic update propagation via `/plugin marketplace update`.

---

## Pre-publish checklist

- [x] `.claude-plugin/plugin.json` created with correct paths and version
- [x] `.claude-plugin/marketplace.json` created with correct plugin entry
- [ ] `claude plugin validate .` run from repo root — no errors
- [ ] Smoke test via `--plugin-dir` (no install, fully isolated): `claude --plugin-dir .` — verify ml-lab is available and asks to sharpen the hypothesis
- [ ] Verify subagent dispatch via `--plugin-dir`: confirm ml-lab can invoke ml-critic/ml-defender (Steps 3–5), research-reviewer (Step 10 R1), research-reviewer-lite (Step 10 R2–3), readme-rewriter (Step 13)
- [ ] Install test: `/plugin marketplace add ./` then `/plugin install claude-ml-lab@ml-debate-lab` — verify all six agent files appear in `~/.claude/agents/`
- [ ] Push to GitHub
- [ ] Test from a clean machine: `/plugin marketplace add chris-santiago/ml-debate-lab` then `/plugin install claude-ml-lab@ml-debate-lab`
- [ ] Confirm `agents/README.md` shows plugin install as the primary path (already done)

---

## What does NOT change

- Agent file contents — all six `.md` files are used as-is
- Memory system spec inside `ml-lab.md` — kept fully embedded; ml-lab creates `~/.claude/agent-memory/ml-lab/MEMORY.md` on first investigation run
- Subagent dispatch design — all agents except ml-lab are internal subagents; only ml-lab is user-facing
- Experiment artifacts, reports, and analysis — not referenced by plugin.json, not installed
