# Agentic Agile-V Process

Agentic Agile-V combines two layers:

1. **Agile-V macro-cycle**: requirements, design, implementation, verification, approval, audit evidence, release.
2. **SCOPE-V micro-cycle**: Specify, Constrain, Orchestrate, Prove, Evolve, Verify.

## Macro-cycle

Each increment should remain traceable from intent to evidence:

```text
Intent -> Requirement -> Design -> Implementation -> Verification -> Evidence -> Approval -> Release
```

## Micro-cycle

### 1. Specify
Convert intent into a clear engineering brief.

### 2. Constrain
Define non-goals, boundaries, compatibility rules, safety limits, and allowed files.

### 3. Orchestrate
Define how the agent will work: inspect, plan, implement, test, summarize, and update evidence.

### 4. Prove
Require tests, checks, logs, screenshots, simulation, HIL, or other evidence.

### 5. Evolve
Update repository instructions, tests, templates, or design notes based on what was learned.

### 6. Verify
Accept output only after risk-appropriate verification and human review.

## Conversation-to-contract gate

Conversation is useful for discovery. It should not be the implementation artifact.

Before implementation, create a brief that contains:

- objective
- scope
- non-goals
- constraints
- affected modules
- acceptance criteria
- test plan
- required evidence
- risk level
- approval rule
