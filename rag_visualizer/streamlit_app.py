import streamlit as st
import os
from app import Generation

file_generation = Generation()

st.title("RAG Visualizer")

upload_file = st.file_uploader("Upload a document (txt/pdf)",type=["txt","pdf"])

if upload_file is not None:
    folder = ""
    if upload_file.name.endswith(".txt"):
        folder = "txtDocuments"
    elif upload_file.name.endswith(".pdf"):
        folder = "pdfDocuments"
    os.makedirs(folder, exist_ok=True)
    filepath = os.path.join(folder, upload_file.name)
    with open(filepath,"wb") as f:
        f.write(upload_file.getbuffer())
    st.success(f"Uploaded {upload_file.name}")

question = st.text_input("Ask a question?")
tab500, tab200, tabMeta, tabSemantic, tabHybrid = st.tabs([
    "500 Chars", "200 Chars", "Metadata Filtering", "Semantic Chunking", "Hybrid Chunking",
])

def display_results(gen, question, tab):
    with tab:
        if st.button("Ask", key=f"btn_{gen.chunk_size}_{gen.overlap}"):
            if question:
                gen.read_files()
                st.metric("Total Chunks", gen.collection.count())
                if gen.collection.count() == 0:
                    st.warning("No documents indexed. Please upload a file first.")
                else:
                    result = gen.ask(question)
                st.write("**Answer:**",result["answer"])
                st.metric("Confidence", result["confidence"])

                eval_data = result["evaluation"]
                col1, col2,col3 = st.columns(3)
                col1.metric("Faithfullness", eval_data.get('faithfulness'))
                col2.metric("Context Precision", eval_data.get('context_precision'))
                col3.metric("Answer Relevance", eval_data.get('context_relevance'))
                st.info(eval_data.get("reason",""))

                st.subheader("Retrieved Chunks")
                for chunk in result["chunks"]:
                    with st.expander(f"Chunk {chunk['chunk_number']} - {chunk['source']} (distance: {chunk['distance']:.4f})"):
                        st.write(chunk["text"])


display_results(Generation(chunk_size=500, overlap=80), question, tab500)
display_results(Generation(chunk_size=200, overlap=50), question, tab200)

with tabMeta:
    if st.button("Ask", key="btn_meta"):
        if question:
            gen_seman = Generation(chunk_size=500, overlap=80)
            gen_seman.read_files()
            st.metric("Total Chunks:", gen_seman.collection.count())
            result = gen_seman.ask(question)
            st.write("**Answer:**", result["answer"])
            st.write("**Confidence:**", result["confidence"])
            eval_data = result["evaluation"]
            col1, col2, col3 = st.columns(3)
            col1.metric("Faithfulness", eval_data.get('faithfulness'))
            col2.metric("Context Precision", eval_data.get('context_precision'))
            col3.metric("Answer Relevance", eval_data.get('context_relevance'))
            st.info(eval_data.get("reason", ""))
            st.subheader("Retrieved Chunks")
            for chunk in result["chunks"]:
                with st.expander(
                        f"Chunk {chunk['chunk_number']} - {chunk['source']} (distance: {chunk['distance']:.4f})"):
                    st.write(chunk["text"])

with tabSemantic:
    if st.button("Ask", key="btn_semantic"):
        if question:
            gen_seman = Generation(mode="semantic")
            gen_seman.read_files(skip_pages=4)
            st.metric("Total Chunks:", gen_seman.collection.count())
            result = gen_seman.ask(question)
            st.write("**Answer:**", result["answer"])
            st.write("**Confidence:**", result["confidence"])
            eval_data = result["evaluation"]
            col1, col2, col3 = st.columns(3)
            col1.metric("Faithfulness", eval_data.get('faithfulness'))
            col2.metric("Context Precision", eval_data.get('context_precision'))
            col3.metric("Answer Relevance", eval_data.get('context_relevance'))
            st.info(eval_data.get("reason", ""))
            st.subheader("Retrieved Chunks")
            for chunk in result["chunks"]:
                with st.expander(
                        f"Chunk {chunk['chunk_number']} - {chunk['source']} (distance: {chunk['distance']:.4f})"):
                    st.write(chunk["text"])

    with tabHybrid:
        if st.button("Ask", key="btn_hybrid"):
            if question:
                gen_hybrid = Generation(chunk_size=500, overlap=80)
                gen_hybrid.read_files()
                top3 = gen_hybrid.bm25(question)
                # Build context from top3
                context = "\n".join([doc for score, id, doc in top3])

                st.subheader("Hybrid Retrieved Chunks")
                for i, (score, chunk_id, doc) in enumerate(top3):
                    with st.expander(f"Chunk {i + 1} - {chunk_id} (hybrid score: {score:.4f})"):
                        st.write(doc)