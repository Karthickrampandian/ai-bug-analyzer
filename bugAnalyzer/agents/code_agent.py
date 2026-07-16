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
    # print(f"RAW RESPONSE: {repr(raw_response)}")  # ← moved here, always runs
    # print(f"FILEPATH SENT: {repr(filepath)}")
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
        files = {}
        file_content = ""
        for file in file_path["relevant_files"]:
            if os.path.exists(file):
                with open(file,"r") as f:
                    file_content = f.read()
                    files[file] = file_content
        bug_content[bug_id] = files
    return bug_content

def analyse_code(bug_title:str, source_code:str, previous_fix = None):
    if previous_fix:
        content = f"Bug title:{bug_title} \n Source code:{source_code} \n Previous attempted fix: {previous_fix} \n This is the fix provided in the last try, strictly think of some other solution and fix"
    else:
        content = f"Bug title:{bug_title} \n Source code:{source_code}"

    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        system=CODE_ANALYSIS_PROMPT,
        messages=[{"role":"user","content":content}]
    )

    raw_response = response.content[0].text.replace('```','').replace('json','')

    try:
        results=json.loads(raw_response)
    except json.JSONDecodeError:
        print(f"Json is not valid for - {bug_title}")
        invalid_bug = {
            "bug_location": "JSON_PARSE_ERROR",
            "bug_code": "N/A",
            "fixed_code": "N/A",
            "Explanation": "JSON Parsing failed, valid json is not returned for processing"
        }
        return invalid_bug
    return results

def code_agent(state:bug_analyser):

    retry_bugs = state.get("retry_bugs",{})

    if retry_bugs:
        bugs_to_process = retry_bugs
    else:
        bugs_to_process = state.get("valid_bugs",{})

    fixes={}
    # valid_bugs = state.get("valid_bugs", {})
    print("🔴 Code agent processing critical bugs...")

    file_path = get_local_files()
    for bug_id, summary in bugs_to_process.items():
        bug_title = summary.get("title") or summary.get("bug_title", "")
        previous_fix = summary.get("fix", {}).get("fixed_code")

        if summary.get("source_code"):
            fixes[bug_id] = {
                "relevant_files":summary.get("relevant_files"),
                "bug_title":bug_title,
                "source_code":summary.get("source_code"),
                "previous_fix":previous_fix,
            }
        else:
            relevant_files = identify_local_files(bug_title,file_path)
            fixes[bug_id] = {
                "relevant_files": relevant_files,
                "bug_title": bug_title,
                "previous_fix": previous_fix,
            }

    bugs_needing_files = {bug_id: data for bug_id, data in fixes.items() if not data.get("source_code")}
    bugs_already_have_source = {bug_id: data for bug_id, data in fixes.items() if data.get("source_code")}

    bug_contents = read_content(bugs_needing_files)

    for bug_id,content in bug_contents.items():
        fixes[bug_id]["source_code"] = content
        failed_fix = fixes[bug_id]["previous_fix"]
        bug_title = fixes[bug_id]["bug_title"]


        if not fixes[bug_id]["relevant_files"]:
            print(f"{bug_id} has insufficient context (no relevant files found) — marked for manual review")
            fixes[bug_id]["fix"] ={
                "bug_location":"INSUFFICIENT_CONTEXT",
                "bug_code":"N/A",
                "fixed_code":"N/A",
                "Explanation":"No relevant source files were identified for this bug. A fix was not generated to avoid producing an unverified, speculative code change"
            }
            continue
        print(f"First attempt of bug fixing in progress for - {bug_id}")
        formatted_source = "\n\n".join(f"--{filepath}---\n{filecontent}" for filepath, filecontent in content.items())
        fixes[bug_id]["fix"] = analyse_code(bug_title,formatted_source,failed_fix)

    for bug_id, data in bugs_already_have_source.items():
        print(f"Finding another solution for {bug_id} as previous fix was rejected")
        bug_title = data.get("bug_title")
        failed_fix = fixes[bug_id]["previous_fix"]
        formatted_source = "\n\n".join(
            f"--{filepath}---\n{content}" for filepath, content in data.get('source_code').items())
        fixes[bug_id]["fix"] = analyse_code(bug_title, formatted_source,failed_fix)


    return {'code_analysis':fixes}