from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class BugRequest(BaseModel):
    project: str = "SCRUM"

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/analyse")
def analyse_bugs(request: BugRequest):
    from buganayser_agent import graph
    config = {"configurable":{"thread_id":"api_session_1"}}
    result = graph.invoke(
        {"jira":{},"claude":{},"analyse":{},"code_analysis":""},
        config
    )
    clean_result = {}

    for bug_id, data in result["code_analysis"].items():
        clean_result[bug_id] = {
            "bug_title": data.get("bug_title"," "),
            "relevant_files": data.get("relevant_files"," "),
            "fix": data.get("fix"," "),
        }

    return clean_result

