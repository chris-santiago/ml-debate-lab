# Presentations

Slide decks covering different aspects of the ml-lab ecosystem.

## Available decks

### Evaluation Overview

High-level overview of the adversarial debate evaluation methodology, including the experiment arc and key results.

**Source:** `slides/evaluation-overview.md`

### ml-journal System

Architecture and workflow of the ml-journal audit trail system — the four-layer design, entry types, chain patterns, and synthesis ladder.

**Source:** `slides/ml-journal-overview.md`

### Plugin Architecture

Technical overview of the Claude Code plugin structure — agents, skills, dispatch patterns, and the plugin cache sync system.

**Source:** `slides/plugin-overview.md`

## Format

All slides are written in [Marp](https://marp.app/) markdown and compiled to PDF. Supporting diagrams are in `slides/diagrams/`.

To rebuild a deck:

```bash
marp slides/<deck-name>.md -o slides/<deck-name>.pdf
```
