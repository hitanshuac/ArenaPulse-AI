---
name: mcp-server-architect
description: Instructs the agent to scaffold custom tools as Model Context Protocol (MCP) servers using the official Python SDK, strictly avoiding raw API wrappers.
---

# Model Context Protocol (MCP) Architect

When instructed to "build a tool", "connect to a database", or "create an integration", you must **NEVER** write a raw Python wrapper class. All external tools must be implemented as Model Context Protocol (MCP) servers.

## Core Rules

1. **Strict SDK Usage:** Use the official `@mcp.tool` decorator from the `mcp` Python package. Do not implement the JSON-RPC protocol manually.
2. **Typed Schemas:** Every MCP tool must use Pydantic models to define its input schema. This prevents malformed calls from the LLM.
3. **Stateless Operations:** MCP tools must be stateless. Do not store connection objects globally; initialize them per request or use a robust connection pool.
4. **Error Boundaries:** Wrap all external calls within the MCP tool in a `try/except` block and return a structured error string. Do not let the MCP server crash.

## Implementation Pattern

```python
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field

# 1. Initialize Server
mcp = FastMCP("Enterprise Tool Server")

# 2. Define Strict Schema
class QuerySchema(BaseModel):
    query_string: str = Field(description="The exact SQL query to run.")

# 3. Expose Tool
@mcp.tool()
def execute_query(input: QuerySchema) -> str:
    """Executes a read-only query against the database."""
    try:
        # Implementation here
        return "Success"
    except Exception as e:
        return f"Tool Execution Failed: {str(e)}"
```

**Anti-Pattern:** Creating a `class DatabaseTool:` and calling it directly from the LangGraph node. This breaks portability and violates enterprise SOP.
