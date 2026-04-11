import anthropic
import os
import json
import pandas as pd
from jira_connector  import jira_connector
import chromadb

class BugAnalyser:


    def __init__(self):
        self.claude_model = "claude-opus-4-5"
        self.tokens = 1024
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.user_prompt = """You are a QA automation architect.
        Analyze the bug and use the provided tools.
        After using all tools, return ONLY this JSON — no other text:
        {
            "severity": "Critical/High/Medium/Low",
            "priority": "P0/P1/P2/P3",
            "component": "affected component",
            "suggestion": "fix suggestion",
            "title": "meaningful bug title"
        }"""
        self.chroma = chromadb.PersistentClient(path="./bug_vector")
        self.collection = self.chroma.get_or_create_collection("bug_history")

        self.bug_details = {
            "severity": "",
            "priority": "",
            "component": "",
            "suggestion": "",
            "title": ""
        }

        self.get_bug_severity = [{
            "name": "get_bug_severity",
            "description": "You must use this tool to ",
            "input_schema":
                {
                    "type": "object",
                    "properties": {
                        "bug_description": {"type": "string"},
                    },
                    "required": ["bug_description"],
                }
        }]

        self.duplicate_bug = [{
            "name": "get_duplicate_bug",
            "description": "You must use this tool to find out the bug is duplicate or not. You must use this tool to find out the duplicates.",
            "input_schema":
                {
                    "type": "object",
                    "properties": {
                        "bug_description": {"type": "string"},
                    },
                    "required": ["bug_description"],
                }
        }]

        self.retest_case_generate = [{
            "name": "get_retest_case",
            "description": "You must use this tool to create test cases for the bug. You must use this tool to create failed testcases.",
            "input_schema":
                {
                    "type": "object",
                    "properties": {
                        "bug_description": {"type": "string"},
                    },
                    "required": ["bug_description"],
                }
        }]

        self.tools = (
                self.get_bug_severity +
                self.duplicate_bug +
                self.retest_case_generate
        )

    def claude_connect(self, bug_input):
        all_bugs = {}
        client = anthropic.Anthropic(api_key=self.api_key)
        bug_connector = jira_connector()
        bug_list = bug_connector.get_bugs()

        for bug, summary in bug_list.items():
            duplicates = []
            message = client.messages.create(
                model=self.claude_model,
                max_tokens=self.tokens,
                tools=self.tools,
                messages=[{"role": "user", "content": summary}]
            )

            if message.stop_reason == "tool_use":
                tool_calls = [b for b in message.content if b.type == "tool_use"]
                tool_results = []

                for tool_call in tool_calls:
                    if tool_call.name == "get_bug_severity":
                        bug_desc = tool_call.input["bug_description"]
                        severity_rules = [
                            "high impact + frequent = Critical",
                            "high impact + occasional = High",
                            "medium impact + frequent = High",
                            "medium impact + occasional = Medium",
                            "low impact + any = Low"
                        ]
                        matches = [r for r in severity_rules if any(
                            w in r.lower() for w in bug_desc.lower().split())]
                        result = matches[0] if matches else "Medium severity"

                    elif tool_call.name == "duplicate_bug":
                        bug_desc = tool_call.input["bug_description"]
                        similar = self.collection.query(query_texts=[bug_desc], n_results=2)
                        duplicates = similar["documents"][0] if similar["documents"][0] else []
                        result = f"Similar bugs: {duplicates}" if duplicates else "No duplicates"

                    elif tool_call.name == "get_retest_case":
                        bug_desc = tool_call.input["bug_description"]
                        result = f"Retest: verify {bug_desc} is fixed"

                    else:
                        result = "Tool not found"

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call.id,
                        "content": [{"type": "text", "text": result}]
                    })

                final_message = client.messages.create(
                    model=self.claude_model,
                    max_tokens=self.tokens,
                    tools=self.tools,
                    messages=[
                        {"role": "user", "content": summary},
                        {"role": "assistant", "content": message.content},
                        {"role": "user", "content": tool_results},
                        {"role": "user",
                         "content": "Return ONLY JSON with keys: severity, priority, component, suggestion, title. No markdown."}
                    ]
                )
                raw_response = final_message.content[0].text

            else:
                raw_response = message.content[0].text

            raw_response = raw_response.replace("```json", "").replace("```", "").strip()
            print(f"Raw response: {raw_response}")

            try:
                result = json.loads(raw_response)
            except json.JSONDecodeError:
                print("Claude didn't return valid JSON")
                result = {}

            final_result = {
                field: result.get(field.lower(), "N/A")
                for field in self.bug_details
            }
            final_result["similar_bugs"] = duplicates

            self.collection.upsert(
                documents=[summary],
                metadatas=[{"severity": final_result.get("severity", ""),
                            "component": final_result.get("component", "")}],
                ids=[bug]
            )
            all_bugs[bug] = final_result

        return all_bugs
