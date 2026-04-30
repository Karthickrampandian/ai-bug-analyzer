import os
import json
import re

from pypdf import PdfReader
import anthropic
import chromadb
from rank_bm25 import BM25Okapi


class Generation:
    def __init__(self,chunk_size=500, overlap=80,mode="fixed"):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.mode = mode

        self.txt_folder = "txtDocuments"
        self.pdf_folder = "pdfDocuments"
        self.chroma = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma.get_or_create_collection(f"rag_{chunk_size}")
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.llm = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-haiku-4-5-20251001"
        self.max_tokens = 1048

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

    def ask(self, question):
        results = self.collection.query(
            query_texts=[question], n_results=3, include=["documents", "distances", "metadatas"]
        )

        top_distance = results["distances"][0][0]
        confidence = "low" if top_distance > 1.0 else "medium" if top_distance > 0.5 else "high"
        print(results["documents"][0])
        print(results["distances"][0])
        context = "\n".join(results["documents"][0])

        response = self.llm.messages.create(
        model = self.model,
        max_tokens = self.max_tokens,
        system="""Answer the questions based on the provided context provided only. 
        if the answer is not in the context, say 'I dont have enough information to answer the question'. 
        Do not use knowledge from outside""",
        messages = [{
            "role": "user",
            "content": f"Context:\n{context}\n\nQuestion:\n{question}\nAnswer based only on the context provided.",
        }])
        print(f"Confidence: {confidence} (distance: {top_distance:.4f})")
        print(f"Response: {response.content[0].text}")
        answer = response.content[0].text
        evaluation_response = self.analyse_response(question, context, answer)
        return {
            "answer": answer,
            "confidence": confidence,
            "distance": top_distance,
            "evaluation": evaluation_response,
            "chunks":[
                {
                    "text":results["documents"][0][i],
                    "distance":results["distances"][0][i],
                    "source":results["metadatas"][0][i].get("source","unknown"),
                    "chunk_number":results["metadatas"][0][i].get('chunk',i)
                }
                for i in range(len(results["documents"][0]))
            ]
        }

    def bm25(self,question,alpha=0.7):
        all_docs = self.collection.get(include=["documents"])
        documents = all_docs["documents"]
        ids = all_docs["ids"]

        tokenized_docs = [doc.lower().split() for doc in documents]
        bm25 = BM25Okapi(tokenized_docs)
        bm25_scores = bm25.get_scores(question.lower().split())

        semantic_search = self.collection.query(query_texts=[question],n_results=len(documents),
                                                include=["documents","distances"])
        semantic_distances =semantic_search["distances"][0]
        semantic_ids = semantic_search["ids"][0]
        sem_dict = dict(zip(semantic_ids, semantic_distances))
        semantic_distances_ordered = [sem_dict.get(id, 2.0) for id in ids]
        bm_normalise = self.normalize(bm25_scores)
        semantic_sim = [1-d for d in semantic_distances_ordered]
        semantic_normalise = self.normalize(semantic_sim)

        hybrid_scores = [alpha * s + (1-alpha)*b
                         for s,b in zip(semantic_normalise,bm_normalise)]

        scored = list(zip(hybrid_scores,ids,documents))
        scored.sort(key=lambda x: x[0], reverse=True)
        top3 = scored[:3]
        return top3

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

# file_generation = Generation()
# file_generation.read_files()
# file_generation.ask("How do you test API endpoints?")
# file_generation.ask("What is the best programming language for automation?")
# # file_generation.ask("What is the competance and acceptance level?")
# file_generation.ask("What are the requirements for information security risk assessment?")
