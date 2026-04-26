import anthropic
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="python3.11",
        args=["server_MCP.py"]
    )

    async with stdio_client(server_params) as (read,write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()

            anthropic_tools = [
                {
                    "name":tool.name,
                    "description":tool.description,
                    "input_schema":tool.inputSchema,
                }
                for tool in tools.tools
            ]

            client = anthropic.Anthropic()

            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=500,
                tools=anthropic_tools,
                messages=[{"role": "user", "content": "What is tbe test coverage for total cases 1028 and 898 passed? Also analyse and give me severity tip for a loggin bug with 70% seeverity?"}]
            )

            print(response)

            while response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                       result = await session.call_tool(block.name, block.input)
                       tool_results.append({
                           "type":"tool_result",
                           "tool_use_id":block.id,
                           "content":str(result.content[0].text)
                       })
                messages=[
                    {
                        "role":"user","content":"What is tbe test coverage for total cases 1028 and 898 passed? Also analyse and give me severity tip for a loggin bug with 80% seeverity?"
                    },
                    {
                        "role":"assistant","content":response.content
                    },
                    {
                        "role":"user","content":tool_results
                    }
                ]

                response = client.messages.create(
                        model="claude-haiku-4-5-20251001",
                        max_tokens=500,
                        tools=anthropic_tools,
                        messages=messages
                    )
                print(f"Final answer: {response.content[0].text}")

asyncio.run(main())