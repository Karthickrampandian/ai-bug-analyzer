from models.state import bug_analyser

def verify_agent(state:bug_analyser):
    code_analysis=state.get('code_analysis',{})
    retry_count = state.get('retry_count',{})

    valid_bugs = {}
    invalid_bugs = {}

    for bug_id, fixed_data in code_analysis.items():

        if fixed_data["fix"]["bug_location"] == "INSUFFICIENT_CONTEXT":
            valid_bugs[bug_id] = fixed_data
            print(
                f"{bug_id} does not have enough information (like source code, file location, bug description is not clear, etc ) to be fixed")
            continue

        current_attempts = retry_count.get(bug_id,0)

        is_valid = fixed_data["fix"]["fixed_code"] != fixed_data["fix"]["bug_code"]

        if is_valid :
            valid_bugs[bug_id] = fixed_data
            print(f"As all the details are correct for {bug_id}, it is added to valid_bugs dictionary")
        elif current_attempts >=2:
            valid_bugs[bug_id] = fixed_data
            print(f"As {bug_id} could not be fixed after multiple attempts, we are adding it to valid_bugs dictionary")
        else:
            invalid_bugs[bug_id] = fixed_data
            retry_count[bug_id] = current_attempts + 1
            print(f"{bug_id} is failed fix, sent back for fix again to coding agent.")

    return {"code_analysis":valid_bugs,"retry_count":retry_count,"retry_bugs":invalid_bugs}