from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import RetryPolicy

from models.state import bug_analyser
from agents.jira_agent import jira_connect
from agents.claude_agent import claude_connect
from agents.analyse_bug import analyse_bug
# from agents.bug_classifier_agent import bug_classification
from agents.supervisor import supervisor
from agents.code_agent import code_agent
from agents.triage_agent import triage_agent
from agents.github_agent import github_agent
from agents.verify_agent import verify_agent
import asyncio

def route_after_jira(state:bug_analyser):
    if not state["jira"]:
        return "no_bugs"
    else:
        return "analyse"

def route_after_supervisor(state:bug_analyser):
    valid_bugs = state.get("valid_bugs",{})
    if not valid_bugs:
        return "end"

    for bug_id, analysis in valid_bugs.items():
        if analysis.get("severity") in ["P0","P1"]:
            return "code_agent"
    return "triage_agent"

def route_after_verify(state:bug_analyser):
    retry_bugs = state.get("retry_bugs",{})
    code_analysis = state.get("code_analysis",{})
    if not retry_bugs:
        if code_analysis:
            return "github_agent"
        return "end"
    else:
        return "code_agent"

def route_after_github(state:bug_analyser):
    retry_bugs = state.get("retry_bugs",{})
    if retry_bugs:
        return "code_agent"
    return "end"

builder =StateGraph(bug_analyser)

builder.add_node("jira_connect",jira_connect,retry_policy=RetryPolicy(max_attempts=3))
builder.add_node("claude_connect",claude_connect,retry_policy=RetryPolicy(max_attempts=3))
builder.add_node("analyse_bug",analyse_bug)
builder.add_node("code_agent",code_agent,retry_policy=RetryPolicy(max_attempts=3))
builder.add_node("verify_agent",verify_agent)
builder.add_node("triage_agent",triage_agent)
builder.add_node("supervisor",supervisor)
builder.add_node("github_agent",github_agent)
# builder.add_edge("code_agent",END)
# builder.add_node("bug_classification",bug_classification,retry_policy=RetryPolicy(max_attempts=3))

builder.add_edge(START,"jira_connect")
builder.add_conditional_edges("jira_connect",route_after_jira,
                 {"no_bugs":END,
                  "analyse":"claude_connect"})
builder.add_edge("claude_connect","analyse_bug")
builder.add_edge("analyse_bug","supervisor")
# builder.add_edge("bug_classification","supervisor")
builder.add_conditional_edges("supervisor",route_after_supervisor,
                 {"code_agent": "code_agent",
                  "triage_agent":"triage_agent","end":END})

builder.add_edge("code_agent","verify_agent")

builder.add_conditional_edges("verify_agent",route_after_verify,
                              {
                                  "github_agent":"github_agent",
                                  "code_agent":"code_agent",
                                  "end":END
                              })

builder.add_conditional_edges("github_agent", route_after_github,
    {"code_agent": "code_agent", "end": END})

builder.add_edge("triage_agent",END)

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)



