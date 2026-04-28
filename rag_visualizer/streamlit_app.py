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

if st.button("Ask"):
    if question:
        result = file_generation.ask(question)
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