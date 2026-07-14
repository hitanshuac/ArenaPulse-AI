---
name: langgraph-orchestrator
description: "Instructs the agent to scaffold production-grade LangGraph state machines with typed state, checkpointing, human-in-the-loop interrupt nodes, and conditional routing. Encodes industry anti-patterns to prevent over-engineering and runaway loops. TRIGGERS: 'build a langgraph agent', 'create a state machine', 'loop engineering', 'agentic workflow', 'orchestrate agents with langgraph', 'build a react agent with langgraph'."
---

# LangGraph Orchestrator Skill

This skill instructs the IDE copilot to scaffold a production-grade LangGraph state machine. It encodes the canonical patterns from `langchain-ai/react-agent` (783★) and the 2026 industry best practices for loop engineering, while preventing the most common pitfalls that cause production failures.

> **Post-Mortem Origin:** This skill was created after an LLM Council analysis identified that enterprise AI agentic engineering roles require demonstrated proficiency with LangGraph. The anti-patterns encoded here are sourced from production failure analyses across the LangGraph ecosystem in 2025-2026.

---

## Anti-Patterns (MUST Avoid)

### 1. The "Graph Trap" (Over-Engineering)
- **What it is:** Reaching for `StateGraph` on day one for simple RAG or linear pipelines.
- **Rule:** ONLY use LangGraph when the workflow requires **cyclic flows**, **persistent state**, or **multi-agent orchestration**. For simple chains, use `LangChain`'s `create_react_agent` or plain function composition.
- **Test:** If your graph has zero cycles and zero conditional edges, you do NOT need LangGraph.

### 2. The "Mega-Agent" Anti-Pattern
- **What it is:** Creating a single agent node that handles reasoning, tool calling, AND structured output formatting in one prompt.
- **Rule:** Split cognitive tasks into specialized nodes with clear contracts. One node reasons. Another calls tools. Another formats output.

### 3. Improper Checkpoint Growth
- **What it is:** Letting the checkpoint database grow unbounded in production.
- **Rule:** Treat checkpoints as operational logs. Implement a background pruning job that keeps only the last N checkpoints per `thread_id`.

### 4. Missing Error Boundaries
- **What it is:** Assuming LLM calls always succeed. No retry logic, no max iteration limits.
- **Rule:** Every graph MUST have a `max_iterations` guard. Every tool-calling node MUST have a try/except with a fallback path.

### 5. Subgraph Checkpoint Duplication
- **What it is:** Configuring checkpointers at both parent and subgraph levels.
- **Rule:** Configure the checkpointer **ONLY at the parent graph level**. Subgraphs inherit it.

---

## Scaffolding Instructions

When the user asks to build a LangGraph agent, follow this exact sequence:

### Step 1: Define Typed State
```python
from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[list, add_messages]
    # Add ONLY fields that need to persist across nodes.
    # Do NOT dump transient data into state.
```

**Rule:** Use `TypedDict` or `Pydantic BaseModel`. Keep state minimal. Every field MUST justify its existence.

### Step 2: Define Nodes as Pure Functions
```python
def reasoning_node(state: AgentState) -> dict:
    """Return a PARTIAL state update. Do NOT mutate the input."""
    response = model.invoke(state["messages"])
    return {"messages": [response]}

def tool_node(state: AgentState) -> dict:
    """Execute tools. Return results as messages."""
    # ... tool execution logic
    return {"messages": [tool_result]}
```

**Rule:** Nodes MUST be pure functions. Return partial updates, never mutate state directly.

### Step 3: Build the Graph with Conditional Routing
```python
from langgraph.graph import StateGraph, END

graph = StateGraph(AgentState)
graph.add_node("reason", reasoning_node)
graph.add_node("tools", tool_node)

# Conditional edge: if the model wants to call a tool, route to tools node
graph.add_conditional_edges(
    "reason",
    should_continue,  # Returns "tools" or "end"
    {"tools": "tools", "end": END}
)
graph.add_edge("tools", "reason")  # After tools, go back to reasoning
graph.set_entry_point("reason")
```

### Step 4: Configure Checkpointing (Environment-Appropriate)
```python
# Development/Testing:
from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()

# Single-Instance Production:
# from langgraph.checkpoint.sqlite import SqliteSaver
# checkpointer = SqliteSaver.from_conn_string("checkpoints.db")

# Distributed Production:
# from langgraph.checkpoint.postgres import PostgresSaver
# checkpointer = PostgresSaver.from_conn_string(os.environ["DATABASE_URL"])

app = graph.compile(checkpointer=checkpointer)
```

### Step 5: Add Human-in-the-Loop (For High-Stakes Decisions)
```python
from langgraph.types import interrupt

def sensitive_action_node(state: AgentState) -> dict:
    """Pause execution and ask for human approval."""
    action = extract_action(state)
    human_response = interrupt(
        {"action": action, "message": "Approve this action?"}
    )
    if human_response["approved"]:
        return execute_action(action)
    return {"messages": [AIMessage(content="Action cancelled by human.")]}
```

### Step 6: Add Max Iteration Guard
```python
MAX_ITERATIONS = 15

def should_continue(state: AgentState) -> str:
    if len(state["messages"]) > MAX_ITERATIONS * 2:
        return "end"  # Force termination
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "tools"
    return "end"
```

---

## Required Dependencies
```
langgraph>=0.2.0
langchain-core>=0.3.0
```

## Reference Implementations
- `langchain-ai/react-agent` — Official LangGraph ReAct template (783★)
- `NicholasGoh/fastapi-mcp-langgraph-template` — Full-stack MCP + LangGraph (548★)
