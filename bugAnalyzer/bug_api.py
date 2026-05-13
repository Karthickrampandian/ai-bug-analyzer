import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from buganayser_agent import graph

app = FastAPI()

class BugRequest(BaseModel):
    project: str = "SCRUM"

@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/analyse")
def analyse_bugs(request: BugRequest):
    thread_id = str(uuid.uuid4())
    config = {"configurable":{"thread_id":thread_id}}
    try:
        result = graph.invoke(
            {"jira":{},"claude":{},"analyse":{},"code_analysis":""},
            config
        )

        if not result:
            return {"message":"No bugs found","bugs":{}}

        clean_result = {}
        for bug_id, data in result["code_analysis"].items():
            clean_result[bug_id] = {
                "bug_title": data.get("bug_title", " "),
                "relevant_files": data.get("relevant_files", " "),
                "fix": data.get("fix", " "),
            }
        return clean_result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

  

