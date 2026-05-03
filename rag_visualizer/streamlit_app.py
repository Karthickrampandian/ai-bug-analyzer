import streamlit as st
import os
from app import Generation

file_generation = Generation()

st.title("RAG Visualizer")

upload_file = st.file_uploader("Upload a document (txt/pdf)",type=["txt","pdf"])

def render_results(result):
    st.write("**Answer:**", result["answer"])

    st.metric("Confidence", result.get("confidence","N/A"))

    if result["retrieved_chunks"]:
        st.metric("Top Distance (ANN)", result["retrieved_chunks"][0]["distance"])
    else:
        st.metric("Top Distance (ANN)", "N/A")

    if result["reranked_chunks"]:
        st.metric("Top Rerank Score", result["reranked_chunks"][0]["score"])
    else:
        st.metric("Top Rerank Score", "N/A")

    eval_data = result.get("evaluation",{})

    col1, col2, col3 = st.columns(3)
    col1.metric("Faithfulness", eval_data.get("faithfulness", "N/A"))
    col2.metric("Context Precision", eval_data.get("context_precision", "N/A"))
    col3.metric("Answer Relevance", eval_data.get("context_relevance", "N/A"))

    st.info(eval_data.get("reason", ""))

    st.subheader("🔍 Retrieved Chunks")
    if result["retrieved_chunks"]:
        for chunk in result["retrieved_chunks"][:3]:
            with st.expander(f"Chunk {chunk['chunk_number']} (dist: {chunk['distance']:.3f})"):
                st.write(chunk["text"])
    else:
        st.write("No Relevant chunks found.")

    st.subheader("🎯 Reranked Chunks")
    if result["reranked_chunks"]:
        for chunk in result["reranked_chunks"]:
            with st.expander(f"Chunk {chunk['chunk_number']} (dist: {chunk['distance']:.3f})"):
                st.write(chunk["text"])
    else:
        st.write("No reranked results.")

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
tab500, tab200, tabMeta, tabSemantic, tabHybrid, tabCache = st.tabs([
    "500 Chars", "200 Chars", "Metadata Filtering", "Semantic Chunking", "Hybrid Chunking","Semantic Cache",
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
                    render_results(result)

display_results(Generation(chunk_size=500, overlap=80), question, tab500)
display_results(Generation(chunk_size=200, overlap=50), question, tab200)

with tabMeta:
    if st.button("Ask", key="btn_meta"):
        if question:
            gen_seman = Generation(chunk_size=500, overlap=80)
            gen_seman.read_files()
            st.metric("Total Chunks:", gen_seman.collection.count())
            result = gen_seman.ask(question)
            render_results(result)

with tabSemantic:
    if st.button("Ask", key="btn_semantic"):
        if question:
            gen_seman = Generation(mode="semantic")
            gen_seman.read_files(skip_pages=4)
            st.metric("Total Chunks:", gen_seman.collection.count())
            result = gen_seman.ask(question)
            render_results(result)

with tabHybrid:
    if st.button("Ask", key="btn_hybrid"):
        if question:
            gen_hybrid = Generation(chunk_size=500, overlap=80)
            gen_hybrid.read_files()
            top_k = gen_hybrid.bm25(question, alpha=0.7)

            docs = [doc for score, id, doc in top_k]

            reranked = gen_hybrid.rerank(
                question,
                docs,
                [{"source": "bm25", "chunk": i} for i in range(len(docs))],
                [score for score, _, _ in top_k]
            )

            st.subheader("🔍 Hybrid Retrieved (BM25 + Vector)")
            for i, (score, chunk_id, doc) in enumerate(top_k[:5]):
                with st.expander(f"{chunk_id} (score: {score:.4f})"):
                    st.write(doc)

            st.subheader("🎯 After Reranking")
            for item in reranked:
                with st.expander(f"{item['metadata']['chunk']} (rerank score: {item['score']:.4f})"):
                    st.write(doc)
            st.write(item["doc"])

with tabCache:
    if st.button("Ask", key="btn_cache"):
        if question:
            gen_cache = Generation(chunk_size=500, overlap=80)
            gen_cache.read_files()
            result, cacheHit = gen_cache.semantic_cache(question)
            if cacheHit:
                st.success("Cache HIT")
                st.write("**Answer:**", result)
            else:
                st.info("Cache MISS - fetched fresh")
                render_results(result)