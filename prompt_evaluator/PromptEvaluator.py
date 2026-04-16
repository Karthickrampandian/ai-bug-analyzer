import anthropic
import os
import chromadb
import json
import numpy as np

class PromptEvaluator:
    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.llm = anthropic.Anthropic(api_key=self.api_key)

        self.system_prompts = [

            """You are an Senior QA architect who is helping to review the bug and provide below details for the bug - 
                    {
                    "prompt_id":"QA_architect_prompt_1",
                    "severity":"P0/P1/P2/P3",
                    "priority":"High/Medium/Low",
                    "component":"Which component the defect might be in?",
                    "title":"Bug description",
                    "suggestion":"Focus on test gaps and edge cases"
                    }
                    Output should only be in json only, remove any unwated explaiantion or details. Ensure to analyse and reason
                    the response before giving a conclusion""",

            """You are an Developer who is helping to review the bug and provide below details for the bug - 
                      {
                      "prompt_id":"Developer_prompt_2",
                      "severity":"P0/P1/P2/P3",
                      "priority":"High/Medium/Low",
                      "component":"Focus on code-level fix",
                      "title":"Bug description",
            "suggestion":"Your suggestion on how to fix the bug"
                      }
                      Output should only be in json only, remove any unwated explaiantion or details. Ensure to analyse and reason
                      the response before giving a conclusion""",

            """You are an Product Owner who is helping to review the bug and provide below details for the bug - 
                        {
                        "prompt_id":"Product_Owner_prompt_3",
                        "severity":"P0/P1/P2/P3",
                        "priority":"High/Medium/Low",
                        "component":"Focus on business/user impact",
                        "title":"Bug description",
            "suggestion":"Your suggestion on how to fix the bug"
                        }
                        Output should only be in json only, remove any unwated explaiantion or details. Ensure to analyse and reason
                        the response before giving a conclusion""",

            """You are an Scrum Master who is helping to review the bug and provide below details for the bug - 
                             {
                             "prompt_id":"Scrum_Master_prompt_4",
                             "severity":"P0/P1/P2/P3",
                             "priority":"High/Medium/Low",
                             "component":"Focus on system design flaw",
                             "title":"Bug description",
            "suggestion":"Your suggestion on how to fix the bug"
                             }
                             Output should only be in json only, remove any unwated explaiantion or details. Ensure to analyse and reason
                             the response before giving a conclusion""",
        ]
        self.user_prompt = "Does this bug have high impact? Login is failing due to a checkout error on the payment screen."

        self.judge_prompt =   """You are a evaluator to evaluate the bug provided against below factors and give us the response in json
              
              1) Technical correctness
              2) Component alignment
              3) Clarity
              4) Route cause identification.
              
              Ensure the response is in JSON format only with below details, avoid unwanted explanation.
              
              {
              "prompt_id":"prompt_id",
              "rating":"rate the suggestion from 1-10, 1 being the worst and 10 being the best"
              }"""

        self.Judge_prompt2 = """Pick the best rating and prompt from the list and revert 
        back in json only
        {
        "prompt_id":"prompt_id",
        "rating":"rate the suggestion from 1-10, 1 being the worst and 10 being the best"
        }
        STRICTLY return valid JSON only. No extra text. Analyse the result before coming to a conclusion"""

        self.prompt_details = []

        self.bug_details = {
            "severity": "",
            "priority": "",
            "component": "",
            "suggestion": "",
            "title": "",
            "prompt_id":""
        }
        self.model = "claude-haiku-4-5-20251001"
        self.max_tokens = 500

        self.chroma_client = chromadb.Client()
        self.collection_name = self.chroma_client.create_collection("Prompt_evaluator")

        self.coverage_score = {}
        self.quality_score = {}

    def claude_connect(self,system_prompt,user_prompt):
        response = self.llm.messages.create(
                    model = self.model,
                    max_tokens=self.max_tokens,
                    system=system_prompt,
                    messages=[
                        {
                        "role":"user",
                        "content":user_prompt
                    }
                    ]
            )
        raw_result = response.content[0].text.replace("```","").replace("json","")
        return raw_result

    def extract_prompts(self):
        prompts_response_list = []
        prompts_id = []
        for prompt in self.system_prompts:
            raw_result = self.claude_connect(prompt, self.user_prompt)
            try:
                result = json.loads(raw_result)
            except json.JSONDecodeError:
                print("No valid prompts found")
                result = {}
            final_result = {
                field: result.get(field.lower(), "N/A")
                for field in self.bug_details}
            prompts_response_list.append(final_result["suggestion"])
            prompts_id.append(final_result["prompt_id"])
        self.collection_name.upsert(
            documents=prompts_response_list,
            ids=prompts_id,
        )
        self.prompt_details = list(zip(prompts_id, prompts_response_list))

    def quality_scoring(self):
        for prompt_id, suggestion in self.prompt_details:
            raw_result = self.claude_connect(self.judge_prompt, f"""Bug description:{self.user_prompt} 
                                                                prompt ID:{prompt_id} 
                                                                Suggestion:{suggestion}""")
            try:
                result = json.loads(raw_result)
            except json.JSONDecodeError:
                print("No valid quality score found")
                result = {}
            self.quality_score[prompt_id] =  int(result.get("rating", 0))
        print(f"quality score {self.quality_score}")
        # best_prompt = max(self.quality_score, key = self.quality_score.get)
        # print({
        #     "prompt_id":best_prompt,
        #     "rating":self.quality_score[best_prompt]
        # })

    def coverage_scoring(self):

        coverage_list_prompt = """You are an expert system analyst. 
        Given the bug, list import technical areas that should be covered in good solution.
        Return only a python list with single word, can refer to the examples for more clear list.
        Examples: 
        ['logging','session management','authentication']
        """
        response = self.claude_connect(coverage_list_prompt,self.user_prompt)
        keywords = response
        for prompt_id, suggestion in self.prompt_details:
            # print(f"suggestion:{suggestion}")
            score = sum (1 for k in keywords if k.lower() in suggestion.lower())
            self.coverage_score[prompt_id] = score/len(keywords) if len(keywords) > 0 else 0
        print(f"Coverage score {self.coverage_score}")

    def cosine_sim(self, a1, a2):
        a = np.array(a1)
        b = np.array(a2)
        print(type(a), type(b))
        print(a[:5] if hasattr(a, '__len__') else a)
        return np.dot(a,b)/(np.linalg.norm(a) * np.linalg.norm(b))
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

    def diversity_scoring(self):

        data = self.collection_name.get(include=["embeddings","documents"])
        embeddings = data["embeddings"]
        embeddings = [np.array(e).flatten() for e in embeddings]
        # print(data["documents"])
        # print(data["ids"])
        print(len(embeddings))
        scores = []
        for i in range(len(embeddings)):
            for j in range(i+1,len(embeddings)):
                cosine = self.cosine_sim(embeddings[i],embeddings[j])
                scores.append(cosine)
        avg_similarity = sum(scores)/len(scores) if len(scores) > 0 else 0
        diversity = 1 - avg_similarity
        print(f"Diversity score: {diversity}")
        return diversity

    def evaluate_prompt(self):
        self.extract_prompts()
        self.quality_scoring()
        self.coverage_scoring()
        diversity = self.diversity_scoring()
        final_scores = {}
        for prompt_id in self.quality_score:
            q = self.quality_score[prompt_id] / 10  # normalize to 0-1
            c = self.coverage_score[prompt_id]
            d = diversity  # same for all since it's overall
            final_scores[prompt_id] = float(q * 0.5 + c * 0.3 + d * 0.2)
        print(f"Final scores: {final_scores}")
        best = max(final_scores, key=final_scores.get)
        # for evaluation in
        #     final_score = quality_score * 0.5 +
        #          coverage_score * 0.3 +
        #             diversity_score * 0.2



prompt_eval = PromptEvaluator()
prompt_eval.evaluate_prompt()