from graph import graph
import asyncio
from langgraph.types import Command


async def main():
    config = {"configurable": {"thread_id": "bug_session_3"}}

    async for chunk in graph.astream(
            {"jira": {}, "claude": {}, "analyse": "",
             "valid_bugs": {}, "retry_bugs": {}, "retry_count": {}},
            config):
        for node_name, node_output in chunk.items():

            if node_name == "__interrupt__":
                continue
            print(f"[{node_name}] completed")

        if "__interrupt__" in chunk:
            interrupt_data = chunk["__interrupt__"][0].value
            print(f"{interrupt_data.get('bug_id')} - {interrupt_data.get('bug_title')} ")  # bug_id, bug_title
            print(f"Buggy code - \n {interrupt_data.get('bug_code')}")  # bug_code
            print(f"Fixed code - \n {interrupt_data.get('fixed_code')}")  # fixed_code
            while True:
                print("Graph paused, waiting for human input")
                approval = input("Approve? (yes/no): ")
                got_interrupt = False
                async for inner_chunk in graph.astream(
                        Command(resume= approval.lower()),
                        config):
                    for node_name, node_output in inner_chunk.items():
                        if node_name == "__interrupt__":
                            continue
                        print(f"[{node_name}] completed")
                    if "__interrupt__" in inner_chunk:
                        interrupt_data = inner_chunk["__interrupt__"][0].value
                        print(f"{interrupt_data.get('bug_id')} - {interrupt_data.get('bug_title')} ")
                        print(f"Buggy code - \n {interrupt_data.get('bug_code')}")
                        print(f"Fixed code - \n {interrupt_data.get('fixed_code')}")
                        got_interrupt = True

                if not got_interrupt:
                    break


asyncio.run(main())

# "ui_bugs":{},
# "api_bugs":{},
# "db_bugs":{}},