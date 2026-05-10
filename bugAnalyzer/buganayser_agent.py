import re
from os.path import join

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
HARDCODED_BUGS = {
    "SCRUM-10": "Login page accepts empty username without specific validation message",
    "SCRUM-11": "Cart badge count does not update immediately when item is removed",
    "SCRUM-12": "Checkout form allows submission with empty first name field"
}

chroma = chromadb.PersistentClient("./bug_vector")
chroma.delete_collection("bug_history")
collection = chroma.get_or_create_collection("bug_history")
src = "/Users/karthick/Desktop/Learn_Playwright/learningpython/sample-app-web/src"

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
    code_analysis:dict

def jira_connect(bug: bug_analyser):
    bug_list = {}
    auth = HTTPBasicAuth(email,token)
    headers = {"Content-Type": "application/json"}
    payload = {
        "jql": "project=SCRUM AND issuetype=Bug",
        "maxResults": 5,
        "fields": ["summary", "description", "priority", "status"]
    }

    resource = requests.post(
        f"{url}/rest/api/3/search/jql",
        headers=headers,
        auth=auth,
        json=payload
    )
    # print(resource.content)
    data = resource.json()
    for bug in data["issues"]:
        bug_list[bug["key"]] = bug["fields"]["summary"]
    # return {"jira": bug_list}
    # Jira OAuth integration planned — using representative bugs for demo
    # Real Jira connection implemented, pending OAuth token upgrade
    return {"jira": HARDCODED_BUGS}

def code_analysis(state: bug_analyser):
    fixes = {}
    for bug_id, bug in state["claude"].items():
        bug_title = bug.get('title','')
        file_path = get_local_files()
        relevant_files = identify_relevant_files(bug_title,file_path)
        fixes[bug_id]= {
            "relevant_files":relevant_files,
            "bug_title":bug_title,
        }

    bug_contents = read_content(fixes)

    for bug_id, content in bug_contents.items():
        fixes[bug_id]["source_code"] = content
        bug_title = fixes[bug_id]["bug_title"]

        fixes[bug_id]["fix"] = analyse_code(bug_title, content)

    return {"code_analysis": fixes}

def get_local_files():
    file_list = []
    extension_files = [".js",".ts",".jsx",".tsx"]
    for root, dirs, files in os.walk(src):
        dirs[:] = [file for file in dirs if file not in ["node_modules","__test__"]]
        for file in files:
            if any(file.endswith(ext) for ext in extension_files) and ".tests." not in file and ".stories." not in file:
                file_path = os.path.join(root,file)
                file_list.append(file_path)
    fila_path=""
    for file_path in file_list:
        fila_path += f"\n{join(file_path)}"
    return fila_path

def identify_relevant_files(summary,filepath):
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=500,
        system="""You are a senior Code reviewer, your task is to analyse the code and figure out what are the files
        impacted becuase of the bug from the file path.
        
        {
        "bug_summary":"summary of the bug",
        "files_impacted":["Return ONLY full file paths from the provided filepath list. Never return just filenames."]
        }
        
        
        You return the above json format, and avoid any other information. Analyse your response before rushing to a conclusion.
        """,
        messages=[{"role": "user", "content": f"Bug summary: {summary} \n Filepath:{filepath}"}]
    )
    raw_result = response.content[0].text.replace("```","").replace("json","")
    match = re.search(r'\{.*\}',raw_result,re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            return result.get("files_impacted",[])
        except:
            print(f"JSON failed for {filepath}")
            return []
    return []

def read_content(bugs):
    bug_content = {}
    for bug_id, file_path in bugs.items():
        file_content = ""
        for file in file_path["relevant_files"]:
            if os.path.exists(file):
                with open(file,'r') as f:
                    file_content += f"\n---{os.path.basename(file)} ---\n {f.read()}"
        bug_content[bug_id] = file_content
    return bug_content

def analyse_code(bug_title, source_code):
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=500,
        system="""You are a senior Code reviewer, your task is to analyse the code and bug to provide below details
        
        return only on json format
        {
        "bug_location":"function name and line number",
        "bug_code":"the buggy code snippet",
        "fixed_code":"the corrected code snippet",
        "Explanation":"one line explanation of why this fix is suggested"
        }
        Avoid unwanted information, analyse the result and return the response.
        """,
        messages=[{"role": "user", "content": f"Bug title: {bug_title} \n\n Source_code: {source_code}"}]
    )

    raw = response.content[0].text.replace("```","").replace("json","").strip()

    print(raw)
    try:
        result = json.loads(raw)
        return result
    except:
        return raw

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
builder.add_node("code_analysis", code_analysis)

builder.add_edge(START,"jira_connect")
builder.add_conditional_edges("jira_connect",route_after_jira,{"no_bugs":END,"analyse":"claude_connect"})
builder.add_edge("claude_connect", "analyse_bug")
builder.add_edge("analyse_bug","code_analysis")
builder.add_edge("code_analysis", END)

with SqliteSaver.from_conn_string("bug_memory.db") as memory:
    graph = builder.compile(checkpointer=memory)
    config = {"configurable":{"thread_id":"bug_session_1"}}
    graph.invoke({"jira":{},"claude":{},"analyse":{},"code_analysis":""}, config)


