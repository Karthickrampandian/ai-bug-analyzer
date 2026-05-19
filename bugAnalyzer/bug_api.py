import uuid
import time

from fastapi import FastAPI, HTTPException

from buganayser_agent import graph

app = FastAPI()

from models import BugRequest

def invoke_with_retry(graph,input_data,config,max_retries=3):
    for i in range(max_retries):
        try:
            return graph.invoke(input_data,config)
        except Exception as e:
            if "overloaded" in str(e) or "529" in str(e) :
                wait = 2 ** i
                print(f"overloaded. Retrying in {wait} seconds...")
                time.sleep(wait)
            else:
                raise

    raise HTTPException(status_code=503, detail= "AI service temporarily busy. Please try again later.")


@app.get("/")
def health():
    return {"status": "ok"}

@app.post("/analyse")
def analyse_bugs(request: BugRequest):
    thread_id = str(uuid.uuid4())
    config = {"configurable":{"thread_id":thread_id}}
    try:
        result = invoke_with_retry(graph,
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

  

