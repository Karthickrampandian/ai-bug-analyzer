import os

import anthropic
import chromadb

JIRA_URL = os.environ.get('JIRA_URL')
JIRA_EMAIL = os.environ.get('JIRA_EMAIL')
JIRA_TOKEN = os.environ.get('JIRA_TOKEN')

#Anthropic Key
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
async_client = anthropic.AsyncAnthropic(api_key=ANTHROPIC_API_KEY)

#Source Directory
# SOURCE_DIR = os.environ.get('SOURCE_DIR','./src')
# config.py
SOURCE_DIR = os.environ.get("SOURCE_DIR", "/Users/karthick/Desktop/Learn_Playwright/learningpython/sample-app-web/src")

#ChromaDB
CHROMA_PATH = "./bug_vector"
COLLECTION_NAME = "bug_history"
DUPLICATE_THRESHOLD = 0.3
chroma = chromadb.PersistentClient(CHROMA_PATH)
collection = chroma.get_or_create_collection(COLLECTION_NAME)

# Hardcoded bugs for demo
HARDCODED_BUGS = {
    "SCRUM-10": "Login page accepts empty username without specific validation message",
    "SCRUM-11": "Cart badge count does not update immediately when item is removed",
    "SCRUM-12": "Checkout form allows submission with empty first name field"
}

# Prompts
CLAUDE_PROMPT = """You are a senior automation architect with over 10 years of experience, go through the bugs
    bug provided in the context and share with me the below details in json format:
    
       Rules :
       - UI: Visual mismatch, label changes, field name mismatch, page rendering, form validation
       - API: endpoint failures, response format, authentication, HTTP errors
       - Backend: database, business logic, data processing, server errors
       
    {
    "severity":"P0/P1/P2/P3",
    "priority":"High/Medium/Low/Critical",
    "title":"bug description",
    "component":"If the bug has component added it, else research and decide which component it belongs to",
    "bug_type":"UI/API/Backend"
    }
        
    Share the details in json format only, avoid any other information."""


# CLASSIFICATION_PROMPT = """You are a senior lead developer, your task is to classify bugs.
# Rules:
# - UI: Visual mismatch, label changes, field name mismatch, page rendering, form validation
# - API: endpoint failures, response format, authentication, HTTP errors
# - Backend: database, business logic, data processing, server errors
#
# Return strictly JSON:
# {
# "bug_type":"UI/API/Backend",
# "bug_summary":"Bug Summary from input",
# "bug_component":"Component from input"
# }
# No extra text. JSON only."""

BUG_DETAILS = {
    "severity": "",
    "priority": "",
    "component": "",
    "title": "",
    "bug_type": ""
}

FILE_IDENTIFICATION = """ You are a Lead developer, you task is to find the relevant files that is impacted by the bug.

Input:
1) Bug Summary
2) File path as str taken from the source code.

output:
{
bug_summary: "Bug Summary from input",
files_impacted:[Return full filepath list not only filenames. Example:filepath1,filepath2,filepath3]
}
output should be strictly in JSON format only. Analyse your response before coming to a conclusion. Return JSON only, avaoid explanation strictly.
"""

CODE_ANALYSIS_PROMPT="""You are Lead developer, your task it to fix the bug bsaed on the bug summary and source code file

output -
{
"bug_location" : "Function from the source code whether bug resides in" , 
"bug_code" : "Which code is causing that bug?", 
"fixed_code":"What is the fix that is suggested by claude along with the code?", 
"Explanation":"Why claude suggested that fix? Is it efficient/good fix?"
}

Output should be strictly in JSON format only. Analyse your response before coming to a conclusion."""