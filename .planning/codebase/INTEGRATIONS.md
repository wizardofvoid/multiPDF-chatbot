# External Integrations

**Analysis Date:** 2026-05-20

## APIs & External Services

**Groq API:**
- LLM inference via langchain-groq
  - SDK/Client: langchain-groq 1.1.2 (ChatGroq)
  - Auth: API key in `GROQ_API_KEY` env var
  - Model: `openai/gpt-oss-20b`
  - Purpose: Generate answers from retrieved context

**Google Generative AI (Gemini):**
- Text embeddings via langchain-google-genai
  - SDK/Client: langchain-google-genai 4.2.2 (GoogleGenerativeAIEmbeddings)
  - Auth: API key in `GOOGLE_API_KEY` env var
  - Model: `gemini-embedding-2`
  - Purpose: Convert text chunks to vector embeddings for similarity search

## Data Storage

**Vector Database:**
- FAISS (local) — Persistent vector index
  - Location: `faiss_index/` directory on disk
  - Client: langchain_community.vectorstores.FAISS
  - Rebuilds: On PDF changes or missing index
  - Serialization: `FAISS.load_local()` / `save_local()` with dangerous deserialization allowed

**Input:**
- PDF files — Source documents in `inputPDF/` directory
  - Format: Text-based, scanned (image), or mixed PDFs

**Output:**
- Extracted text — `output/*.txt` (per-PDF extracted text + OCR results)
- Extracted images — `output/images/` (per-page images for OCR processing)

## Authentication & Identity

**Auth Method:**
- API key based (no user authentication)
- Both services (Groq, Google) authenticated via static API keys in `.env`

## Environment Configuration

**Development:**
- Required env vars: `GROQ_API_KEY`, `GOOGLE_API_KEY`
- Secrets location: `.env` (gitignored — not committed)
- Tesseract path: Hardcoded in `extract_text.py` as `C:\Program Files\Tesseract-OCR\tesseract.exe`

---

*Integration audit: 2026-05-20*
*Update when adding/removing external services*
