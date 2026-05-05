import re

import anthropic
import os
import json
import pandas as pd
from jira_connector  import jira_connector
import chromadb

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
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.claude_model = "claude-opus-4-5"
        self.tokens = 1024
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

        self.file_prompt = """You are a developer. Analyse the bug and source code.
        Return ONLY this JSON:
        {
            "bug_location": "function name and line number",
            "bug_code": "the COMPLETE function with the bug, properly formatted with newlines",
            "fix_code": "the COMPLETE fixed function, properly formatted with newlines",
            "explanation": "one line explanation",
            "changed_lines": "only the specific lines that changed, before and after"
        }
        Return the full function body, not just the changed line."""
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
            message = self.client.messages.create(
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

            repo_path = "/Users/karthick/Desktop/Learn_Playwright/learningpython/sample-app-web/src"
            all_files = self.get_local_files(repo_path)
            print(f"Total files found: {len(all_files)}")
            print(f"Files: {all_files[:5]}")  # show first 5

            relevant_files = self.identify_relevant_files(final_result,all_files)
            print(f"Relevant files: {relevant_files}")

            if relevant_files:
                source_code = self.read_file_content(relevant_files)
                final_result["code_analysis"] = self.analyse_code(summary,source_code)
                final_result["matched_files"] = [os.path.basename(f) for f in relevant_files]

            self.collection.upsert(
                documents = [summary],
                metadatas = [{"severity": final_result.get("severity", ""),
                             "component": final_result.get("component", "")}],
                ids = [bug]
            )
            all_bugs[bug] = final_result
        return all_bugs

    def analyse_code(self, bug_summary, source_code):
        response = self.client.messages.create(
            model=self.claude_model,
            max_tokens=self.tokens,
            system=self.file_prompt,
            messages=[{
                "role": "user",
                "content": f"Bug: {bug_summary}\n\nSource Code:\n{source_code}"
            }]
        )
        raw = response.content[0].text.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(raw)
        except:
            return raw

    def identify_relevant_files(self,bug_summary,all_files):
        file_list = "\n".join(all_files)
        response = self.client.messages.create(
            model = self.claude_model,
            max_tokens=500,
            system="""You are a code analyst. Given a bug description and file list,
            return ONLY the files containing the logic that causes the bug.
            Prefer component files (.jsx) over utility/constant files (.js).
            Focus on files with form handling, event handlers, and UI logic.
            Return ONLY a JSON array of file paths. 
            No other explanation analyse the response before rushing to a conclusion""",
            messages=[
                {
                    "role": "user",
                    "content":f"Bug:{bug_summary}\n\nFile list:\n{file_list}"
                }
            ]
        )

        raw = response.content[0].text.replace("```json", "").replace("```", "").strip()
        print(f"Claude raw response: {raw}")

        match = re.search(r'\[.*\]', raw, re.DOTALL)
        print(f"Match found: {match}")
        if match:

            try:
                result = json.loads(match.group())
                print(f"Parsed result: {result}")
            except:
                print(f"JSON parse error: {e}")
                result = []
        else:
            result = []
        return result

    def get_local_files(self,repo_path):
        all_files = []
        for root, dirs,files in os.walk(repo_path):
            dirs[:] = [d for d in dirs if d not in ["node_modules","__tests__","dist"]]
            for file in files:
                if any(file.endswith(ext) for ext in [".jsx",".js",".ts",".tsx",".py"]):
                    full_path = os.path.join(root, file)
                    all_files.append(full_path)
        return all_files

    def read_file_content(self, file_paths):
        content = ""
        for path in file_paths:
            if os.path.exists(path):
                with open(path, "r") as f:
                    content += f"\n--- {os.path.basename(path)}---\n{f.read()}"
        return content

