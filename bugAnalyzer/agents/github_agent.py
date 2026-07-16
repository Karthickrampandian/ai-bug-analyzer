from langgraph.types import interrupt
from github import Github
from config import GITHUB_PAT, GITHUB_REPO_OWNER, GITHUB_REPO_NAME
from models.state import bug_analyser
from config import SOURCE_DIR
import os
import time

def github_agent(state:bug_analyser):
    code_analysis = state.get("code_analysis",[])
    retry_bugs = {}
    approved_bugs = {}
    human_reject_count = state.get("human_reject_count",{})
    invalid_bugs = state.get("invalid_bugs",{})

    decisions = {}

    authenticate = Github(GITHUB_PAT)
    repo = authenticate.get_repo(f"{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}")
    retry_count = state.get("retry_count",{})
    for bug_id, fixed_data in code_analysis.items():
        if fixed_data["fix"].get("bug_location")=="INSUFFICIENT_CONTEXT":
            invalid_bugs[bug_id] = fixed_data
            print(f"{bug_id} has insufficient context — added to invalid_bugs for manual review")
            continue

        human_decision = interrupt({
            "bug_id": bug_id,
            "bug_title":fixed_data["bug_title"],
            "bug_code":fixed_data["fix"]["bug_code"],
            "fixed_code":fixed_data["fix"]["fixed_code"],
            "question":"Approve fix to be pushed as a PR?"
        })
        decisions[bug_id] = human_decision

        bug_code = fixed_data["fix"]["bug_code"]
        fixed_code = fixed_data["fix"]["fixed_code"]

    for bug_id, human_decision in decisions.items():
        fixed_data = code_analysis[bug_id]
        bug_code = fixed_data["fix"]["bug_code"]
        fixed_code = fixed_data["fix"]["fixed_code"]
        if human_decision == "yes":
            print(f"{bug_id}:{fixed_data['bug_title']} is approved by user after fix")
            branch_name = f"{bug_id}-{retry_count.get(bug_id,0)}-{int(time.time())}"
            sha = repo.get_branch("main").commit.sha
            repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=sha)
            relative_path = os.path.relpath(fixed_data["fix"].get("file_path",""), os.path.dirname(SOURCE_DIR))
            file = repo.get_contents(relative_path,ref=branch_name)
            content = file.decoded_content.decode("utf-8")
            updated_content = apply_fix_to_file(content,bug_code,fixed_code)
            # new_content = fixed_data["fix"].get("fixed_code","")
            repo.update_file(file.path,f"{bug_id}:{fixed_data['bug_title']}", updated_content, file.sha, branch=branch_name)
            repo.create_pull(title=f"Fix: {fixed_data['bug_title']}",body=f"Automated fix for {bug_id}",head=branch_name,base="main")
            approved_bugs[bug_id] = fixed_data
        else:
            current_attempts = human_reject_count.get(bug_id,0)
            human_reject_count[bug_id] = current_attempts+1
            print(f"{bug_id}:{fixed_data['bug_title']} rejected — attempt {human_reject_count[bug_id]}/2")
            if current_attempts >= 2:
                invalid_bugs[bug_id] = fixed_data
            else:
                retry_bugs[bug_id] = fixed_data
        # print(f"Human decisionfor {bug_id}: {human_decision}")

    # return {"analyse":state.get("analyse","")+" | GitHub agent reviewed"}

    return {"retry_bugs":retry_bugs,"approved_bugs":approved_bugs,"human_reject_count":human_reject_count,"invalid_bugs":invalid_bugs}

def apply_fix_to_file(file_content, bug_code, fixed_code):
    if bug_code in file_content:
        updated_content = file_content.replace(bug_code, fixed_code)
        return updated_content
    else:
        raise ValueError("Unable to find bug_code in this file")