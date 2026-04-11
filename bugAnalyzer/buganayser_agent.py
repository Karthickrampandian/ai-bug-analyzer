import anthropic
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
import os
import requests
from requests.auth import HTTPBasicAuth
from langgraph.checkpoint.sqlite import SqliteSaver
import json
import chromadb

url = os.environ.get("JIRA_URL")
email = os.environ.get("JIRA_EMAIL")
token = os.environ.get("JIRA_TOKEN")
api_key = os.environ.get("ANTHROPIC_API_KEY")
client = anthropic.Anthropic(api_key=api_key)

chroma = chromadb.PersistentClient("./bug_vector")
collection = chroma.get_or_create_collection("bug_history")

user_prompt = """ You are a senior automation architect with over 10 years of experience, go through the bugs
    bug provided in the context and share with me the below details in json format:

    {
    "severity":"P0/P1/P2/P3",
    "priority":"High/Medium/Low/Critical",
    "title":"bug desription",
    "component":"If the bug has component added it, else research and decide which component it belongs to",
    }
     Share the details in json format only, avoid any other information.       
    """
bug_details = {
    "severity": "",
    "priority": "",
    "component": "",
    "suggestion": "",
    "title": ""
}

class bug_analyser(TypedDict):
    jira: list
    claude:dict
    analyse:str

def jira_connect(bug: bug_analyser):
    bug_list = {}
    auth = HTTPBasicAuth(email,token)
    headers = {"Content-Type": "application/json"}
    resource = requests.get(
        f"{url}/rest/api/3/search/jql",
        headers=headers,
        auth=auth,
        params={
            "jql": "project=TNR AND issuetype=Bug",
            "maxResults": 5,
            "fields": "summary,description,priority,status"
        }
    )
    # print(resource.content)
    data = resource.json()
    for bug in data["issues"]:
        bug_list[bug["key"]] = bug["fields"]["summary"]
    return {"jira": bug_list}

def route_after_jira(state: bug_analyser):
    if not state["jira"]:
        return "no_bugs"
    else:
        return "analyse"

def claude_connect(state: bug_analyser):
    all_bugs = {}
    for bug_id, summary in state["jira"].items():
        response = client.messages.create(
            model="claude-opus-4-5",
            max_tokens=500,
            system=user_prompt,
            messages=[{"role": "user", "content": summary}]
        )

        raw_response = response.content[0].text.replace("```","").replace("json","")
        try:
            result = json.loads(raw_response)
        except json.JSONDecodeError:
            print(f"JSON failed for {bug_id}")
            result = {}
        final_result = {
                 field: result.get(field.lower(),"N/A")
                for field in bug_details}
        all_bugs[bug_id] = final_result
    return {"claude": all_bugs}

def analyse_bug(state: bug_analyser):
    valid_bugs = {}
    duplicate_bugs = {}

    for bug, analysis in state["claude"].items():
        title = analysis.get("title", "")

        similar = collection.query(query_texts=[title], n_results=2)
        similar_bugs = similar["documents"][0] if len(similar["documents"]) > 0 else []

        if similar_bugs:
            duplicate_bugs[bug] = similar_bugs
        else:
            valid_bugs[bug] = analysis

        collection.upsert(
            documents=[title],
            metadatas=[{"bug_id":bug}],
            ids=[bug]
        )

    print(f"✅ Valid: {len(valid_bugs)} bugs")
    print(f"⚠️ Duplicates: {len(duplicate_bugs)} bugs")

    return {"analyse": f"Valid:{len(valid_bugs)} Duplicates:{len(duplicate_bugs)}"}



builder = StateGraph(bug_analyser)
builder.add_node("jira_connect", jira_connect)
builder.add_node("claude_connect", claude_connect)
builder.add_node("analyse_bug", analyse_bug)

builder.add_edge(START,"jira_connect")
builder.add_conditional_edges("jira_connect",route_after_jira,{"no_bugs":END,"analyse":"claude_connect"})
builder.add_edge("claude_connect", "analyse_bug")
builder.add_edge("analyse_bug",END)

with SqliteSaver.from_conn_string("bug_memory.db") as memory:
    graph = builder.compile(checkpointer=memory)
    config = {"configurable":{"thread_id":"bug_session_1"}}
    graph.invoke({"bug":"Analyse TNR bugs"}, config)

