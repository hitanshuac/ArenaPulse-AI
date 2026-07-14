---
name: hitl-interrupts
description: Instructs the agent to compile LangGraph workflows with strict Human-in-the-Loop (HITL) checkpoints for any infrastructure-mutating actions.
---

# Human-in-the-Loop (HITL) RBAC Gates

Agentic execution loops (like LangGraph) can run infinitely and mutate production state. Enterprise SOP dictates that destructive actions must halt and await human approval.

## Core Rules

1. **Explicit Breakpoints:** Use `interrupt_before` or `interrupt_after` in the LangGraph `compile()` step for any node that performs a mutating action (e.g., `execute_sql`, `deploy_code`, `send_email`).
2. **State Persistence:** You MUST use a checkpointer (e.g., `MemorySaver` or Postgres) when using interrupts. A graph cannot pause without saving its state.
3. **Resumption Logic:** Provide clear instructions on how the human operator injects the approval (or modification) back into the graph to resume execution.

## Implementation Pattern (LangGraph)

```python
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

def human_approval_node(state):
    # This node does nothing; it acts as a gate.
    return state

def execute_destructive_action(state):
    # Performs the actual action
    return state

graph = StateGraph(AgentState)
graph.add_node("human_approval", human_approval_node)
graph.add_node("execute_action", execute_destructive_action)

graph.add_edge("human_approval", "execute_action")

# 1. State must be saved to allow pausing
checkpointer = MemorySaver()

# 2. Compile with an explicit interrupt BEFORE the approval node
app = graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["human_approval"]
)

# 3. Execution will halt here. A human must call app.stream(None, thread_config) to resume.
```

**Anti-Pattern:** Building an autonomous agent that can directly drop a database table or send an email without a human checkpoint. This violates basic enterprise Role-Based Access Control (RBAC).
