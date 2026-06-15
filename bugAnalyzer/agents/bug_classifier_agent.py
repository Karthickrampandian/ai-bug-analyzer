import json
from config import async_client,CLASSIFICATION_PROMPT
from models.state import bug_analyser
import asyncio


async def bug_classification(state:bug_analyser):
    tasks = [classify_single_bug(bug_id, f"Title:{bug.get('title','')} component:{bug.get('component','')}") for bug_id, bug in state["valid_bugs"].items()]
    results = await asyncio.gather(*tasks)

    ui_bugs = {}
    api_bugs = {}
    db_bugs = {}

    for bug_id,classification in results:
        bug_type = classification.get('bug_type',"UI")

        if bug_type == "UI":
            ui_bugs[bug_id] = classification
        elif bug_type == "API":
            api_bugs[bug_id] = classification
        elif bug_type == "DB":
            db_bugs[bug_id] = classification

    return {"ui_bugs": ui_bugs,
            "api_bugs": api_bugs,
            "db_bugs": db_bugs}


async def classify_single_bug(bug_id:str, summary:str):
    response = await async_client.messages.create(
        model="claude-opus-4-5",
        max_tokens=500,
        system=CLASSIFICATION_PROMPT,
        messages=[{"role": "user", "content": summary}]
    )

    raw_response = response.content[0].text.replace("```", " ").replace("json","")

    try:
        result = json.loads(raw_response)
    except json.JSONDecodeError:
        print(f"Invalid json format for {bug_id}")
        result={}

    return bug_id, result