import streamlit as st
import os
from app import Generation

st.title("RAG Visualizer")
st.info("⏳ First query takes 30-60 seconds — CrossEncoder reranking runs on CPU. Subsequent queries are faster.")

upload_file = st.file_uploader("Upload a document (txt/pdf)",type=["txt","pdf"])

if "generators" not in st.session_state:
    st.session_state.generators = {}

def get_gen(chunk_size, overlap, mode="fixed"):
    key = f"{mode}_{chunk_size}_{overlap}"
    if key not in st.session_state.generators:
        gen = Generation(chunk_size=chunk_size, overlap=overlap, mode=mode)
        gen.read_files()
        st.session_state.generators[key] = gen
    return st.session_state.generators[key]

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

def display_results(chunk_size, overlap, question, tab):
    with tab:
        if st.button("Ask", key=f"btn_{chunk_size}_{overlap}"):
            if question:
                gen = get_gen(chunk_size, overlap)
                st.metric("Total Chunks", gen.collection.count())
                if gen.collection.count() == 0:
                    st.warning("No documents indexed. Please upload a file first.")
                else:
                    with st.spinner("Retrieving and ranking chunks..."):
                         result = gen.ask(question)
                         render_results(result)

display_results(500, 80, question, tab500)
display_results(200, 50, question, tab200)

with tabMeta:
    if st.button("Ask", key="btn_meta"):
        if question:
            gen_seman = get_gen(chunk_size=500, overlap=80)
            st.metric("Total Chunks:", gen_seman.collection.count())
            with st.spinner("Retrieving and ranking chunks..."):
                result = gen_seman.ask(question)
                render_results(result)

with tabSemantic:
    if st.button("Ask", key="btn_semantic"):
        if question:
            gen_seman = get_gen(chunk_size=500, overlap=80,mode="semantic")
            st.metric("Total Chunks:", gen_seman.collection.count())
            with st.spinner("Retrieving and ranking chunks..."):
                result = gen_seman.ask(question)
                render_results(result)

with tabHybrid:
    if st.button("Ask", key="btn_hybrid"):
        if question:
            gen_hybrid  = get_gen(chunk_size=500, overlap=80)
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
            gen_cache  = get_gen(chunk_size=500, overlap=80)
            with st.spinner("Checking cache..."):
                result, cacheHit = gen_cache.semantic_cache(question)
            if cacheHit:
                st.success("Cache HIT")
                st.write("**Answer:**", result)
            else:
                st.info("Cache MISS - fetched fresh")
                render_results(result)