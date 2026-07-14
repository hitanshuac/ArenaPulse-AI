---
name: Defensive Programming Standards
description: Technical implementation of schema validation, fast failing, and idempotency for file I/O operations.
---

# Defensive Programming Standards

This skill codifies senior-engineer defensive programming SOPs that prevent silent data loss, schema drift, and error obfuscation.

## 1. Schema-First Data Contracts (Mandatory for All I/O)
- Define a Pydantic model or `TypedDict` at module level for every persistent data structure.
- The Pydantic model is the **single source of truth**. If the existing file does not match the model, the code must raise a descriptive `ValueError` or `SchemaError` and halt. 
- When Pydantic is unavailable, use Python `TypedDict` with explicit runtime validation using `assert`.

### Example (Correct):
```python
from pydantic import BaseModel

class ErrorLogEntry(BaseModel):
    timestamp: str
    error_type: str
    component: str
    message: str
    status: str  # "UNRESOLVED" | "RESOLVED"

# Module-level schema
ErrorLogSchema = list[ErrorLogEntry]
```

## 2. Fail Fast
- Every `except` block MUST log `type(e).__name__` and `str(e)` to the observability layer BEFORE returning any user-facing message.
- Replace bare `except:` and `except Exception:` with specific exception types.

### Example (Correct):
```python
except google.api_core.exceptions.ResourceExhausted as e:
    log_error_to_json("ResourceExhausted", "llm_engine", str(e))
    return fallback_message
```

## 3. Idempotent File Operations
- For JSON append operations: Read the file, deserialize, validate the schema, append the new entry, serialize, and write back atomically.
- Use atomic write patterns where possible: write to a `.tmp` file first, then rename to the production path.

## 4. Guard Clauses and Input Validation at Boundaries
- Every public function must validate its inputs in the first 3 lines using guard clauses.
- Invalid inputs must raise `ValueError` or `TypeError` with a descriptive message.

### Example (Correct):
```python
def log_error_to_json(error_type: str, component: str, message: str) -> bool:
    if not error_type or not isinstance(error_type, str):
        raise ValueError(f"error_type must be a non-empty string, got: {error_type!r}")
    # ... proceed with validated inputs
```
