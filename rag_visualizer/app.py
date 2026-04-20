import os

import anthropic
import chromadb
from anthropic import Anthropic


class Generation:
    def __init__(self):
        self.txt_folder = "txtDocuments"
        self.chroma = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma.get_or_create_collection("rag_visualizer")
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.llm = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-haiku-4-5-20251001"
        self.max_tokens = 1048

    def chunk_text(self, text, chunk_size=200, overlap=50):
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - overlap
            print(f"{start} - {end} - {len(text)} - {overlap}")
        return chunks

    def read_files(self):
        for filename in os.listdir(f"{self.txt_folder}"):
            if filename.endswith(".txt"):
                with open(f"{self.txt_folder}/{filename}", "r") as f:
                    content = f.read()
                chunks = self.chunk_text(content)
                self.store_chunks(filename, chunks)
                print(f"---{filename} - {len(chunks)} chunks ---")
                for i, chunk in enumerate(chunks):
                    print(f"Chunk {i+1} ({len(chunk)} chars) : {chunk[:50]}")

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
            query_texts=[question], n_results=3, include=["documents", "distances"]
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
        verification_prompt = self.llm.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            messages=[{
                "role": "user",
                "content":f"""Context:{context}\n\nAnswer given:{answer} Is this answer fully supportd by the context provided?
                          Reply with only: GROUNDED or HALLUCINATED and one sentence why.""",
            }]
        )
        answer = verification_prompt.content[0].text
        print(f"Final Answer: {answer}")

file_generation = Generation()
file_generation.read_files()
file_generation.ask("How do you test API endpoints?")
file_generation.ask("What is the best programming language for automation?")
