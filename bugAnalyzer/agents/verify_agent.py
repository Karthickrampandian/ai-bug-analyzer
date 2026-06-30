from models.state import bug_analyser

def verify_agent(state:bug_analyser):
    code_analysis=state.get('code_analysis',{})
    retry_count = state.get('retry_count',{})

    valid_bugs = {}
    invalid_bugs = {}

    for bug_id, fixed_data in code_analysis.items():

        if fixed_data["fix"]["bug_location"] == "INSUFFICIENT_CONTEXT":
            valid_bugs[bug_id] = fixed_data
            continue

        current_attempts = retry_count.get(bug_id,0)

        is_valid = fixed_data["fix"]["fixed_code"] != fixed_data["fix"]["bug_code"]

        if is_valid or current_attempts >=2:
            valid_bugs[bug_id] = fixed_data

        else:
            invalid_bugs[bug_id] = fixed_data
            retry_count[bug_id] = current_attempts + 1

    return {"code_analysis":valid_bugs,"retry_count":retry_count,"retry_bugs":invalid_bugs}