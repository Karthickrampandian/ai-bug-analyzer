from pydantic import BaseModel

class BugRequest(BaseModel):
    project: str = "SCRUM"

class FixDetail(BaseModel):
    bug_location:str
    bug_code:str
    fixed_code:str
    explanation:str

class BugResult(BaseModel):
    bug_title:str
    relevant_files:list
    fix:dict


