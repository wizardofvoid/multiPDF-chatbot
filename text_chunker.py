import os
from pathlib import Path
from dotenv import load_dotenv

# pyrefly: ignore [missing-import]
from langchain_text_splitters import RecursiveCharacterTextSplitter
# pyrefly: ignore [missing-import]
from langchain_google_genai import GoogleGenerativeAIEmbeddings
# pyrefly: ignore [missing-import]
from langchain_community.vectorstores import FAISS

# Load environment variables (e.g., GOOGLE_API_KEY)
load_dotenv()

# =========================================================
# CONFIG
# =========================================================
INPUT_DIR = "output"
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
EMBEDDING_MODEL = "gemini-embedding-2"
VECTORSTORE_DIR = "faiss_index"

def chunk_all_text_files(input_dir: str, chunk_size: int, chunk_overlap: int):
    """
    Reads all text files in a directory and splits them into token-aware chunks.
    """
    path = Path(input_dir)
    if not path.exists() or not path.is_dir():
        print(f"[ERROR] Directory not found: {path.absolute()}")
        return []

    all_text = ""
    for file_path in path.glob("*.txt"):
        print(f"[INFO] Reading file: {file_path.name}")
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                all_text += file.read() + "\n\n"
        except Exception as e:
            print(f"[ERROR] Could not read {file_path.name}: {e}")

    if not all_text.strip():
        print("[WARNING] No text found in directory to chunk.")
        return []

    print(f"[INFO] Initializing token-aware text splitter (Size: {chunk_size}, Overlap: {chunk_overlap})...")
    
    # Token-aware splitter
    splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name="cl100k_base",
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    print("[INFO] Splitting text into chunks...")
    chunks = splitter.split_text(all_text)
    return chunks

def create_and_save_vectorstore(chunks: list[str]):
    """
    Generates embeddings for chunks and saves them in a local FAISS vector store.
    """
    if not chunks:
        return None

    print(f"[INFO] Initializing Google Embeddings Model ({EMBEDDING_MODEL})...")
    
    # Make sure GOOGLE_API_KEY is in your .env file
    try:
        embeddings_model = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
    except Exception as e:
        print(f"[ERROR] Failed to initialize embeddings model. Make sure GOOGLE_API_KEY is set. Details: {e}")
        return None

    try:
        # Workaround: The LangChain Google GenAI library currently has a bug where 
        # embed_documents silently truncates long batches. We embed one-by-one instead.
        import sys
        embeddings_list = []
        for i, chunk in enumerate(chunks):
            sys.stdout.write(f"\rEmbedding chunk {i+1}/{len(chunks)}...")
            sys.stdout.flush()
            emb = embeddings_model.embed_query(chunk)
            embeddings_list.append(emb)
        print("\n[INFO] All embeddings generated successfully.")
        
        # Create FAISS vector store from the manually generated embeddings
        text_embeddings = list(zip(chunks, embeddings_list))
        vectorstore = FAISS.from_embeddings(text_embeddings, embeddings_model)
        
        # Save it locally so we don't have to re-embed next time
        vectorstore.save_local(VECTORSTORE_DIR)
        print(f"[SUCCESS] FAISS vector store successfully saved to '{VECTORSTORE_DIR}' directory!")
        
        return vectorstore
    except Exception as e:
        print(f"\n[ERROR] FAISS creation failed: {e}")
        return None

def main():
    # 1. Chunk the text
    chunks = chunk_all_text_files(INPUT_DIR, CHUNK_SIZE, CHUNK_OVERLAP)
    
    if not chunks:
        return

    print(f"\n[SUCCESS] Total chunks generated: {len(chunks)}")

    # 2. Generate Embeddings & Save to FAISS
    vectorstore = create_and_save_vectorstore(chunks)
    
    # 3. Test the vector store with a Similarity Search
    if vectorstore:
        print("\n" + "="*50)
        print("[TEST] Running a sample similarity search...")
        
        # NOTE: You can change this test query to match whatever is in your PDF!
        query = "What is this document about?"
        print(f"Query: '{query}'\n")
        
        results = vectorstore.similarity_search(query, k=2)
        
        for i, result in enumerate(results):
            print(f"--- RESULT {i+1} ---")
            print(result.page_content)
            print("-" * 20 + "\n")

if __name__ == "__main__":
    main()
