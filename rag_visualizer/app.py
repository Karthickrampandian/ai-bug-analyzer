import os
import json
import re
from sentence_transformers import CrossEncoder
from pypdf import PdfReader
import anthropic
import chromadb
from rank_bm25 import BM25Okapi


class Generation:
    def __init__(self,chunk_size=500, overlap=80,mode="fixed"):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.mode = mode
        self.cross_encoder = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')

        self.threshold = 1.2

        self.txt_folder = "txtDocuments"
        self.pdf_folder = "pdfDocuments"
        # self.chroma = chromadb.PersistentClient(path="./chroma_db")
        self.chroma = chromadb.EphemeralClient()
        self.collection = self.chroma.get_or_create_collection(f"rag_{chunk_size}")
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.llm = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-haiku-4-5-20251001"
        self.max_tokens = 1048

    def query_classification(self,question):
        q = question.lower()

        if "what is" in q or "define" in q:
            return "definition"
        elif "how" in q:
            return "procedural"
        elif "why" in q:
            return "reasoning"
        else:
            return "factual"

    def rewrite_question(self,question,question_type):
        if question_type == "definition":
            return question + " in ISO 27001"
        return question

    def chunk_text(self, text):
        chunks = []
        start = 0
        while start < len(text):
            end = start + self.chunk_size
            chunks.append(text[start:end])
            start = end - self.overlap
            print(f"{start} - {end} - {len(text)} - {self.overlap}")
        return chunks

    def semantic_chunking(self,text):
        pattern = r'\n(?=\d+\.?\d*\s+[A-Z])'
        sections= re.split(pattern, text)
        print(f"Sections found: {len(sections)}")
        chunks = [s.strip() for s in sections if len(s.strip())>100]
        print(f"Chunks after filtering: {len(chunks)}")
        return chunks

    def read_files(self,skip_pages = 0):
        collection_name = f"rag_{self.chunk_size}" if self.mode == "fixed" else "rag_semantic"
        try:
            self.chroma.delete_collection(collection_name)
        except Exception:
            pass  # collection doesn't exist yet, that's fine
        self.collection = self.chroma.get_or_create_collection(collection_name)
        self.read_txt_files()
        if self.mode == "semantic":
            self.read_pdf_semantic()
        elif skip_pages > 0:
            self.read_pdf_with_metadata_filter(skip_pages)
        else:
            self.read_pdf_files()

    def read_pdf_semantic(self):
        for filename in os.listdir(self.pdf_folder):
            if filename.endswith(".pdf"):
                reader = PdfReader(f"{self.pdf_folder}/{filename}")
                content = ""
                for page in reader.pages:
                    content += page.extract_text()
                chunks = self.semantic_chunking(content)
                self.store_chunks(filename, chunks)
                print(f"---{filename} - {len(chunks)} chunks ---")

    def read_txt_files(self):
        for filename in os.listdir(self.txt_folder):
            if filename.endswith(".txt"):
                with open(f"{self.txt_folder}/{filename}", "r") as f:
                    content = f.read()
                chunks = self.chunk_text(content)
                self.store_chunks(filename, chunks)
                print(f"---{filename} - {len(chunks)} chunks ---")
                for i, chunk in enumerate(chunks):
                    print(f"Chunk {i+1} ({len(chunk)} chars) : {chunk[:50]}")

    def read_pdf_files(self):
        for filename in os.listdir(self.pdf_folder):
            if filename.endswith(".pdf"):
                reader = PdfReader(f"{self.pdf_folder}/{filename}")
                content = ""
                for page in reader.pages:
                    content += page.extract_text()
                chunks = self.chunk_text(content)
                self.store_chunks(filename, chunks)
                print(f"---{filename} - {len(chunks)} chunks ---")

    def read_pdf_with_metadata_filter(self, skip_pages = 4):
        for file in os.listdir(self.pdf_folder):
            if file.endswith(".pdf"):
                reader = PdfReader(f"{self.pdf_folder}/{file}")
                content = ""
                for page_num, page in enumerate(reader.pages):
                    if page_num <= skip_pages:
                        continue
                    content += page.extract_text()
                chunks = self.chunk_text(content)
                self.store_chunks(file, chunks)


    def store_chunks(self, filename, chunks):
        existing = self.collection.get()["ids"]
        for i, chunk in enumerate(chunks, 1):
            chunk_id = f"{filename.replace('.txt', '')}_chunk{i}"
            if chunk_id in existing:
                continue
            self.collection.add(
                documents=[chunk],
                ids=[chunk_id],
                metadatas={
                    "source": filename,
                    "chunk": i
                }
            )
            print(f"{filename} - {self.collection.count()}")

    def query_and_score(self, question):
        result = self.collection.query(
            query_texts=[question],
            n_results=3,
            include=["documents", "distances", "metadatas"]
        )
        for i in range(len(result["documents"][0])):
            print(f"Match {i+1}:")
            print(f" Source: {result['metadatas'][0][i]['source']}")
            print(f" Chunk: {result['metadatas'][0][i]['chunk']}")
            print(f" Distance: {result['distances'][0][i]:.4f}")
            print(f" Text: {result['documents'][0][i][:100]}...")

    def deduplicate(self,docs, metadatas,distances):
        seen = set()
        unique_docs = []
        unique_meta = []
        unique_dist = []

        for doc, meta, dist in zip(docs, metadatas, distances):
            key = (doc[:200], meta["source"], meta["chunk"])  # simple similarity check
            if key not in seen:
                seen.add(key)
                unique_docs.append(doc)
                unique_meta.append(meta)
                unique_dist.append(dist)

        return unique_docs, unique_meta, unique_dist

    def ask(self, question):
        #Understand Question
        question_type = self.query_classification(question)
        question = self.rewrite_question(question,question_type)
        top_k = self.top_k_count(question_type)

        #retrieve candidates
        queries = [question] + self.expand_query(question, question_type)

        all_docs, all_meta, all_dist = [], [], []

        for q in queries:
            res = self.retrieve(q, top_k=top_k)
            all_docs.extend(res["documents"])
            all_meta.extend(res["metadatas"])
            all_dist.extend(res["distances"])

        docs, metadatas, distances = self.deduplicate(all_docs, all_meta, all_dist)

        if not docs:
            return self.no_response_return()

        #Confidence layer
        top_distance = float(distances[0])
        if top_distance > 1.2:
            confidence = "low"
        elif top_distance > 0.6:
            confidence = "medium"
        else:
            confidence = "high"

        #rerank
        reranked = self.rerank(question, docs,  metadatas, distances)
        if not reranked:
            return self.no_response_return()

        threshold = self.threshold
        if reranked:
            if question_type == "definition" and reranked[0]["score"] < 0:
                threshold = 1.5

        if top_distance > threshold:
            return self.no_response_return()

        #Context Building - generation layer
        context = self.build_context(reranked)

        #llm reasoning layer
        answer = self.llm_generation(question,context)
        evaluation_response = self.analyse_response(question, context, answer)
        # evaluation_response = self.ragas_evaluate(question, answer, [item["doc"] for item in reranked])

        self.log_pipelines({
            "question": question,
            "retrieved_docs": docs[:5],
            "reranked_docs": [r["doc"] for r in reranked],
            "context": context,
            "answer": answer
        })

        retrieved_formatted = {
            "documents": docs[:5],
            "distances": distances[:5],
            "metadatas": metadatas[:5]
        }

        return self.format_response(
            answer,confidence,
            evaluation_response,
            retrieved_formatted,
            reranked)

    def retrieve(self, question,top_k=8):
        results = self.collection.query(
            query_texts=[question],
            n_results=top_k,
            include=["documents", "distances", "metadatas"]
        )

        return {
            "documents":results["documents"][0],
            "metadatas":results["metadatas"][0],
            "distances":results["distances"][0]
        }

    def expand_query(self, question, question_type):
        if question_type == "definition":
            return [
                question,
                question + " meaning",
                question + " definition ISO 27001"
            ]
        return [question]

    def no_response_return(self):
        return {
            "answer": "No relevant information found in the document",
            "confidence": "low",
            "evaluation": {},
            "retrieved_chunks": [],
            "reranked_chunks": [],
        }

    def top_k_count(self,question_type):
        if question_type == "definition":
            top_k = 12
        elif question_type == "procedural":
            top_k = 6
        else:
            top_k = 8
        return top_k

    def rerank(self, question, docs, metadatas, distances):
        pairs = [(question,doc) for doc in docs]
        scores = self.cross_encoder.predict(pairs)

        combined = []
        for i in range(len(docs)):
            combined.append({
                "doc":docs[i],
                "score":scores[i],
                "distance":distances[i],
                "metadata":metadatas[i],
                "index": i
            })

        ranked = sorted(combined, key = lambda x:x["score"], reverse=True)
        return ranked[:3]

    def build_context(self,reranked,top_n=3):

        context_parts=[]
        for i, item in enumerate(reranked[:top_n]):
            context_parts.append(f"[Source {i+1}]\nDocument: {item['metadata']['source']} \n{item['doc']} ")
        return "\n\n".join(context_parts)

    def log_pipelines(self, data):
        with open("rag_logs.json","a") as f:
            f.write(json.dumps(data) +"\n")


    def llm_generation(self,question,context):
        response = self.llm.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
                    system="""You are a document assistant. You answer questions strictly from the provided context.
        
                    RULES:
                    - Only use information explicitly stated in the context
                    - If the answer is not in the context, respond exactly: "I don't have enough information to answer this."
                    - Always quote the supporting sentence from the context
                    - Never infer or assume beyond what is written
                    
                    FORMAT:
                    Answer: <your answer here>
                    Source: <exact quote from context that supports it>
                    """,
            messages=[{
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion:\n{question}\nAnswer based only on the context provided.",
            }])
        return response.content[0].text

    def format_response(self,answer,confidence,evaluation,retrieved,reranked):
        return {
            "answer": answer,
            "confidence": confidence,
            "evaluation": evaluation,

            "retrieved_chunks": [
                {
                    "text": retrieved["documents"][i],
                    "distance": retrieved["distances"][i],
                    "source": retrieved["metadatas"][i].get("source", "unknown"),
                    "chunk_number": retrieved["metadatas"][i].get("chunk", i)
                }
                for i in range(len(retrieved["documents"]))
            ],

            "reranked_chunks": [
                {
                    "text": item["doc"],
                    "score": item["score"],  # cross-encoder score
                    "distance": item["distance"],
                    "source": item["metadata"].get("source", "unknown"),
                    "chunk_number": item["metadata"].get("chunk", item["index"])
                }
                for item in reranked
            ]
        }


    def bm25(self,question,alpha=0.7):
        all_docs = self.collection.get(include=["documents"])
        documents = all_docs["documents"]
        ids = all_docs["ids"]

        tokenized_docs = [doc.lower().split() for doc in documents]
        bm25 = BM25Okapi(tokenized_docs)
        bm25_scores = bm25.get_scores(question.lower().split())
        bm_normalise = self.normalize(bm25_scores)

        semantic_search = self.collection.query(query_texts=[question],n_results=len(documents),
                                              include=["documents","distances"])

        semantic_distances =semantic_search["distances"][0]
        semantic_ids = semantic_search["ids"][0]
        sem_dict = dict(zip(semantic_ids, semantic_distances))
        semantic_distances_ordered = [sem_dict.get(id, 2.0) for id in ids]
        semantic_sim = [1-d for d in semantic_distances_ordered]
        semantic_normalise = self.normalize(semantic_sim)

        hybrid_scores = [alpha * s + (1-alpha)*b
                         for s,b in zip(semantic_normalise,bm_normalise)]

        scored = list(zip(hybrid_scores,ids,documents))
        scored.sort(key=lambda x: x[0], reverse=True)
        top3 = scored[:3]
        return top3

    def semantic_cache(self, question):
        cache_collection = self.chroma.get_or_create_collection("cache")

        if cache_collection.count()>0:
            cached = cache_collection.query(query_texts=[question],n_results=1,include=["documents","distances","metadatas"])

            if cached["distances"][0][0] <0.15:
                return cached["metadatas"][0][0]["answer"], True

        result = self.ask(question)

        cache_collection.add(
            documents=[question],
            ids=[f"cache_{hash(question)}"],
            metadatas=[{"answer":result["answer"]}],
        )

        return result, False


    def normalize(self,score):
        max_s = max(score)
        min_s = min(score)
        if max_s == min_s:
            return [1.0] * len(score)

        return [(s - min_s) / (max_s - min_s) for s in score]

    def analyse_response(self, question, context, answer):
        eval_prompt = f""" You are a RAG evaluation expert.
             Your task is to analyse the context provided and provide below details before analysing 
             the context thoroughly before rushing to a conclusion. Score the following on a scale of 1-10.

             question:{question}
             context retrieved:{context}
             Answer given:{answer}

             Return only in JSON structure and avoid any other unwanted explanation.

             {{
                 "faithfulness":"Grounded or hallucinated",
                 "context_precision": "Rate between 1 to 10, 1 = worst, 10 = best, based on the answers provided.",
                 "context_relevance":"Rate between 1 to 10, 1 = worst, 10 = best, based on the answers provided.",
                 "reason":"One reason why"
             }}

             """
        response = self.llm.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages = [{
                "role": "user",
                "content": eval_prompt
            }]
        )

        raw_result = response.content[0].text.replace("```","").replace("json","")
        try:
            evaluation = json.loads(raw_result)
            return evaluation
        except json.JSONDecodeError:
            return {"error": "evaluation failed"}

    def ragas_evaluate(self, question, answer, reranked):
        from ragas import evaluate
        from ragas.metrics.collections import Faithfulness, AnswerRelevancy
        from datasets import Dataset
        from ragas.llms import LangchainLLMWrapper
        from langchain_anthropic import ChatAnthropic
        llm = LangchainLLMWrapper(ChatAnthropic(
            model="claude-haiku-4-5-20251001",
            api_key=self.api_key,
        ))

        data = {
            "question": [question],
            "answer": [answer],
            "contexts":[reranked],
        }

        dataset = Dataset.from_dict(data)
        result = evaluate(dataset, metrics = [Faithfulness(llm=llm),AnswerRelevancy(llm=llm)])

        return {
            "faithfulness":round(result["faithfulness"],2),
            "answer_relevancy":round(result["answer_relevancy"],2),
        }
# file_generation = Generation()
# file_generation.read_files()
# file_generation.ask("How do you test API endpoints?")
# file_generation.ask("What is the best programming language for automation?")
# # file_generation.ask("What is the competance and acceptance level?")
# file_generation.ask("What are the requirements for information security risk assessment?")
