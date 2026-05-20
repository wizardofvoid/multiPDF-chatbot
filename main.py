import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# pyrefly: ignore [missing-import]
from langchain_community.vectorstores import FAISS
# pyrefly: ignore [missing-import]
from langchain_core.chat_history import InMemoryChatMessageHistory
# pyrefly: ignore [missing-import]
from langchain_core.output_parsers import StrOutputParser
# pyrefly: ignore [missing-import]
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
# pyrefly: ignore [missing-import]
from langchain_core.runnables.history import RunnableWithMessageHistory
# pyrefly: ignore [missing-import]
from langchain_google_genai import GoogleGenerativeAIEmbeddings
# pyrefly: ignore [missing-import]
from langchain_groq import ChatGroq

import extract_text as et
import text_chunker as tc

load_dotenv()

VECTORSTORE_DIR = "faiss_index"
FAISS_INDEX_FILE = Path(VECTORSTORE_DIR) / "index.faiss"
EMBEDDING_MODEL = "gemini-embedding-2"
LLM_MODEL = "openai/gpt-oss-20b"

store = {}


def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


def _env_ok(name: str) -> bool:
    return bool(os.getenv(name))


@st.cache_resource
def get_vectorstore():
    embeddings_model = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
    return FAISS.load_local(
        folder_path=VECTORSTORE_DIR,
        embeddings=embeddings_model,
        allow_dangerous_deserialization=True,
    )


@st.cache_resource
def get_chain_with_history():
    llm = ChatGroq(groq_api_key=os.getenv("GROQ_API_KEY"), model=LLM_MODEL)
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a study assistant. Answer using the Context below when it is relevant.\n"
                "If the Context does not contain the needed information, say it is not in the provided materials.\n"
                "Do not invent document facts.\n"
                "You may use general knowledge only for clarification if asked, and clearly label that it is not from the materials.\n\n"
                "Context:\n{context}",
            ),
            MessagesPlaceholder("history"),
            ("human", "{input}"),
        ]
    )
    chain = prompt | llm | StrOutputParser()
    return RunnableWithMessageHistory(
        chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="history",
    )


def run_ingestion() -> bool:
    extracted = et.main()
    index_missing = not FAISS_INDEX_FILE.exists()
    if extracted or index_missing:
        return tc.main()
    return True


def main():
    st.set_page_config(page_title="PDF Study Assistant", page_icon="📚", layout="wide")
    st.title("📚 PDF Study Assistant")

    if not _env_ok("GROQ_API_KEY") or not _env_ok("GOOGLE_API_KEY"):
        st.error("Missing GROQ_API_KEY or GOOGLE_API_KEY in .env")
        st.stop()

    with st.sidebar:
        st.header("Controls")
        session_id = st.text_input("Session ID", value="default_session")
        if st.button("Extract + Build Index", use_container_width=True):
            with st.spinner("Extracting text and building index..."):
                ok = run_ingestion()
            # Clear cached resources so rebuilt index is reloaded.
            st.cache_resource.clear()
            if ok:
                st.success("Index is ready.")
            else:
                st.error("Index build failed. Check logs/errors and try again.")

        if st.button("Clear Chat History", use_container_width=True):
            store.pop(session_id, None)
            st.session_state["messages"] = []
            st.success(f"Cleared history for session '{session_id}'.")

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if not FAISS_INDEX_FILE.exists():
        st.info("No index found. Click 'Extract + Build Index' in the sidebar.")
        st.stop()

    question = st.chat_input("Ask a question about your PDFs...")
    if not question:
        return

    st.session_state["messages"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                vectorstore = get_vectorstore()
                chain_with_history = get_chain_with_history()
                results = vectorstore.similarity_search(question, k=3)
                context_text = "\n\n".join(doc.page_content for doc in results)
                answer = chain_with_history.invoke(
                    {"input": question, "context": context_text},
                    config={"configurable": {"session_id": session_id}},
                )
            except Exception as e:
                answer = f"[ERROR] Request failed: {e}"
            st.markdown(answer)

    st.session_state["messages"].append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()
