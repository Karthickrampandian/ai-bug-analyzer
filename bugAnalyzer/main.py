from graph import graph
import asyncio
from langgraph.types import Command


async def main():
    config = {"configurable": {"thread_id": "bug_session_3"}}

    async for chunk in graph.astream(
            {"jira": {}, "claude": {}, "analyse": "",
             "valid_bugs": {}, "retry_bugs": {}, "retry_count": {}},
            config):
        print(chunk)

        if "__interrupt__" in chunk:
            while True:
                print("Graph paused, waiting for human input")
                approval = input("Approve? (yes/no): ")

                got_interrupt = False
                async for inner_chunk in graph.astream(
                        Command(resume={"approved": approval.lower() == "yes"}),
                        config):
                    print(inner_chunk)
                    if "__interrupt__" in inner_chunk:
                        got_interrupt = True

                if not got_interrupt:
                    break


asyncio.run(main())

# "ui_bugs":{},
# "api_bugs":{},
# "db_bugs":{}},