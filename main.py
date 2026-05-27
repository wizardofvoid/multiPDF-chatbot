import streamlit as st

from rag_agent import RAGAgent


@st.cache_resource
def get_agent() -> RAGAgent:
    return RAGAgent()

def main():
    st.set_page_config(page_title="PDF Study Assistant", page_icon="📚", layout="wide")
    st.title("📚 PDF Study Assistant")

    agent = get_agent()

    missing = agent.missing_env_vars()
    if missing:
        st.error(f"Missing in .env: {', '.join(missing)}")
        st.stop()

    with st.sidebar:
        st.header("Controls")
        session_id = st.text_input("Session ID", value="default_session")

        st.subheader("1. Upload PDFs")
        uploaded_files = st.file_uploader(
            "Upload one or more PDFs", type=["pdf"], accept_multiple_files=True
        )

        uploaded_file_names = [f.name for f in uploaded_files] if uploaded_files else []

        if "prev_uploaded_files" not in st.session_state:
            st.session_state["prev_uploaded_files"] = []

        # Sync PDFs in storage with files currently uploaded in Streamlit
        if uploaded_files or st.session_state["prev_uploaded_files"]:
            from pathlib import Path
            input_dir = Path("inputPDF")
            input_dir.mkdir(exist_ok=True, parents=True)

            # Save new uploads
            saved_names = []
            for uploaded_file in uploaded_files:
                file_path = input_dir / uploaded_file.name
                if not file_path.exists():
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    saved_names.append(uploaded_file.name)
            if saved_names:
                st.success(f"Saved: {', '.join(saved_names)}")

            # Remove deleted uploads and their caches only if they were explicitly removed from the uploader
            removed_names = []
            for existing_file in input_dir.glob("*.pdf"):
                if existing_file.name in st.session_state["prev_uploaded_files"] and existing_file.name not in uploaded_file_names:
                    existing_file.unlink()
                    removed_names.append(existing_file.name)
                    # Clear its cached text files
                    for ocr_state in ["True", "False"]:
                        cache_file = Path("output") / "cache" / f"{existing_file.name}_ocr_{ocr_state}.txt"
                        if cache_file.exists():
                            cache_file.unlink()
            if removed_names:
                st.warning(f"Deleted from storage: {', '.join(removed_names)}")

            st.session_state["prev_uploaded_files"] = uploaded_file_names

        st.subheader("2. Indexing")
        skip_ocr = st.checkbox("Skip Image OCR (Fast Mode)", value=True)
        if st.button("Extract + Build Index", use_container_width=True):
            with st.spinner("Extracting text and building index..."):
                ok = agent.run_ingestion(skip_ocr=skip_ocr)
            st.cache_resource.clear()
            if ok:
                st.success("Index is ready.")
            else:
                st.error("Index build failed. Check terminal logs and try again.")

        if st.button("Clear Chat History", use_container_width=True):
            agent.clear_session(session_id)
            st.session_state["messages"] = []
            st.success(f"Cleared history for session '{session_id}'.")

        if st.button("Clear Index & Storage", use_container_width=True):
            import shutil
            from pathlib import Path
            
            # 1. Clear inputPDF/
            input_dir = Path("inputPDF")
            if input_dir.exists():
                shutil.rmtree(input_dir)
                input_dir.mkdir(parents=True, exist_ok=True)
                
            # 2. Clear output/
            output_dir = Path("output")
            if output_dir.exists():
                shutil.rmtree(output_dir)
                output_dir.mkdir(parents=True, exist_ok=True)
                
            # 3. Clear faiss_index/
            faiss_dir = Path("faiss_index")
            if faiss_dir.exists():
                shutil.rmtree(faiss_dir)
                
            # 4. Clear session states and agent
            agent.reload()
            agent.clear_session(session_id)
            st.session_state["messages"] = []
            st.session_state["prev_uploaded_files"] = []
            st.cache_resource.clear()
            st.success("Successfully cleared all PDFs, caches, vector index, and chat memory!")

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if not agent.index_ready():
        st.info("No index found. Click 'Extract + Build Index' in the sidebar.")
        st.stop()

    question = st.chat_input("Ask a question about your PDFs...")
    if not question:
        return

    st.session_state["messages"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        answer = st.write_stream(agent.ask_stream(question, session_id=session_id))

    st.session_state["messages"].append({"role": "assistant", "content": answer})


if __name__ == "__main__":
    main()
