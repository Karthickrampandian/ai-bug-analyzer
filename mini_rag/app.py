import anthropic
import chromadb
import os


class MiniRag():
    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.llm = anthropic.Anthropic(api_key=self.api_key)
        self.max_tokens = 500
        self.model = "claude-haiku-4-5-20251001"
        self.system_prompt = """You are a senior QA architect and your task is to analyse the bugs provided in the input and 
        revert back with below details
        {
        "severity":"P0/P1/P2/P3",
        "priority":"High/Medium/Low",
        "title":"Bug description",
        "component":"Which component the bug belongs to?",
        }
        
        Ensure the response is in json only and no other formats. Analyse the bug before coming to a conclusion"""
        self.question = input("Describe your bug:")

        self.chroma = chromadb.Client()
        self.collection = self.chroma.create_collection("bugs")

        self.collection.add (
            documents = ["Login button not working on Safari",
                         "Payment page crashes on checkout",
                         "Transaction type dropdown is not available in checkout page",
                         "Logo is considerably small in the login page then in the home page",
                         "Cache issue exist when user tries using 2 browsers at the same time"],
            ids= ["bug_1", "bug_2", "bug_3","bug_4","bug_5"],
        )

# Login selection is failing only for preofessor accounts but working for students
    def query_and_score(self):
        similar_bugs = self.collection.query(query_texts=[self.question], n_results = 2)
        distance = similar_bugs["distances"][0]
        top_distance = distance[0]
        if top_distance > 1.0:
            confidence = "low"
        elif top_distance > 0.5:
            confidence = "medium"
        else:
            confidence = "high"
        return confidence,similar_bugs

    def claude_connect(self):
        confidence_level,similar_bug = self.query_and_score()
        context_summary = f"Here are similar bugs: {similar_bug}. User's new bug: {self.question}. Analyze if this is a duplicate or new. Also confidence level of this bug against existing chromaDB: {confidence_level}"
        print(f"Content input:{context_summary}")
        response = self.llm.messages.create(
            model = self.model,
            max_tokens = self.max_tokens,
            system= self.system_prompt,
            messages = [
                {"role":"user",
                 "content":context_summary
                         }]
        )
        result = response.content[0].text.replace("```","").replace("json","")
        print(result)
        return response


rag = MiniRag()
rag.claude_connect()


