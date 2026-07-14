---
name: telemetry-tracing
description: Instructs the agent to implement LangSmith or OpenTelemetry tracing across all agentic nodes to prevent orphaned spans and ensure full reasoning observability.
---

# Telemetry & Reasoning Tracing

When building LangGraph loops, RAG pipelines, or LLM chains, you must ensure 100% observability of the agent's "reasoning trajectory."

## Core Rules

1. **No Orphaned Spans:** Do not use `logger.info()` to log prompts or LLM outputs. Standard logging loses the conversational graph structure.
2. **Traceable Decorators:** Use `@traceable` (LangSmith) or standard OpenTelemetry spans around **every** node in the LangGraph state machine.
3. **Session Propagation:** You must extract `run_id` or `session_id` from the LangGraph `State` dictionary and explicitly pass it to any asynchronous or external tool calls.
4. **Tagging:** Always tag traces with the agent role (e.g., `tags=["researcher_agent", "v2_prompt"]`) to enable A/B testing evaluation.

## Implementation Pattern

```python
from langsmith import traceable
from typing import TypedDict

class AgentState(TypedDict):
    messages: list
    session_id: str

@traceable(run_type="chain", name="analyzer_node")
def analyze_data(state: AgentState):
    """
    The @traceable decorator ensures the inputs and outputs
    of this node are tied to the broader execution trace.
    """
    session_id = state.get("session_id")
    # Execute LLM call passing the session context
    return {"messages": ["Analysis complete."]}
```

**Anti-Pattern:** Relying on `print()` statements or flat text logs to debug why an agent hallucinated. If you cannot visualize the exact prompt + tool call tree in a UI, the tracing is insufficient.
