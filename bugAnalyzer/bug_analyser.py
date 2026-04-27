import anthropic
import os
import json
import pandas as pd
from jira_connector  import jira_connector
import chromadb

COMPONENT_FILE_MAP = {
    "login": ["Login.jsx"],
    "cart": ["Cart.jsx","CartButton.jsx", "HeaderContainer.jsx"],
    "checkout": ["CheckOutStepOne.jsx","InputError.jsx"]
}

SAUCEDEMO_PATH = "/Users/karthick/Desktop/Learn_Playwright/learningpython/sample-app-web/src"

class BugAnalyser:

    def load_bug_Report(self):
        try:
            report = pd.read_excel("bugfile/JIRA_BUG_REPORT.xlsx")
            bug_list = report["Bugs found"].to_list()
        except FileNotFoundError:
            print("No bugs found")
            bug_list=[]
        return bug_list

    def __init__(self):
        self.bug_list = self.load_bug_Report()
        self.claude_model = "claude-opus-4-5"
        self.tokens = 1024
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.user_prompt = """Your task is to consider yourself as a Automation architect, You need to go through
        the summary of the bug that is going to be shared from the JIRA report. I want you to go through the bug summary
        and research to help to update the below details
        [
        "severity": "Critical/High/Medium/Low",
        "priority": "P0,P1,P2,P3",
        "component":"Which part of the application component is affected because of this bug?",
        "suggestion": "What is the suggested fix for this bug? Can have have 2 bullet points one for developer and one for agent",
        "title": "Can use the summary and make it more meaningful"
        ]
        
        Ensure to review the report properly before rushing to the conclusion, ensure all the bugs were addressed properly.
        Ensure to revert the output back in json format only and dont add any additional information or details apart from 
        the bug report."""

        self.file_prompt = """Your task is to consider yourself as a developer, identify which function is causing this bug.
        Avoid unnecessary information. Share with me the correct function line number and function name."""
        self.chroma = chromadb.PersistentClient(path="./bug_vector")
        self.collection = self.chroma.get_or_create_collection("bug_history")

        self.bug_details = {
            "severity": "",
            "priority": "",
            "component": "",
            "suggestion": "",
            "title": ""
        }

    def claude_connect(self,bug_input ):

        global final_result
        all_bugs={}
        client = anthropic.Anthropic(api_key=self.api_key)
        bug = jira_connector()
        bug_list = bug.get_bugs()
        for bug,summary in bug_list.items():
            similar = self.collection.query(query_texts=[summary],n_results=2)
            similar_bugs = similar["documents"][0] if similar ["documents"][0] else []
            context = ""
            if similar_bugs:
                context="\n\nSimilar past bugs for referenc:\n"
                context += "\n" .join(f"- {b}" for b in similar_bugs)
                print(f"Similar bugs found: {similar_bugs}")
            else:
                print("No similar bugs yet — first run")
            message = client.messages.create(
                    model=self.claude_model,
                    max_tokens=self.tokens,
                    system=self.user_prompt,
                    messages=
                    [{
                        "role": "user",
                        "content": summary + context
                    }]
                )

            raw_response = message.content[0].text
            raw_response = raw_response.replace("```json", "").replace("```", "").strip()

            try:
                result = json.loads(raw_response)
            except json.JSONDecodeError:
                print("Claude didn't return valid json for this bug")
                result = {}
            final_result = {
                 field: result.get(field.lower(),"N/A")
                for field in self.bug_details}

            # Add similar bugs BEFORE adding to all_bugs
            final_result["similar_bugs"] = similar_bugs
            component = final_result.get("component", "")
            source_code, matched_files = self.read_source_file(component)
            if source_code:
                final_result["code_analysis"] = self.analyse_code(client, summary, source_code)
                final_result["matched_files"] = matched_files

            self.collection.upsert(
                documents = [summary],
                metadatas = [{"severity": final_result.get("severity", ""),
                             "component": final_result.get("component", "")}],
                ids = [bug]
            )
            all_bugs[bug] = final_result
        return all_bugs

    def analyse_code(self, client, bug_summary, source_code):
        response = client.messages.create(
            model=self.claude_model,
            max_tokens=self.tokens,
            system=self.file_prompt,
            messages=[{
                "role": "user",
                "content": f"Bug: {bug_summary}\n\nSource Code:\n{source_code}"
            }]
        )
        return response.content[0].text

    def read_source_file(self, component):
        files_content = ""
        matched_files = []
        folders = ["components", "pages"]
        for key, files in COMPONENT_FILE_MAP.items():
            if key in component.lower():
                for file in files:
                    for folder in folders:
                        filepath = os.path.join(SAUCEDEMO_PATH, folder, file)
                        if os.path.exists(filepath):
                            matched_files.append(file)
                            with open(filepath, "r") as f:
                                files_content += f"\n--- {file} ---\n{f.read()}"
                            break
        return files_content, matched_files