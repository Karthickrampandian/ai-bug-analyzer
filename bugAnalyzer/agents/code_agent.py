import json
import os
import re
from os.path import join
from config import SOURCE_DIR, client,FILE_IDENTIFICATION, CODE_ANALYSIS_PROMPT
from models.state import bug_analyser

def get_local_files():
    file_list = []
    extensions = [".js",".ts",".jsx",".tsx"]
    for root,dirs,files in os.walk(SOURCE_DIR):
        dirs[:]=[file for file in dirs if file not in ["node_modules","__test__"]]
        for file in files:
            if any(file.endswith(ext) for ext in extensions) and ".tests." not in file and ".stories." not in file:
                file_path = os.path.join(root,file)
                file_list.append(file_path)
    file_path_str = ""

    for file_path in file_list:
        file_path_str += f"\n{join(file_path)}"
    return file_path_str

def identify_local_files(bug_summary:str, filepath:str):
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=FILE_IDENTIFICATION,
        messages=[{"role":"user","content":f"Bug summary:{bug_summary} \n Filepath:{filepath}"}]
    )


    raw_response = response.content[0].text.replace('```','').replace('json','')
    print(f"RAW RESPONSE: {repr(raw_response)}")  # ← moved here, always runs
    print(f"FILEPATH SENT: {repr(filepath)}")
    match = re.search(r'\{.*?\}',raw_response,re.DOTALL)
    if match:
        try:
            result = json.loads(match.group())
            return result.get("files_impacted",[])
        except json.JSONDecodeError:
            print(f"RAW RESPONSE: {raw_response}")
            print(f"Json is not valid for - {bug_summary}")
            return []
    return []


def read_content(bugs:dict):
    bug_content = {}
    for bug_id,file_path in bugs.items():
        file_content = ""
        for file in file_path["relevant_files"]:
            if os.path.exists(file):
                with open(file,"r") as f:
                    file_content += f"\n--{os.path.basename(file)}---\n{f.read()}"
        bug_content[bug_id] = file_content
    return bug_content

def analyse_code(bug_title:str, source_code:str):
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=500,
        system=CODE_ANALYSIS_PROMPT,
        messages=[{"role":"user","content":f"Bug title:{bug_title} \n Source code:{source_code}"}]
    )

    raw_response = response.content[0].text.replace('```','').replace('json','')

    try:
        results=json.loads(raw_response)
    except json.JSONDecodeError:
        print(f"Json is not valid for - {bug_title}")
        return []
    return results

def code_agent(state:bug_analyser):
    fixes={}
    valid_bugs = state.get("valid_bugs", {})
    print("🔴 Code agent processing critical bugs...")

    file_path = get_local_files()
    for bug_id, summary in valid_bugs.items():
        bug_title = summary.get("title","")

        relevant_files = identify_local_files(bug_title,file_path)
        fixes[bug_id] = {
            "relevant_files": relevant_files,
            "bug_title": bug_title,
        }

    bug_contents = read_content(fixes)

    for bug_id,content in bug_contents.items():
        fixes[bug_id]["source_code"] = content
        bug_title = fixes[bug_id]["bug_title"]

        if not fixes[bug_id]["relevant_files"]:
            fixes[bug_id]["fix"] ={
                "bug_location":"INSUFFICIENT_CONTEXT",
                "bug_code":"N/A",
                "fixed_code":"N/A",
                "Explanation":"No relevant source files were identified for this bug. A fix was not generated to avoid producing an unverified, speculative code change"
            }
            continue
        fixes[bug_id]["fix"] = analyse_code(bug_title,content)

    return {'code_analysis':fixes}