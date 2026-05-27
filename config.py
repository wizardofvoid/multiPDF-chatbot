from pathlib import Path

# Directory and file paths
INPUT_DIR = Path("inputPDF")
OUTPUT_DIR = Path("output")
OUTPUT_TEXT = OUTPUT_DIR / "output.txt"
VECTORSTORE_DIR = "faiss_index"
FAISS_INDEX_FILE = Path(VECTORSTORE_DIR) / "index.faiss"

# RAG and LLM models
EMBEDDING_MODEL = "gemini-embedding-2"
LLM_MODEL = "openai/gpt-oss-20b"

# Chunking and Retrieval configurations
RETRIEVAL_K = 3
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
MIN_IMAGE_SIZE = 150
