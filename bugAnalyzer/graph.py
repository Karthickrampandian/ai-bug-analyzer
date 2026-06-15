from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from models.state import bug_analyser
from agents.jira_agent import jira_connect
from agents.claude_agent import claude_connect
from agents.analyse_bug import analyse_bug
from agents.bug_classifier_agent import bug_classification
from agents.supervisor import supervisor
from agents.code_agent import code_agent
from agents.triage_agent import triage_agent
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

builder =StateGraph(bug_analyser)

builder.add_node("jira_connect",jira_connect)
builder.add_node("claude_connect",claude_connect)
builder.add_node("analyse_bug",analyse_bug)
builder.add_node("code_agent",code_agent)
builder.add_node("triage_agent",triage_agent)
builder.add_node("supervisor",supervisor)
builder.add_node("bug_classification",bug_classification)

builder.add_edge(START,"jira_connect")
builder.add_conditional_edges("jira_connect",route_after_jira,
                 {"no_bugs":END,
                  "analyse":"claude_connect"})
builder.add_edge("claude_connect","analyse_bug")
builder.add_edge("analyse_bug","bug_classification")
builder.add_edge("bug_classification","supervisor")
builder.add_conditional_edges("supervisor",route_after_supervisor,
                 {"code_agent": "code_agent",
                  "triage_agent":"triage_agent","end":END})

builder.add_edge("code_agent",END)
builder.add_edge("triage_agent",END)

memory = MemorySaver()
graph = builder.compile(checkpointer=memory)



