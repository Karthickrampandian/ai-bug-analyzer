from config import client
from models.state import bug_analyser


def supervisor(state:bug_analyser):

    valid_bugs = state.get("valid_bugs",{})

    if not valid_bugs:
        print("No valid bugs found")
        return {"valid_bugs":{}}

    p0_p1 = {k:v for k,v in valid_bugs.items() if v.get("severity") in ["P0","P1"]}
    p2_p3 = {k:v for k,v in valid_bugs.items() if v.get("severity") in ["P2","P3"]}


    print(f"🔴 Critical (P0/P1): {len(p0_p1)}")
    print(f"🟡 Low priority (P2/P3): {len(p2_p3)}")

    return {"valid_bugs":valid_bugs}

