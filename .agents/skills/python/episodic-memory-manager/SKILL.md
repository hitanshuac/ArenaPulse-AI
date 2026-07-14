---
name: episodic-memory-manager
description: Instructs the agent to integrate Episodic Memory (Mem0/Zep) for cross-session state, explicitly segregating it from RAG document retrieval.
---

# Episodic Memory Manager

Enterprise agents must remember user preferences, past conversational outcomes, and identity across sessions. This is **Episodic Memory**. It is fundamentally different from RAG (Semantic Knowledge).

## Core Rules

1. **Strict Segregation:** Never mix document chunks (RAG) with user conversation history (Episodic) in the same vector namespace.
2. **Identity Mapping:** Every memory write must be keyed by `user_id` and `session_id`.
3. **Graph Memory (Optional):** When requested, use Graph-based memory (e.g., Mem0's graph capabilities) to extract entities (e.g., "User likes Python").
4. **Memory Injection:** Inject episodic memories into the `system_prompt` before the LLM call, not as mocked user messages.

## Implementation Pattern (Mem0)

```python
from mem0 import Memory

# 1. Initialize strictly for Episodic Storage
episodic_memory = Memory()

def store_preference(user_id: str, preference: str):
    # 2. Key by Identity
    episodic_memory.add(preference, user_id=user_id, metadata={"type": "preference"})

def get_context(user_id: str, query: str):
    # 3. Retrieve and inject into System Prompt
    memories = episodic_memory.search(query, user_id=user_id)
    return "\\n".join([m["text"] for m in memories])
```

**Anti-Pattern:** Storing the entire chat history in a massive array and feeding it into the LLM context window until it exceeds the token limit (The "Stuffed Context" anti-pattern). Episodic memory must be actively retrieved and summarized.
