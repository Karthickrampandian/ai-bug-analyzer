from models.state import bug_analyser

def triage_agent(state:bug_analyser):
    valid_bugs = state.get("valid_bugs",{})

    print("🟡 Triage agent processing low priority bugs...")

    for bug_id, analysis in valid_bugs.items():
        print(f"-> {bug_id} : {analysis.get('title','')} [{analysis.get('severity','')}]")

    return {"analyse": state["analyse"] + "| Triage Complete"}