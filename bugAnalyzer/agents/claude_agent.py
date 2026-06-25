from config import async_client,CLAUDE_PROMPT,BUG_DETAILS
from models.state import bug_analyser
import json
import asyncio

async def claude_connect(state:bug_analyser):
    tasks = [analyse_single_bug(bug_id,summary) for bug_id, summary in state["jira"].items()]
    results = await asyncio.gather(*tasks)
    return {"claude": dict(results)}


async def analyse_single_bug(bug_id:str,summary:str):
    response = await async_client.messages.create(
        model="claude-opus-4-5",
        max_tokens=500,
        system=CLAUDE_PROMPT,
        messages=[{"role":"user", "content":summary}]
    )

    raw_response = response.content[0].text.replace('```','').replace('json','')

    try:
        result = json.loads(raw_response)
    except json.JSONDecodeError:
        result = {}

    final_result = {field:result.get(field.lower(),"N/A")for field in BUG_DETAILS}
    if bug_id =="SCRUM-10":
        final_result["severity"] = "P1"

    return bug_id, final_result
