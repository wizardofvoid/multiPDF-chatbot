from pathlib import Path

VECTORSTORE_DIR = "faiss_index"
FAISS_INDEX_FILE = Path(VECTORSTORE_DIR) / "index.faiss"
OUTPUT_TEXT = Path("output") / "output.txt"
EMBEDDING_MODEL = "gemini-embedding-2"
LLM_MODEL = "openai/gpt-oss-20b"
RETRIEVAL_K = 3
