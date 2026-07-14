---
name: multi-agent-crew
description: "Instructs the agent to build multi-agent teams with strict role contracts, typed output schemas, and hard-fail delegation. Encodes the God Orchestrator, silent compensation, and context contamination anti-patterns from 2025-2026 production failures. TRIGGERS: 'build a multi-agent system', 'create an agent crew', 'multi-agent orchestration', 'agent delegation', 'build a team of agents', 'researcher analyzer writer pattern'."
---

# Multi-Agent Crew Skill

This skill instructs the IDE copilot to scaffold production-grade multi-agent systems. It encodes patterns from `oh-my-claudecode` (37.4k★), OpenAI `Swarm` (21.7k★), and the 2026 industry failure analysis across CrewAI, AutoGen, and LangGraph multi-agent deployments.

> **Post-Mortem Origin:** Industry analysis shows that 10 agents create 45 potential interaction failure points. Exponential coordination costs are the #1 killer of multi-agent systems. This skill enforces minimal agent counts and strict contracts.

---

## Anti-Patterns (MUST Avoid)

### 1. The "God Orchestrator"
- **What it is:** A single orchestrator agent with a 3,000+ token system prompt that manages all sub-agents.
- **Rule:** The orchestrator MUST be a lightweight router with a system prompt under 500 tokens. Its ONLY job is to classify the task and delegate to the correct specialist.

### 2. The "Premature Orchestrator" (Complexity Bias)
- **What it is:** Implementing multi-agent before it is needed. Most workflows are better served by simple, deterministic DAGs.
- **Rule:** You MUST justify multi-agent orchestration with this test: "Does this task require DIFFERENT reasoning strategies applied by DIFFERENT specialists?" If a single agent with tools can do it, do NOT use multi-agent.

### 3. Silent Compensation
- **What it is:** A downstream agent quietly "fixes" or infers data to cover for mistakes made by an upstream agent. This masks errors.
- **Rule:** Agents MUST hard-fail when receiving incomplete or malformed input. NEVER infer missing data. Return a structured error that halts the pipeline.

### 4. Context Contamination (Memory Bleed)
- **What it is:** Agents having access to raw, un-sanitized context from all preceding steps. Causes hallucinations and weakened constraints.
- **Rule:** Each agent receives ONLY its typed input contract. No raw message history from other agents. Use explicit handoff schemas.

### 5. Ambiguous Role Definitions
- **What it is:** Overlapping responsibilities between agents causing role confusion.
- **Rule:** Every agent MUST have a single, typed output schema. If two agents can produce the same output type, they are redundant. Merge them.

---

## Scaffolding Instructions

When the user asks to build a multi-agent system, follow this exact sequence:

### Step 1: Define the Agent Roster (Maximum 3-5 Agents)
```python
AGENT_ROSTER = {
    "researcher": {
        "role": "Find and summarize relevant information",
        "input_schema": ResearchRequest,   # Pydantic model
        "output_schema": ResearchReport,   # Pydantic model
        "tools": ["web_search", "document_reader"],
        "max_iterations": 5,
    },
    "analyzer": {
        "role": "Evaluate data and identify patterns",
        "input_schema": ResearchReport,
        "output_schema": AnalysisReport,
        "tools": ["calculator", "chart_generator"],
        "max_iterations": 3,
    },
    "writer": {
        "role": "Produce final deliverable from analysis",
        "input_schema": AnalysisReport,
        "output_schema": FinalDocument,
        "tools": ["markdown_formatter"],
        "max_iterations": 2,
    },
}
```

**Rule:** The roster MUST be defined BEFORE writing any agent code. Every agent MUST have explicit input/output Pydantic schemas.

### Step 2: Define Typed Handoff Contracts
```python
from pydantic import BaseModel, Field

class ResearchRequest(BaseModel):
    query: str = Field(..., description="The research question")
    scope: str = Field(..., description="Boundaries for the research")
    max_sources: int = Field(default=5)

class ResearchReport(BaseModel):
    findings: list[str] = Field(..., min_length=1)
    sources: list[str] = Field(..., min_length=1)
    confidence: float = Field(..., ge=0.0, le=1.0)
    gaps: list[str] = Field(default_factory=list)

class AnalysisReport(BaseModel):
    patterns: list[str] = Field(..., min_length=1)
    recommendations: list[str] = Field(..., min_length=1)
    risk_factors: list[str] = Field(default_factory=list)
```

**Rule:** Contracts are enforced at the transport layer. If an agent returns prose instead of the expected schema, the system MUST reject it and retry (up to 3 times), then hard-fail.

### Step 3: Build the Lightweight Orchestrator
```python
class Orchestrator:
    """Lightweight router. Under 500 tokens system prompt."""

    def route(self, task: str) -> str:
        """Classify task and return the first agent to invoke."""
        # Use structured output to force classification
        classification = model.with_structured_output(TaskClassification).invoke(
            f"Classify this task into one of: research, analysis, writing. Task: {task}"
        )
        return classification.agent_name

    def execute_pipeline(self, task: str) -> FinalDocument:
        """Execute the agent pipeline with hard-fail on schema violations."""
        research = self.run_agent("researcher", ResearchRequest(query=task, scope="general"))
        if not isinstance(research, ResearchReport):
            raise AgentOutputError("Researcher failed schema validation")

        analysis = self.run_agent("analyzer", research)
        if not isinstance(analysis, AnalysisReport):
            raise AgentOutputError("Analyzer failed schema validation")

        return self.run_agent("writer", analysis)
```

### Step 4: Implement Hard-Fail Error Handling
```python
class AgentOutputError(Exception):
    """Raised when an agent's output fails schema validation."""
    pass

def run_agent(self, agent_name: str, input_data: BaseModel) -> BaseModel:
    """Run an agent with strict output validation."""
    agent_config = AGENT_ROSTER[agent_name]
    for attempt in range(3):  # Max 3 retries
        try:
            result = agent.invoke(input_data)
            validated = agent_config["output_schema"].model_validate(result)
            return validated
        except ValidationError as e:
            if attempt == 2:
                raise AgentOutputError(
                    f"Agent '{agent_name}' failed after 3 attempts: {e}"
                )
    # NEVER silently compensate. NEVER infer missing data.
```

### Step 5: Add Observability
```python
import logging

logger = logging.getLogger("multi_agent")

def run_agent_with_trace(self, agent_name: str, input_data: BaseModel) -> BaseModel:
    logger.info(f"[{agent_name}] Starting with input: {input_data.model_dump_json()}")
    result = self.run_agent(agent_name, input_data)
    logger.info(f"[{agent_name}] Output: {result.model_dump_json()}")
    return result
```

---

## Framework Selection Guide

| Scenario | Recommended Framework | Why |
|:---|:---|:---|
| Role-based business workflows | CrewAI | Easiest delegation model |
| Reasoning-heavy conversational | AutoGen | Native conversation patterns |
| Deterministic enterprise production | LangGraph | Full control, typed state, checkpointing |
| Simple linear pipeline | Plain Python | Do NOT use multi-agent |

---

## Required Dependencies
```
pydantic>=2.0
langchain-core>=0.3.0
```

## Reference Implementations
- `Yeachan-Heo/oh-my-claudecode` — Multi-agent orchestration for Claude Code (37.4k★)
- `openai/swarm` — Educational multi-agent framework (21.7k★)
- `kyegomez/swarms` — Enterprise multi-agent framework (6.9k★)
