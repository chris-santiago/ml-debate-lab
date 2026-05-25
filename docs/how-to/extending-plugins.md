# Add an Agent or Skill

## Adding a new agent

Create a markdown file in `plugins/ml-lab/agents/`:

```
plugins/ml-lab/agents/my-agent.md
```

The file should define:

1. **Name and description** — frontmatter that Claude Code uses for dispatch
2. **Persona** — who the agent is and what perspective it brings
3. **Instructions** — what the agent does when dispatched
4. **Output format** — what artifacts the agent produces

The agent is dispatched via the `Agent` tool from the main session (or from a skill). It runs as a subagent with isolated context.

!!! note "Plugin cache sync"
    A PostToolUse hook (`sync-plugin-cache.sh`) automatically rsyncs edits in `plugins/ml-lab/` to the versioned plugin cache. No manual reinstall needed after editing.

## Adding a new skill

Create a directory in `plugins/ml-lab/skills/` with a `SKILL.md` file:

```
plugins/ml-lab/skills/my-skill/SKILL.md
```

The `SKILL.md` file defines:

1. **Frontmatter** — `name`, `description` (used for routing), and optional `model`
2. **Instructions** — the step-by-step workflow the skill executes
3. **Scripts** — any supporting scripts go in `skills/my-skill/scripts/`

Once the plugin cache syncs, the skill is available as `/my-skill`.

## Registering in the plugin manifest

If adding to the ml-lab plugin, update the plugin manifest at:

```
plugins/ml-lab/.claude-plugin/plugin.json
```

Agents are auto-discovered from `agents/`; skills are auto-discovered from `skills/`. The manifest registers the plugin with Claude Code's plugin system.

## Testing

1. Edit the agent or skill file
2. Wait for the sync hook to fire (or manually reinstall)
3. Invoke the skill or dispatch the agent
4. Verify output matches expectations

## You have now...

Added a new agent or skill to the ml-lab plugin and verified it works through the plugin cache sync system.
