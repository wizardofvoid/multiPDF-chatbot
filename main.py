import os
from dotenv import load_dotenv

# pyrefly: ignore [missing-import]
from langchain_groq import ChatGroq
# pyrefly: ignore [missing-import]
from langchain_community.vectorstores import FAISS
# pyrefly: ignore [missing-import]
from langchain_google_genai import GoogleGenerativeAIEmbeddings
# pyrefly: ignore [missing-import]
from langchain_core.prompts import ChatPromptTemplate
# pyrefly: ignore [missing-import]
from langchain_core.output_parsers import StrOutputParser
# pyrefly: ignore [missing-import]
from langchain_core.chat_history import InMemoryChatMessageHistory
# pyrefly: ignore [missing-import]
from langchain_classic.memory import ConversationSummaryBufferMemory
# pyrefly: ignore [missing-import]
from langchain_core.runnables.history import RunnableWithMessageHistory




import text_chunker as tc
import extract_text as et
load_dotenv()

# =========================================================
# CONFIG
# =========================================================
VECTORSTORE_DIR = "faiss_index"
EMBEDDING_MODEL = "gemini-embedding-2"
LLM_MODEL = "openai/gpt-oss-20b"

store = {}

def get_session_history(session_id):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]



def main():
    # 1. Check for PDF updates and load the FAISS vector database
    print("[INFO] Checking for PDF updates...")
    embeddings_model = GoogleGenerativeAIEmbeddings(model=EMBEDDING_MODEL)
    
    changes_made = et.main()
    
    if changes_made or not os.path.exists(VECTORSTORE_DIR):
        print("[INFO] Database missing or PDFs changed. Rebuilding database...")
        tc.main()
        
    vectorstore = FAISS.load_local(
        folder_path=VECTORSTORE_DIR,
        embeddings=embeddings_model,
        allow_dangerous_deserialization=True
    )
    # 1.1 Define llm
    llm = ChatGroq(groq_api_key=os.getenv("GROQ_API_KEY"),model=LLM_MODEL)
    prompt = ChatPromptTemplate.from_template(
        """Answer the user's question based on the context provided below.
        If the answer is not in the context, say "Question out of context", 
        then you can answer according to you, if answer is not available say "I don't know"
        
        Previous conversation:
        {history}
        
        Context:
        {context}
        
        Question:
        {input}"""
    )
    memory = ConversationSummaryBufferMemory(
        llm=llm,
        max_token_limit=500,
        memory_key="history",
        input_key="input"
    )
    chain = prompt | llm | StrOutputParser()
    chain_with_history = RunnableWithMessageHistory(
        chain, 
        get_session_history, 
        input_messages_key="input", 
        history_messages_key="history"
        )
    

    # 2. Define the user's question
    while True:
        question = input("Enter your question: ")
        if question == "exit":
            break
        print(f"\nUser: {question}")

        # 3. Retrieve relevant chunks from the database
        results = vectorstore.similarity_search(question, k=3)
        context_text = "\n\n".join([doc.page_content for doc in results])  
    
        # Combine the retrieved chunks into one big context string
    
        response = chain_with_history.invoke(
            {"input": question, "context": context_text}, 
            config={"configurable": {"session_id": "default_session"}}
        )
        print("\nChatbot:")
        print(response)

if __name__ == "__main__":
    main()