from config import JIRA_URL, JIRA_EMAIL,JIRA_TOKEN, HARDCODED_BUGS
from models.state import bug_analyser
import requests
from requests.auth import HTTPBasicAuth


def jira_connect(state:bug_analyser):
    if not JIRA_URL:
        print("⚠️ No Jira URL — using hardcoded bugs")
        return {"jira": HARDCODED_BUGS}

    bug_list = {}
    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_TOKEN)
    headers = {"content-type": "application/json"}
    payload = {"jql":"project=SCRUM AND issuetype=BUG",
               "maxResults":10,
               "fields":["summary","description","priority","status"]}

    resource = requests.post(f"{JIRA_URL}/rest/api/3/search/jql", headers=headers, auth=auth,json=payload)

    data = resource.json()

    for bug in data["issues"]:
        bug_list[bug["id"]] = bug["fields"]["summary"]

    return {"jira":HARDCODED_BUGS}
