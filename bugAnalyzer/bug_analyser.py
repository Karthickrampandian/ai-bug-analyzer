import anthropic
import os
import json
import pandas as pd
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
        self.user_prompt = """Consider yourself as a LEAD QA consultant. Help with to categorise the below bug using these fields,
                [
                "severity":"Critical/High/Medium/Low",
                "priority":"P0/P1/P2/P3",
                "component":"Which part of the app is affected",
                "suggestion": "one clear fix direction",
                "title":"What can be the title of the bug"
                ]
                Ensure to revert back in json format only. No unwanted explanations."""
        self.bug_details = {
            "Severity": "",
            "priority": "",
            "component": "",
            "suggestion": "",
            "title": ""
        }

    def claude_connect(self,bug_input ):

        client = anthropic.Anthropic(api_key=self.api_key)

        # for bug in self.bug_list:
        message = client.messages.create(
                model=self.claude_model,
                max_tokens=self.tokens,
                system=self.user_prompt,
                messages=
                [{
                    "role": "user",
                    "content": bug_input
                }]
            )

        raw_response = message.content[0].text
        raw_response = raw_response.replace("```json", "").replace("```", "").strip()

        try:
            result = json.loads(raw_response)
        except json.JSONDecodeError:
            print("Claude didn't return valid json for this bug")
            result = {}
        final_result = {field: result[field.lower()] for field in self.bug_details.keys()}
        return final_result
