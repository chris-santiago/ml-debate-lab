# Log Decisions & Discoveries

## Log an entry

At any point during a session, run:

```shell
/log-entry
```

ml-journal infers the entry type from conversation context and presents a draft for confirmation.

## Entry types to know

The most common types you'll log during an investigation:

| Type | When to log | Confirm required? |
|------|-------------|-------------------|
| `decision` | User confirms a direction ("let's do X") | Yes |
| `discovery` | Unexpected finding changes understanding | Yes |
| `issue` | Bug or inconsistency identified | No |
| `resolution` | Fix verified working | No |
| `lesson` | Root cause understood | No |
| `experiment` | Verdict is clear (confirmed/refuted/inconclusive) | Yes |

For the complete list, see [Entry Types & Schema](../reference/ml-journal/entry-types.md).

## Chain patterns

Entries chain naturally during a session. ml-journal auto-proposes each step:

**Bug fix chain:**

1. Bug identified → auto-propose `issue`
2. Fix verified → auto-propose `resolution`
3. Root cause understood → auto-propose `lesson`

**Investigation chain:**

1. Hypothesis formed → manual `hypothesis`
2. Experiment run → auto-propose `experiment`
3. Unexpected finding → auto-propose `discovery`
4. Direction confirmed → auto-propose `decision`

## Tips

- Log as events happen, not in a batch at the end
- Accept or decline auto-proposals — ml-journal won't re-propose if you decline
- Use relative dates in conversation; ml-journal converts to absolute timestamps
- Link related entries — resolutions link to issues, experiments link to hypotheses

## You have now...

Learned to log decisions, discoveries, and issues with `/log-entry` and let chain patterns guide the audit trail through natural investigation stages.
