from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Learning Server")

@mcp.tool()
def add_numbers(a:int, b:int) -> int:
    """Add two numbers together"""
    return a +b

@mcp.tool()
def get_testing_tip(topic:str) -> str:
    """Get a testing tip for a given topic"""
    tips = {
        "api": "Always test status codes, response schema, and error handling",
        "ui": "Use data-testid attributes for stable locators",
        "performance": "Test under realistic load, not just peak load"
    }
    return tips.get(topic.lower(),"Write tests that reflect real user behaviour")

if __name__ == "__main__":
    mcp.run()