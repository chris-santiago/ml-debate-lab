# Related Work

A literature survey covering the research areas that inform ml-lab's design.

!!! note "Source location"
    The full related work survey is maintained at [`RELATED_WORK.md`](https://github.com/chris-santiago/ml-lab/blob/main/RELATED_WORK.md) in the repository root.

## Key areas

### LLM-as-Judge

Using language models as evaluation judges — scoring, ranking, or comparing outputs against rubrics. ml-lab's evaluation uses LLM judges for scoring benchmark cases and relies on multi-judge panels for reliability.

### Multi-Agent Debate

Structured argumentation between LLM agents to improve reasoning quality. ml-lab's critic-defender protocol draws from this literature but applies it specifically to methodology evaluation rather than general reasoning.

### Evaluation Calibration

The problem of ensuring evaluation metrics actually measure what they claim. ml-lab's eight-version experiment arc is largely a calibration story — each version fixed measurement issues discovered in the previous one.

### Pre-registration in ML

Borrowing pre-registration practices from experimental psychology and applying them to ML experimentation. ml-lab enforces pre-registration with automated drift detection.

### Adversarial Testing

Using adversarial probes to find failure modes in ML systems. ml-lab's critic agent is an adversarial tester of methodology rather than model behavior.
