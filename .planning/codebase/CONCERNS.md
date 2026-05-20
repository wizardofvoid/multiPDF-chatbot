# Codebase Concerns

**Analysis Date:** 2026-05-20

## Tech Debt

**Dead memory integration (`main.py:17,77-81`):**
- Issue: `ConversationSummaryBufferMemory` is imported and instantiated but never wired into the chain. `RunnableWithMessageHistory` uses `get_session_history` which returns `InMemoryChatMessageHistory` independently.
- Impact: Summary buffer memory does nothing — session history is unbounded and will grow indefinitely.
- Fix approach: Remove the dead code or wire it properly.

**Dead/broken dependency (`main.py:17`):**
- Issue: `from langchain_classic import ConversationSummaryBufferMemory` imports from `langchain-classic` package which doesn't exist (package name is `langchain-classic` but import might be `langchain_classic` — unclear if this resolves at runtime with the installed version).
- Impact: `import` may fail at runtime, crashing the application.
- Fix approach: Use `from langchain_community.memory import ConversationSummaryBufferMemory` if available, or remove the memory entirely.

**Incorrect embedding model ID (`main.py:33`, `text_chunker.py:21`):**
- Issue: `EMBEDDING_MODEL = "gemini-embedding-2"` — this is not a valid Google Gemini embedding model identifier.
- Impact: Embedding generation may fall back to defaults or fail depending on API version.
- Fix approach: Use correct model ID like `"models/embedding-001"`.

**Inline OCR config (`extract_text.py:19`):**
- Issue: Tesseract path hardcoded to Windows-specific path `C:\Program Files\Tesseract-OCR\tesseract.exe`.
- Impact: Breaks on macOS/Linux without modification.
- Fix approach: Use platform detection or make configurable via env var.

**Test code embedded in production module (`text_chunker.py:114-127`):**
- Issue: Similarity search test is hardcoded in `main()` function with a static query.
- Impact: Runs every time chunking is triggered, polluting output with test results.
- Fix approach: Move to separate test file.

## Known Bugs

**Wrong model string (`main.py:33`):**
- Symptoms: LLM model `openai/gpt-oss-20b` may not be a valid Groq model name.
- Trigger: LLM invocation during chat.
- Root cause: Model name likely copied from incorrect documentation or placeholder.
- Severity: High — may cause runtime failures.

## Security Considerations

**API keys in `.env`:**
- Risk: API keys are stored in plaintext `.env` file in the project directory.
- Current mitigation: `.env` is in `.gitignore` (preventing commit to git).
- Recommendations: Use environment variables or a secrets manager. Verify `.env` is never accidentally committed.

**Hardcoded API keys concern:**
- Risk: If `.env` is ever committed or backed up with the project, API keys are exposed.
- Current mitigation: None beyond `.gitignore`.

## Performance Bottlenecks

**One-at-a-time embedding (`text_chunker.py:80-86`):**
- Problem: Embeddings are generated one chunk at a time in a loop.
- Measurement: ~1 second per chunk for Gemini embedding — scales linearly with chunk count (~100+ chunks = 100+ seconds).
- Cause: Workaround for a reported LangChain Google GenAI batching bug.
- Improvement path: Verify if the upstream bug is fixed and use `embed_documents()` for batch processing.

**No caching:**
- Problem: FAISS index is rebuilt from scratch on any PDF change, even if only one file changed.
- Impact: Unnecessary recomputation for incremental additions.
- Improvement path: Support incremental index updates.

## Fragile Areas

**FAISS deserialization (`main.py:55-59`):**
- Risk: `allow_dangerous_deserialization=True` is required to load the index, which is a security warning from LangChain about pickle-based deserialization.
- Impact: Malicious FAISS file could execute arbitrary code.
- Mitigation: Only loads from local `faiss_index/` directory.

**Pipeline dependency chain:**
- `main.py` calls `et.main()` then `tc.main()` in sequence — if extraction fails, chunking may proceed with stale or empty data.
- No validation of intermediate state between pipeline stages.

## Dependencies at Risk

**langchain-classic 1.0.7:**
- Risk: Not a standard LangChain package — may be a misspelled or private package. The correct import path would be `langchain_community.memory`.
- Impact: Import error at runtime.

**FAISS dangerous deserialization:**
- LangChain's `FAISS.load_local()` requires `allow_dangerous_deserialization=True` since LangChain 0.3+.
- Current fix works but should be noted as a security consideration.

## Missing Critical Features

**No input validation:**
- Problem: User input in `main.py:93` has no validation — empty strings, control characters, or extremely long inputs are not handled.
- Impact: Empty queries waste API calls; malformed input may cause unexpected behavior.

**No error recovery in REPL:**
- Problem: If one LLM call fails, the REPL loop terminates rather than retrying or continuing.
- Impact: Single API failure ends the session.

**No configuration file:**
- Problem: All paths and settings are hardcoded in source files (PDF_PATH, VECTORSTORE_DIR, chunk sizes, model names).
- Impact: Changing any setting requires editing source code.

## Test Coverage Gaps

**Entire codebase:**
- What's not tested: Every module has zero test coverage.
- Risk: Regressions go undetected; refactoring is high-risk.
- Priority: High

---

*Concerns audit: 2026-05-20*
*Update as issues are fixed or new ones discovered*
