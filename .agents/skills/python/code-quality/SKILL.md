---
name: Enterprise Code Quality Standards
description: Technical implementation of SAST compliance, PyLint, Flake8, Ruff, and structural AI evaluator passing.
---

# Enterprise Code Quality Standards

This skill codifies the strict requirements for achieving a perfect maintainability and reliability score against automated SAST and AI Code Analyzers (e.g., SonarQube, DeepSource).

## 1. Project Structure & Imports (Pylint/Flake8 Compliance)
- Ensure every package directory (`src/`, subdirectories, `tests/`) has an `__init__.py` file.
- Rely on `pyproject.toml` or `conftest.py` for path resolution rather than `sys.path.append()`.
- All imports must be at the top of the file, ordered: stdlib -> third-party -> local (isort standard).

## 2. Formatting & Cleanliness
- **Zero trailing whitespace** in any file.
- Exactly **2 blank lines** between top-level function/class definitions.
- Maximum line length of **120 characters**.
- No blank line at the end of the file (W391), just a single newline.

## 3. Strict Linting Requirements
- **No broad exceptions**: Replace `except Exception as e:` with specific exceptions like `except (ValueError, ConnectionError):`.
- **No inline imports**: Ensure imports are always at the module level.
- **No mutable defaults**: Change `def func(arg: dict = None):` to `def func(arg: Optional[dict] = None):`.
- **No pointless re-raises**: Avoid using `raise e` inside an except block without adding context.
- **Zero Hacks**: Fix the underlying AST violation natively rather than using `# pylint: disable` or `# noqa` suppression comments.

## 4. Cyclomatic Complexity (Radon CC = A-Grade)
- If a function exceeds CC=5, extract branching logic into private helper functions.
- **Pre-compile regex patterns** (`re.compile`) at the module level rather than inside functions.
- Extract magic numbers and strings into uppercase module constants.
- Keep functions under 25 lines of core logic.

## 5. Documentation & Typing
- Include a module-level docstring at the top of every `.py` file.
- Use **Google-style docstrings** with explicit `Args:`, `Returns:`, and `Raises:` sections.
- Add explicit type hints on every parameter and return value.
- Void functions must explicitly declare `-> None`.

## 6. Ruff Formatting Standards
- Target Python Version: 3.11+
- Rules Enforced: `E`, `F`, `I`, `UP`, `RUF`.
- All code must pass `ruff check .` and `ruff format --check .` locally before pushing.

## 7. Pre-Push Verification Commands
```bash
pylint src/ --fail-under=9.5
flake8 src/ tests/ --max-line-length=120 --count
radon cc src/ -a -s -n B   # Output must be empty
radon mi src/ -s           # All must be 'A'
pytest tests/ -v           # All must pass
```
