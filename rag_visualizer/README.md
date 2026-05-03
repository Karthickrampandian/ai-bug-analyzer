# RAG Visualizer

A Retrieval-Augmented Generation (RAG) system built with Python, ChromaDB, and Claude AI. Visualizes how different chunking strategies, retrieval methods, and evaluation metrics affect answer quality.

## What it does

Upload a PDF or TXT document, ask a question, and see exactly how the system retrieves, ranks, and generates an answer — with full transparency into every layer.

## Pipeline

**1. Ingestion**
- Upload PDF or TXT files via Streamlit UI
- Documents are chunked and stored in ChromaDB
- Each chunk is mapped to its source file and chunk index
- ChromaDB creates embeddings and places similar chunks close together in vector space

**2. Query Processing**
- Classifies the question: definition / procedural / reasoning / factual
- Expands definition questions into multiple angles for better retrieval
- Rewrites query to improve domain-specific matching

**3. Retrieval**
- Queries ChromaDB for top-k chunks (8–12 depending on question type)
- Deduplicates results across expanded queries
- Calculates confidence level from vector distance (high / medium / low)

**4. Reranking**
- Passes retrieved chunks through a CrossEncoder model
- Re-scores each chunk by relevance to the question
- Returns top 3 most relevant chunks
- If rerank threshold is too high → returns "no relevant information found"

**5. Generation**
- Builds context from top 3 reranked chunks with source labels
- Passes context + question to Claude with strict system prompt
- Claude is instructed to cite the supporting sentence and say "I don't know" if context doesn't answer

**6. Evaluation**
- LLM-as-judge: Claude evaluates faithfulness, context precision, and answer relevance
- Returns scores + reason for the evaluation decision
- RAGAS integration: implemented, requires OpenAI key for independent metric scoring

## Chunking Strategies (Tabs)

| Tab | Strategy |
|---|---|
| 500 Chars | Fixed chunking, 500 char window, 80 char overlap |
| 200 Chars | Fixed chunking, 200 char window, 50 char overlap |
| Metadata Filtering | Skips first N pages (e.g. table of contents) |
| Semantic Chunking | Regex-based section splitting by document structure |
| Hybrid Search | BM25 keyword + vector semantic search combined |
| Semantic Cache | Returns cached answer for similar questions (threshold: 0.15) |

## Tech Stack

- **Python** — core language
- **ChromaDB** — vector database for chunk storage and retrieval
- **Claude API (Haiku)** — LLM for generation and evaluation
- **CrossEncoder (ms-marco-MiniLM)** — reranking model
- **BM25Okapi** — keyword search for hybrid retrieval
- **Streamlit** — UI
- **RAGAS** — evaluation framework (OpenAI key required)

## Evaluation Metrics

- **Faithfulness** — Did the answer come from the context or did the LLM hallucinate?
- **Context Precision** — Were the retrieved chunks actually relevant?
- **Answer Relevance** — Did the answer address the question?

## Run Locally

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here
streamlit run streamlit_app.py
```
