import os
import json
from pypdf import PdfReader
import anthropic
import chromadb

class Generation:
    def __init__(self):
        self.txt_folder = "txtDocuments"
        self.pdf_folder = "pdfDocuments"
        self.chroma = chromadb.PersistentClient(path="./chroma_db")
        self.collection = self.chroma.get_or_create_collection("rag_visualizer")
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.llm = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-haiku-4-5-20251001"
        self.max_tokens = 1048

    def chunk_text(self, text, chunk_size=500, overlap=80):
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - overlap
            print(f"{start} - {end} - {len(text)} - {overlap}")
        return chunks

    def read_files(self):
        self.chroma.delete_collection("rag_visualizer")
        self.collection = self.chroma.get_or_create_collection("rag_visualizer")
        self.read_txt_files()
        self.read_pdf_files()

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
        evaluation_response = self.analyse_response(question, context, answer)
        print(f"Final Answer: {answer}")
        print(f"Faithfullness: {evaluation_response.get('faithfulness')}")
        print(f"Context Precision: {evaluation_response.get('context_precision')}")
        print(f"Answer Relevance: {evaluation_response.get('context_relevance')}")
        print(f"Reason: {evaluation_response.get('reason')}")

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

file_generation = Generation()
file_generation.read_files()
file_generation.ask("How do you test API endpoints?")
file_generation.ask("What is the best programming language for automation?")
# file_generation.ask("What is the competance and acceptance level?")
file_generation.ask("What are the requirements for information security risk assessment?")
