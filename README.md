# 📚 PDF Study Assistant

**A conversational AI that reads your study PDFs so you don't have to re-read them.**

🔗 **[Try it live →](https://multipdf-chatbot-proto.streamlit.app/)**

---

## What is this?

PDF Study Assistant is a web app that lets you upload one or more PDF documents and then *have a conversation* with them. You ask questions in plain English, and the assistant answers based specifically on what's written in your files — not from general internet knowledge.

It was built as a study tool for situations where you have large lecture slides, textbooks, or course materials and want to quickly find answers, summarize sections, or test your understanding — without having to manually Ctrl+F through hundreds of pages.

---

## How it works

When you upload a PDF, the app extracts all the text from it — including text embedded in images using AI-powered OCR. That text is then broken into chunks, converted into vector embeddings using Google's Gemini embedding model, and stored in a local FAISS index (think of it as a specialized search database for meaning, not just keywords).

When you ask a question, the app searches that index for the 3 most relevant chunks of text, hands them to a large language model (running on Groq), and the LLM crafts a grounded answer using only what's in your documents. Your conversation history is kept in memory per session, so follow-up questions work naturally — the assistant remembers what you already discussed.

```
Your PDF → Text Extraction → Chunking → Embeddings → FAISS Index
                                                           ↓
                                          Your Question → Similarity Search
                                                           ↓
                                              Top 3 Chunks + Chat History → LLM → Answer
```

---

## Features

- **Multi-PDF support** — upload as many PDFs as you want and ask across all of them at once
- **Image OCR** — extracts text from diagrams and scanned images using Gemini Vision (can be toggled off for speed)
- **Conversational memory** — remembers your previous questions within a session so you can ask follow-ups naturally
- **Per-file caching** — already-processed PDFs are cached, so re-indexing is fast when only new files are added
- **PDF management** — removing a file from the uploader automatically deletes it from storage and clears its cache
- **Session control** — clear chat history without clearing your index, or wipe everything and start fresh
- **Honest answers** — the assistant will tell you if the answer isn't in your documents rather than making something up

---

## Tech Stack

| Component | Technology |
|---|---|
| UI | Streamlit |
| Text extraction | PyMuPDF (native text) + Gemini Vision (image OCR) |
| Embeddings | Google `gemini-embedding-2` |
| Vector store | FAISS (local, CPU) |
| LLM | Groq (`openai/gpt-oss-20b`) |
| Orchestration | LangChain |
| Environment | Python 3.11 |

---

## Running it locally

**1. Clone the repo**
```bash
git clone https://github.com/wizardofvoid/multiPDF-chatbot.git
cd multiPDF-chatbot
```

**2. Create and activate a virtual environment**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Set up your API keys**

Create a `.env` file in the project root:
```
GOOGLE_API_KEY=your_google_api_key_here
GROQ_API_KEY=your_groq_api_key_here
```

- Get a Google API key from [Google AI Studio](https://aistudio.google.com/app/apikey)
- Get a Groq API key from [console.groq.com](https://console.groq.com/)

**5. Launch the app**
```bash
streamlit run main.py
```

---

## Project structure

```
.
├── main.py           # Streamlit UI and app entry point
├── rag_agent.py      # Core RAG pipeline (load index, run LLM, manage sessions)
├── extract_text.py   # PDF text extraction with hybrid native + OCR approach
├── text_chunker.py   # Token-aware text splitting and FAISS index building
├── image_text.py     # Image OCR via Gemini Vision API
├── config.py         # Shared constants (model names, paths, retrieval config)
├── requirements.txt  # Python dependencies
└── runtime.txt       # Python version spec for deployment
```

---

## A note on accuracy

The assistant is intentionally designed to stay grounded in your documents. If you ask something that isn't covered in the uploaded PDFs, it will say so rather than hallucinate an answer. You can ask it to use its general knowledge for definitions or clarifications, but it will label that clearly so you know what came from your materials and what didn't.

---

## License

MIT
