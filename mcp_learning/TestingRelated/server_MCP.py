from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Learning Server based MCP")

@mcp.tool()
def calculate_test_coverage(total_tests, passed_tests) -> float:
    """Calculate the test coverage using provided test count"""
    total= int(total_tests)
    passed = int(passed_tests)
    if total == passed:
        return 100
    else:
        return (passed/total) * 100

@mcp.tool()
def get_bug_severity_tipe(severity:str) -> str:
    """Generate the bug severity using provided severity"""
    severity_num = float(str(severity).replace("%", "").strip())
    if severity_num >= 90:
        return "P0"
    elif severity_num>=70 :
        return "P1"
    elif  severity_num >= 50:
        return "P2"
    else:
        return "P3"


if __name__ == '__main__':
    mcp.run()
