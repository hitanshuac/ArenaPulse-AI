# Council Advisors - Dead Code Workflow Refinement

## Framed Question
The user noted that the newly created `dead-code-cleanup.md` workflow is 'barebones' and lacks true structure, relying primarily on rudimentary `grep_search` for finding dead code and unused dependencies. The user requested using `git-discovery-preflight` to find deterministic tools that can work in tandem with the LLM. We found `jendrikseipp/vulture` (finds dead Python code) and `hadialqattan/pycln` (removes unused imports). How should we structurally update the `dead-code-cleanup.md` workflow to integrate these AST-based, deterministic static analysis tools as a 'pre-flight' before the LLM takes over, creating a truly robust and structured garbage collection pipeline?

## The Contrarian
You cannot blindly trust `vulture` or `pycln` any more than you can trust an LLM. `vulture` notoriously flags dynamic attributes, ORM fields, and magic methods as "dead code" because AST analysis cannot resolve runtime bindings. If you just pipe the output of `vulture` directly into a `Remove-Item` loop, you will instantly break the application. The LLM must not be replaced by these tools; it must act as the *adjudicator* of these tools. The workflow shouldn't be "run vulture and delete what it finds." It must be "run vulture, feed the whitelist/blacklist to the LLM, let the LLM use `grep_search` to double-check the tool's findings, and only *then* propose deletion."

## The First Principles Thinker
What is the fundamental flaw with `grep_search`? It has no semantic understanding of Python. It searches strings, not syntax. An Abstract Syntax Tree (AST) parser understands syntax. Therefore, deterministic tools are objectively superior for the *discovery* phase. The structure of the workflow should follow a classic Map-Reduce pattern. 
1. **Map (Discovery):** Run `vulture` and `pycln --check`. Collect all flagged dead code and imports into a report.
2. **Reduce (Validation):** The LLM reviews the report, cross-references against `grep_search` to catch edge cases (like string-based references in config files), and reduces it to a final confirmed list of deletions.
3. **Execute:** Delete with human approval.

## The Expansionist
Why stop at just `vulture` and `pycln`? If we are restructuring this workflow to be a deterministic static analysis pipeline, we should include `deptry` for orphaned dependencies in `pyproject.toml` or `requirements.txt`. The workflow can become the ultimate "Codebase Detox" protocol. The structure should define specific "Scanners" (Vulture for dead logic, Pycln for imports, Deptry for packages) that run sequentially and output JSON. The LLM then consumes that JSON, applies context-aware filtering, and outputs an `implementation_plan.md` that is mathematically flawless.

## The Outsider
The user said the workflow was "barebones" and lacked structure. Right now, it's just a bulleted list of "do this, do that." A real workflow file should look like a pipeline with strict inputs and outputs. You need XML tags or strict Markdown sections defining exactly what CLI command to run (e.g., `pip install vulture pycln`, then `vulture src/`), where to pipe the output, and how the LLM should parse it. Give the workflow actual executable skeleton code. That's what the user means by "structure".

## The Executor
Here is the concrete path forward. We update `dead-code-cleanup.md` to integrate the discovered tools. 
Phase 1: Bootstrapping. The agent must `pip install vulture pycln deptry` (or use `uv`). 
Phase 2: Deterministic Scan. The agent runs `vulture . --min-confidence 80`, `pycln . --check`, and dependency checks. 
Phase 3: LLM Adjudication. The agent parses the tool outputs and cross-checks with `grep_search`. 
Phase 4: The implementation plan and human approval gate (already exists).
This directly satisfies the `git-discovery-preflight` directive by integrating GitHub tools, and fixes the "barebones" complaint by providing an exact toolchain.
