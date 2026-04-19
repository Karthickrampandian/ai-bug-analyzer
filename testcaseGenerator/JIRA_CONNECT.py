import os
import streamlit as st
import requests
from requests.auth import HTTPBasicAuth

from llm_connect import LlmConnect
from dotenv import load_dotenv
load_dotenv()

class JiraConnect:
    def __init__(self, data):
       try:
           self.llm = LlmConnect()
           self.jira_id = data
           self.url = st.secrets.get("TEST_JIRA_URL") or os.environ.get("TEST_JIRA_URL")
           self.email = st.secrets.get("TEST_JIRA_EMAIL") or os.environ.get("TEST_JIRA_EMAIL")
           self.token = st.secrets.get("TEST_JIRA_TOKEN") or os.environ.get("TEST_JIRA_TOKEN")
       except Exception:
            self.url =os.environ.get("TEST_JIRA_URL")
            self.email = os.environ.get("TEST_JIRA_EMAIL")
            self.token = os.environ.get("TEST_JIRA_TOKEN")

    def jira_connect(self):
        auth = HTTPBasicAuth(self.email, self.token)
        headers = {"Content-Type": "application/json"}
        response = requests.get(
            url = f"{self.url}/rest/api/3/search/jql/",
            auth = auth,
            headers = headers,
            params = {
                "jql":self.llm.llm_connect(self.jira_id),
                "maxResults":15,
                "fields":"summary, description, priority, status"
            }
        )
        return response.json()

    def get_description(self):
        response = self.jira_connect()
        bug_list = {}
        for bug in response["issues"]:
            bug_list[bug["key"]] = bug["fields"]["summary"]
        return bug_list




