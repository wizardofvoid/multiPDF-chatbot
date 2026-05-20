# Architecture

**Analysis Date:** 2026-05-20

## Pattern Overview

**Overall:** RAG (Retrieval-Augmented Generation) Pipeline — CLI Application

**Key Characteristics:**
- Batch pipeline: extract → chunk → embed → query
- Stateless between runs (rebuilds index on PDF changes)
- Single-threaded sequential execution
- No web server, no database — purely file-based

## Layers

**Extraction Layer:**
- Purpose: Convert PDF documents to plain text
- Contains: PDF parsing (PyMuPDF), OCR processing (Tesseract), image extraction
- Location: `extract_text.py`
- Depends on: File system (inputPDF/, output/)
- Used by: Pipeline orchestrator (main.py via et.main())

**Chunking & Embedding Layer:**
- Purpose: Split text into searchable chunks, generate vector embeddings, persist to FAISS
- Contains: Token-aware text splitting, Gemini embedding, FAISS save/load
- Location: `text_chunker.py`
- Depends on: Extraction layer output, Google Gemini API, FAISS
- Used by: Pipeline orchestrator (main.py via tc.main())

**Query & Generation Layer:**
- Purpose: Accept user questions, retrieve relevant context, generate answers
- Contains: Similarity search, prompt construction, LLM invocation, conversation memory
- Location: `main.py`
- Depends on: FAISS index, Groq API, LangChain runnables

## Data Flow

**Pipeline Execution (startup):**

1. `main()` called
2. `et.main()` — Check for PDF updates, extract text and OCR from PDFs
3. If changes detected or index missing: `tc.main()` — Chunk text, generate embeddings, save FAISS index
4. `FAISS.load_local()` — Load existing vectorstore
5. Enter REPL loop

**Query Flow (per user question):**

1. User enters question via stdin
2. `vectorstore.similarity_search(question, k=3)` — Retrieve top-3 relevant chunks
3. Join retrieved chunks as context string
4. `chain_with_history.invoke({input, context})` — Prompt LLM with context + question + history
5. Print response to stdout
6. Loop until "exit"

**State Management:**
- Persistent state: FAISS index on disk (`faiss_index/`)
- Session state: `InMemoryChatMessageHistory` per session (lost on restart)
- Conversation memory: `ConversationSummaryBufferMemory` instantiated but not wired (dead code)

## Key Abstractions

**LangChain Chain:**
- Purpose: Composable prompt → LLM → output parser pipeline
- Example: `prompt | llm | StrOutputParser()`
- Pattern: LangChain pipe operator (`|`)

**Vectorstore:**
- Purpose: Semantic search over document chunks
- Example: `FAISS` with Gemini embeddings
- Pattern: load_local / similarity_search

**Chat History:**
- Purpose: Per-session conversation state
- Example: `InMemoryChatMessageHistory` in `store` dict
- Pattern: Keyed by session_id

## Entry Points

**Main Entry:**
- Location: `main.py`
- Triggers: `python main.py`
- Responsibilities: Orchestrate pipeline, run REPL loop

**Extraction Entry:**
- Location: `extract_text.py`
- Triggers: Called from `main()`
- Responsibilities: Extract text from PDFs via PyMuPDF + Tesseract

**Chunking Entry:**
- Location: `text_chunker.py`
- Triggers: Called from `main()` when index needs rebuild
- Responsibilities: Split, embed, persist

## Error Handling

**Strategy:** Print error messages to stdout, return `False` or `None` on failure

**Patterns:**
- Print `[ERROR]` prefixed messages
- Return boolean (`changes_made`) or `None` from functions
- No exception propagation to top level (caught locally)
- No retry logic for API calls

## Cross-Cutting Concerns

**Logging:**
- Print-based logging with `[INFO]`, `[ERROR]`, `[WARNING]`, `[SUCCESS]` prefixes
- No structured logging library

**Configuration:**
- Hardcoded constants at module level in each `.py` file
- `.env` for API keys only (not for paths or settings)
- No config file or CLI arguments

**File I/O:**
- Pathlib for path handling
- UTF-8 encoding for text files
- Binary for image/PDF I/O

---

*Architecture analysis: 2026-05-20*
*Update when major patterns change*
