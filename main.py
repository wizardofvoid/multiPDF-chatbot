import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# pyrefly: ignore [missing-import]
from langchain_groq import ChatGroq
# pyrefly: ignore [missing-import]
from langchain_community.vectorstores import FAISS
# pyrefly: ignore [missing-import]
from langchain_google_genai import GoogleGenerativeAIEmbeddings
# pyrefly: ignore [missing-import]
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# pyrefly: ignore [missing-import]
from langchain_core.output_parsers import StrOutputParser
# pyrefly: ignore [missing-import]
from langchain_core.chat_history import InMemoryChatMessageHistory
# pyrefly: ignore [missing-import]
from langchain_core.runnables.history import RunnableWithMessageHistory

import extract_text as et
import text_chunker as tc

# =========================================================
# CONFIG
# =========================================================
VECTORSTORE_DIR = "faiss_index"
FAISS_INDEX_FILE = Path(VECTORSTORE_DIR) / "index.faiss"
OUTPUT_TEXT = Path("output") / "output.txt"
EMBEDDING_MODEL = "gemini-embedding-2"
LLM_MODEL = "openai/gpt-oss-20b"
SESSION_ID = "default_session"

store = {}


def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"[ERROR] Missing environment variable: {name} (set it in .env)")
    return value


def main():
    _require_env("GROQ_API_KEY")
    _require_env("GOOGLE_API_KEY")

    print("[INFO] Checking PDFs and index...")
    embeddings_model = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)

    extraction_ran = et.main()
    index_missing = not FAISS_INDEX_FILE.exists()

    if extraction_ran or index_missing:
        print("[INFO] Rebuilding vector index from output/*.txt ...")
        if not tc.main():
            raise SystemExit(
                "[ERROR] Index build failed. Ensure output/output.txt exists "
                "(run extract_text or fix GOOGLE_API_KEY) and try again."
            )
    elif not OUTPUT_TEXT.exists():
        print(f"[WARNING] {OUTPUT_TEXT} not found. Run extract_text.py ")


    if not FAISS_INDEX_FILE.exists():
        raise SystemExit(
            f"[ERROR] No FAISS index at {VECTORSTORE_DIR}. "
            "Add PDFs to inputPDF/, run python extract_text.py, then python main.py."
        )

    vectorstore = FAISS.load_local(
        folder_path=VECTORSTORE_DIR,
        embeddings=embeddings_model,
        allow_dangerous_deserialization=True,
    )

    llm = ChatGroq(groq_api_key=os.getenv("GROQ_API_KEY"), model=LLM_MODEL)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a study assistant. Answer using the Context below when it is relevant.\n"
                "If the Context does not contain the information needed, say you cannot find that "
                "in the provided materials—do not invent facts from the documents. You may state facts infered from the available data.\n"
                "You may use general knowledge only for definitions or clarification if the user asks, "
                "and label that clearly as not from the materials.\n\n"
                "Context:\n{context}",
            ),
            MessagesPlaceholder("history"),
            ("human", "{input}"),
        ]
    )

    chain = prompt | llm | StrOutputParser()
    chain_with_history = RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )

    print("\n[INFO] Chat ready. Type 'exit' to quit.\n")

    while True:
        question = input("Enter your question: ").strip()
        if question.lower() == "exit":
            break
        if not question:
            continue

        print(f"\nUser: {question}")

        try:
            results = vectorstore.similarity_search(question, k=3)
            context_text = "\n\n".join(doc.page_content for doc in results)

            response = chain_with_history.invoke(
                {"input": question, "context": context_text},
                config={"configurable": {"session_id": SESSION_ID}},
            )
            print("\nChatbot:")
            print(response)
        except Exception as e:
            print(f"\n[ERROR] Request failed: {e}")


if __name__ == "__main__":
    main()
