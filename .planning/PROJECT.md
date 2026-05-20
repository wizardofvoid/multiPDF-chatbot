# Multi-PDF Study Assistant

## What This Is

A personal web-based study assistant that answers questions across a library of uploaded PDF textbooks, papers, and lecture notes. Built on RAG (Retrieval-Augmented Generation) — upload PDFs, ask questions, get answers grounded in your materials. Runs locally in the browser with persistent memory across study sessions.

## Core Value

Answer any question about the user's study materials accurately, using only the content from their uploaded PDFs.

## Requirements

### Validated

- ✓ PDF text extraction (PyMuPDF) — text-based PDFs
- ✓ OCR for scanned/image PDFs (Tesseract)
- ✓ Token-aware text chunking (tiktoken)
- ✓ Vector embeddings (Google Gemini)
- ✓ Local vector search (FAISS)
- ✓ LLM-powered Q&A (Groq API)

### Active

- [ ] Web UI — Browser-based interface for chat and PDF management
- [ ] Multi-PDF management — Upload, list, select, and remove PDFs via UI
- [ ] Persistent session memory — Remember conversation context across sessions
- [ ] PDF upload via web UI — Upload PDFs through browser, not file system
- [ ] Per-PDF scoping — Ask questions against specific PDF(s) or all at once

### Out of Scope

- Multi-user accounts — Local-only, single user
- Flashcards/quizzes — v2 feature, v1 is Q&A only
- Document comparison — v2 feature
- Mobile app — Desktop browser first
- Cloud deployment — Local-only
- Real-time collaboration — Single user

## Context

**Existing codebase:** Working CLI prototype with PDF extraction, OCR, chunking, embeddings, and LLM Q&A via LangChain + Groq + Gemini. Needs a web UI, persistent memory, and better multi-PDF management.

**Known issues to address:**
- Dead `ConversationSummaryBufferMemory` wiring in main.py
- Wrong embedding model ID
- No error recovery in REPL loop
- One-at-a-time embedding (slow for many PDFs)
- Tesseract path hardcoded to Windows

**Tech stack (existing):** Python, LangChain, FAISS, Google Gemini, Groq API, PyMuPDF

**Tech stack (to add):** Web framework (FastAPI + minimal frontend), SQLite for persistent memory

## Constraints

- **Timeline**: v1 working this week (exam prep urgency)
- **Platform**: Local-only web app, no cloud/auth
- **Stack**: Python-based (existing investment), minimal new dependencies
- **Scale**: 20+ PDFs, 50-200 pages each

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| CLI → Web app | Needs browser UI for practical study use | — Pending |
| Local-only | No auth, no deployment, simpler and faster | — Pending |
| SQLite for memory | Zero-config, sufficient for single-user persistent sessions | — Pending |
| v1 Q&A only | Must ship this week; flashcard/quizzes deferred | — Pending |

---

*Last updated: 2026-05-20 after project initialization*
