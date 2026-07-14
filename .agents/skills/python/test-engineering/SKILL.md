---
name: Test Engineering & QA
description: Technical implementation of Pytest, Fixtures, State-Aware Integration Tests, and Contract Tests.
---

# Test Engineering Standards

## 1. Test Pyramid Enforcement
- **Unit Tests** must form the majority (~70%) of the test suite. They test pure logic in isolation with mocked dependencies.
- **Integration Tests** (~20%) test boundaries between components (e.g., API → database, validator → DLQ).
- **End-to-End Tests** (~10%) test the full user-facing flow. 

## 2. State-Aware Integration Tests (Mandatory for I/O)
- Any module that reads or writes persistent files (JSON, DB, Parquet) MUST have at least one integration test that operates on pre-populated fixture data matching the REAL production schema.
- Create test fixtures in `tests/fixtures/` containing representative samples of real production data.
- At minimum, assert: `len(after) >= len(before)` for all append operations.

## 3. Fixture & Setup Standards
- Shared fixtures must be defined using `conftest.py`.
- Database tests must use in-memory instances (e.g., DuckDB `:memory:`).
- External API dependencies must be mocked.

## 4. Test Execution Protocol
- Tests must be run after **every** code change.
- Use the framework-appropriate test command (e.g., `pytest src/tests/ -v`).

## 5. Contract Tests for Data Schemas
- Every Pydantic model or `TypedDict` used for file I/O MUST have a corresponding contract test that validates a known-good fixture file against the model.
- Test file: `tests/test_contracts.py`

## 6. Failure Handling
- If a test fails, check `.agents/workflows/error-observability.md` for historical context.
- Fix the **implementation code**, rather than weakening the test.
- After 3 failed debugging iterations on the same test, flag it for manual user review.

## 7. Anti-Solipsism Verification (Human Testing)
- Explicitly provide the human user with the exact, step-by-step UI and CLI testing commands required to run and test the full-stack system locally upon completion of any task.
