---
name: prompt-registry-sync
description: Instructs the agent to externalize all LLM prompts to markdown files, treating them as versionable assets rather than hardcoded Python strings.
---

# Prompt Asset Management

Enterprise AI requires prompts to be managed as configuration assets, allowing non-engineers to tweak them and enabling A/B testing without code deployments.

## Core Rules

1. **No Hardcoded Prompts:** Never define a multi-line prompt string inside a `.py` file (e.g., `PROMPT = \"\"\" You are an AI... \"\"\"`).
2. **File-Based Assets:** Store all prompts in a dedicated `prompts/` or `assets/prompts/` directory as `.md` or `.txt` files.
3. **Template Variables:** Use explicit curly braces `{var_name}` inside the prompt files for runtime formatting via `string.format()` or LangChain's `PromptTemplate`.
4. **Validation:** On startup, the system must load and validate that the required template variables are present in the loaded text file.

## Implementation Pattern

```python
import os
from pathlib import Path

def load_prompt(prompt_name: str) -> str:
    """Loads a prompt from the central registry."""
    prompt_path = Path(f"prompts/{prompt_name}.md")
    if not prompt_path.exists():
        raise FileNotFoundError(f"Missing prompt asset: {prompt_name}")
    return prompt_path.read_text(encoding="utf-8")

# Usage
system_prompt = load_prompt("researcher_v2")
formatted_prompt = system_prompt.format(user_query="How does MCP work?")
```

**Anti-Pattern:** Hardcoding a massive system prompt inside `agent.py`. This leads to massive pull requests just to fix a typo in the AI's instructions and prevents dynamic A/B testing of prompt variations.
