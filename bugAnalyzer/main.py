from graph import graph
import asyncio

async def main():
    config = {"configurable":{"thread_id":"bug_session_1"}}
    async for chunk in graph.astream(
            {"jira":{},
             "claude":{},
             "analyse":"",
             "valid_bugs":{}},
            config):
        print(chunk)

asyncio.run(main())

# "ui_bugs":{},
# "api_bugs":{},
# "db_bugs":{}},