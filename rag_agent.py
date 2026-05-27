import os
from dataclasses import dataclass, field

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
from config import EMBEDDING_MODEL, FAISS_INDEX_FILE, LLM_MODEL, RETRIEVAL_K, VECTORSTORE_DIR

load_dotenv()


@dataclass
class ChatResult:
    answer: str
    context_chunks: list[str] = field(default_factory=list)
    error: str | None = None


class RAGAgent:
    """RAG pipeline: ingest PDFs, retrieve chunks, answer with history."""

    def __init__(self):
        self._vectorstore: FAISS | None = None
        self._chain: RunnableWithMessageHistory | None = None
        self._session_store: dict[str, InMemoryChatMessageHistory] = {}

    @staticmethod
    def env_configured() -> bool:
        return bool(os.getenv("GROQ_API_KEY")) and bool(os.getenv("GOOGLE_API_KEY"))

    @staticmethod
    def missing_env_vars() -> list[str]:
        missing = []
        if not os.getenv("GROQ_API_KEY"):
            missing.append("GROQ_API_KEY")
        if not os.getenv("GOOGLE_API_KEY"):
            missing.append("GOOGLE_API_KEY")
        return missing

    @staticmethod
    def index_ready() -> bool:
        return FAISS_INDEX_FILE.exists()

    def _get_session_history(self, session_id: str) -> InMemoryChatMessageHistory:
        if session_id not in self._session_store:
            self._session_store[session_id] = InMemoryChatMessageHistory()
        return self._session_store[session_id]

    def _load_vectorstore(self) -> FAISS:
        if self._vectorstore is None:
            embeddings = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
            self._vectorstore = FAISS.load_local(
                folder_path=VECTORSTORE_DIR,
                embeddings=embeddings,
                allow_dangerous_deserialization=True,
            )
        return self._vectorstore

    def _load_chain(self) -> RunnableWithMessageHistory:
        if self._chain is None:
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
            self._chain = RunnableWithMessageHistory(
                chain,
                self._get_session_history,
                input_messages_key="input",
                history_messages_key="history",
            )
        return self._chain

    def reload(self) -> None:
        """Drop cached vectorstore and chain (call after rebuilding the index)."""
        self._vectorstore = None
        self._chain = None

    def run_ingestion(self, skip_ocr: bool = False) -> bool:
        et.main(skip_ocr=skip_ocr)
        # Always run text chunker indexing when explicitly triggered by the user
        ok = tc.main()
        if ok:
            self.reload()
        return ok

    def clear_session(self, session_id: str) -> None:
        self._session_store.pop(session_id, None)

    def ask(self, question: str, session_id: str = "default_session") -> ChatResult:
        if not self.index_ready():
            return ChatResult(
                answer="",
                error="No search index found. Run extraction and index build first.",
            )

        try:
            vectorstore = self._load_vectorstore()
            chain = self._load_chain()
            docs = vectorstore.similarity_search(question, k=RETRIEVAL_K)
            chunks = [doc.page_content for doc in docs]
            context_text = "\n\n".join(chunks)
            answer = chain.invoke(
                {"input": question, "context": context_text},
                config={"configurable": {"session_id": session_id}},
            )
            return ChatResult(answer=answer, context_chunks=chunks)
        except Exception as e:
            return ChatResult(answer="", error=str(e))

    def ask_stream(self, question: str, session_id: str = "default_session"):
        if not self.index_ready():
            yield "[ERROR] No search index found. Run extraction and index build first."
            return

        try:
            vectorstore = self._load_vectorstore()
            chain = self._load_chain()
            docs = vectorstore.similarity_search(question, k=RETRIEVAL_K)
            chunks = [doc.page_content for doc in docs]
            context_text = "\n\n".join(chunks)
            for chunk in chain.stream(
                {"input": question, "context": context_text},
                config={"configurable": {"session_id": session_id}},
            ):
                yield chunk
        except Exception as e:
            yield f"[ERROR] {str(e)}"

