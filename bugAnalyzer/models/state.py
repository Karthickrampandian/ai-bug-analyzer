from typing_extensions import TypedDict

class bug_analyser(TypedDict):
    jira: dict
    claude: dict
    analyse: str
    code_analysis: dict
    valid_bugs: dict
    ui_bugs: dict
    api_bugs: dict
    db_bugs: dict