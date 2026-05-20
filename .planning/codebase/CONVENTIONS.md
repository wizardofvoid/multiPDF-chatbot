# Coding Conventions

**Analysis Date:** 2026-05-20

## Naming Patterns

**Files:**
- `snake_case.py` for all Python modules
- `UPPER_SNAKE_CASE.txt` for output artifacts by convention

**Functions:**
- `snake_case()` for all functions (Python standard)
- `main()` for module entry points
- Descriptive prefixes: `chunk_all_`, `create_and_save_`, `extract_`, `detect_`

**Variables:**
- `snake_case` for all variables
- `UPPER_SNAKE_CASE` for module-level constants (INPUT_DIR, CHUNK_SIZE, LLM_MODEL)
- No Hungarian notation or type prefixes

**Types:**
- No type annotations used anywhere in the codebase
- No MyPy, pyright, or type checking enabled

## Code Style

**Formatting:**
- Standard Python indentation (4 spaces)
- No formatter config detected
- Single and double quotes used inconsistently (both appear in same files)

**Linting:**
- No linter config detected (no `.pylintrc`, `pyproject.toml`, or `ruff.toml`)

## Imports

**Order:**
1. Standard library imports (os, sys, io, Path)
2. Third-party library imports (fitz, pytesseract, langchain_*)
3. Local module imports (text_chunker, extract_text)

**Grouping:**
- Blank line between import groups
- No sorting within groups

**Pattern:**
- `# pyrefly: ignore [missing-import]` comments above third-party imports to suppress a type checker

## Error Handling

**Patterns:**
- Print `[ERROR]` prefixed messages to stdout
- Return sentinel values (`False`, `None`, `[]`) instead of raising exceptions
- Try/except around file I/O and external API calls
- No custom exception classes

**Error Messages:**
- Formatted: `print(f"[ERROR] Failed to X: {e}")`
- Prefix convention: `[ERROR]`, `[WARNING]`, `[INFO]`, `[SUCCESS]`

## Logging

**Framework:**
- `print()` statements with bracket prefixes
- No logging library (no `import logging`)

**Levels (by prefix):**
- `[INFO]` — Normal progress updates
- `[ERROR]` — Failures
- `[WARNING]` — Non-critical issues
- `[SUCCESS]` — Completion confirmations
- `[TEST]` — Test output (in text_chunker.py)

## Comments

**When used:**
- `# ========== SECTION HEADERS ==========` for config/function section breaks
- Brief inline comments explaining non-obvious logic
- Some commented-out code remains

**Not used:**
- No docstrings on any function or module
- No type annotations
- No TODO/FIXME markers

## Function Design

**Size:**
- Functions range from ~10–60 lines
- `main()` functions are orchestration-style (sequence of steps)
- Some functions mix multiple responsibilities

**Parameters:**
- Functions take parameters directly (no options objects or dataclasses)
- Default parameter values used where applicable

**Return Values:**
- Mixed return types: `bool`, `list`, `str`, `None`
- Not consistently typed or documented

---

*Convention analysis: 2026-05-20*
*Update when patterns change*
