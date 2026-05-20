# Technology Stack

**Analysis Date:** 2026-05-20

## Languages

**Primary:**
- Python 3.x — All application code

## Runtime

**Environment:**
- Python 3.x — Scripts run directly via `python main.py`

**Package Manager:**
- pip — Dependencies listed in `requirements.txt`
- Lockfile: None (`requirements.txt` with loose version pins)

## Frameworks

**Core:**
- LangChain 1.3.1 — RAG pipeline orchestration (chains, prompts, output parsing)
- LangChain Community 0.4.1 — Vectorstore integrations (FAISS)
- LangChain Google GenAI 4.2.2 — Gemini embeddings connector
- LangChain Groq 1.1.2 — Groq API LLM connector
- LangChain Core 1.4.0 — Base abstractions (prompts, chat history, runnables)

**AI/ML:**
- FAISS (CPU) 1.10.0 — Local vector similarity search
- Google Generative AI Embeddings (gemini-embedding-2) — Text embeddings
- ChatGroq (openai/gpt-oss-20b) — LLM for answer generation
- tiktoken 0.9.0 — Token-aware text splitting
- transformers 4.49.0 — HuggingFace transformers (installed but not directly imported)

**Document Processing:**
- PyMuPDF (fitz) 1.25.3 — PDF text extraction
- pytesseract 0.3.13 — OCR for scanned PDF images
- Pillow 11.1.0 — Image processing for OCR

## Key Dependencies

**Critical:**
- langchain-groq — LLM access via Groq API (requires GROQ_API_KEY)
- langchain-google-genai — Embeddings via Google Gemini (requires GOOGLE_API_KEY)
- faiss-cpu — Local vector search index
- PyMuPDF — PDF text extraction
- pytesseract — OCR for scanned/image-based PDFs

**Infrastructure:**
- python-dotenv — Environment variable loading from `.env`
- tiktoken — Token counting for text splitting

## Configuration

**Environment:**
- `.env` file — API keys for Groq and Google Gemini
- `GROQ_API_KEY` — Required for LLM access
- `GOOGLE_API_KEY` — Required for embeddings generation

**No build step** — Pure Python scripts, no compilation needed.

## Platform Requirements

**Development:**
- Windows (current), macOS, or Linux
- Python 3.8+
- Tesseract-OCR installed separately (Windows: `C:\Program Files\Tesseract-OCR\tesseract.exe`)
- Google API key with Generative Language API enabled
- Groq API key

**Production:**
- Not deployed — runs locally as a CLI tool
- Requires same platform dependencies as development

---

*Stack analysis: 2026-05-20*
*Update after major dependency changes*
