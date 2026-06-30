from langgraph.types import interrupt

from models.state import bug_analyser

def github_agent(state:bug_analyser):

    code_analysis = state.get("code_analysis",[])

    for bug_id, fixed_data in code_analysis.items():
        if fixed_data["fix"].get("bug_location")=="INSUFFICIENT_CONTEXT":
            continue

        human_decision = interrupt({
            "bug_id": bug_id,
            "bug_title":fixed_data["bug_title"],
            "bug_code":fixed_data["fix"]["bug_code"],
            "fixed_code":fixed_data["fix"]["fixed_code"],
            "question":"Approve fix to be pushed as a PR?"
        })

        print(f"Human decisionfor {bug_id}: {human_decision}")

    return {"analyse":state.get("analyse","")+" | GitHub agent reviewed"}
