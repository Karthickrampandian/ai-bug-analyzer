import os
import requests
from requests.auth import HTTPBasicAuth
class jira_connector:
    def __init__(self):
        self.url = os.environ.get("JIRA_URL")
        self.email = os.environ.get("JIRA_EMAIL")
        self.token = os.environ.get("JIRA_TOKEN")

    def jira_connect(self):
        auth = HTTPBasicAuth(self.email, self.token)
        headers = {"Accept": "application/json"}

        response = requests.get(
            f"{self.url}/rest/api/3/search/jql",
            headers=headers,
            auth=auth,
            params={
                "jql": "project=TNR AND issuetype=Bug",
                "maxResults": 5,
                "fields": "summary,description,priority,status"
            }
        )
        return response.json()

    def get_bugs(self):
        bugs_list = {}
        bugs = self.jira_connect()
        for bug in bugs["issues"]:
            bugs_list[bug["key"]] = bug["fields"]["summary"]
        return bugs_list


