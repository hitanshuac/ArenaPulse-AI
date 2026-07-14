---
name: Meta-Agent Formats
description: Output templates for Rules, Proposals, Reviews, and Checkpoints.
---

# Meta-Agent Formats and Templates

## 1. Rule Entry Template
```markdown
### Rule: <RULE_ID>
- Owner layer: Global | Domain | Project
- Scope: [where this rule applies]
- Stability: core | behavior | experimental
- Status: active | superseded | draft
- Directive: [clear imperative rule]
- Rationale: [why this rule exists]
- Conflict handling: [what overrides this rule or when to escalate]
- Example: [positive example]
- Non-example: [what this rule forbids or does not cover]
```

## 2. Deliverable / Proposal Template
```markdown
## Deliverable: [title]
### Proposal
### Alternatives considered
### Pros / Cons
### Risks
### Recommendation
```

## 3. Review / Audit Output Template
```markdown
## Review: [title]
### Findings
### Open questions / assumptions
### Residual risks
### Summary
```

## 4. Execution Checkpoint Template
```markdown
## Checkpoint: [gate name]
**Current state**: 
**Proposal**: 
**Risks**: 
**Decision needed**: 
Waiting for approval before proceeding.
```
