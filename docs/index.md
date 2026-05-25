# ml-lab

A Claude Code plugin that runs structured ML hypothesis investigations using an adversarial critic-defender debate protocol or an independent ensemble of critics. It enforces rigor at every step — pre-specified metrics, confidence-tiered review findings, agreed experiments only — and produces a self-contained report with a production re-evaluation.

## When to use ml-lab

Use ml-lab when you have a falsifiable ML hypothesis and want a structured process to test it. The plugin handles the full lifecycle: sharpening the hypothesis, building a minimal proof-of-concept, adversarial review (or ensemble sweep), pre-registered experiments, and synthesis of conclusions. It is designed for rigor over speed.

## Quick start

```shell
# Install the plugin
/plugin marketplace add chris-santiago/ml-lab
/plugin install ml-lab@ml-lab

# Start an investigation
/ml-lab
```

## Where to go next

<div class="grid cards" markdown>

-   :material-school: **Tutorials**

    ---

    Get started with ml-lab — from installation to running your first investigation.

    [:octicons-arrow-right-24: Tutorials](tutorials/index.md)

-   :material-clipboard-list: **How-to Guides**

    ---

    Step-by-step instructions for specific tasks: running investigations, logging decisions, querying the journal.

    [:octicons-arrow-right-24: How-to Guides](how-to/index.md)

-   :material-book-open-variant: **Reference**

    ---

    Complete reference for agents, skills, entry types, scripts, and configuration.

    [:octicons-arrow-right-24: Reference](reference/index.md)

-   :material-lightbulb: **Explanation**

    ---

    Understand why ml-lab works the way it does — the debate protocol, evaluation methodology, and lessons learned.

    [:octicons-arrow-right-24: Explanation](explanation/index.md)

-   :material-flask: **Research**

    ---

    The experiments behind ml-lab — eight versions of self-evaluation, the working paper, and related work.

    [:octicons-arrow-right-24: Research](research/index.md)

</div>
