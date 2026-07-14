---
trigger: glob
glob: "src/**/*.py"
---

# Migrated to Skills
All implementation details previously held in this rule file have been migrated to the `.agents/skills/` directory to adhere to the Separation of Concerns.
- DuckDB logic -> `duckdb-optimizer/SKILL.md`
- Data Ingestion logic -> `universal-ingestion/SKILL.md`
- Context Compaction -> `context-compactor/SKILL.md`
