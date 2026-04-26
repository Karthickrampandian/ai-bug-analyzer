import os
import requests
from requests.auth import HTTPBasicAuth
import streamlit as st

class jira_connector:
    def __init__(self):
        try:
            self.url = st.secrets.get("TEST_JIRA_URL") or os.environ.get("TEST_JIRA_URL")
            self.email = st.secrets.get("TEST_JIRA_EMAIL") or os.environ.get("TEST_JIRA_EMAIL")
            self.token = st.secrets.get("TEST_JIRA_TOKEN") or os.environ.get("TEST_JIRA_TOKEN")
        except Exception:
            self.url = os.environ.get("TEST_JIRA_URL")
            self.email = os.environ.get("TEST_JIRA_EMAIL")
            self.token = os.environ.get("TEST_JIRA_TOKEN")

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
        # bugs = self.jira_connect()
        # for bug in bugs["issues"]:
        #     bugs_list[bug["key"]] = bug["fields"]["summary"]
        # return bugs_list

        return {
            "SCRUM-10": "Login page accepts empty username without specific validation message",
            "SCRUM-11": "Cart badge count does not update immediately when item is removed",
            "SCRUM-12": "Checkout form allows submission with empty first name field"
        }


