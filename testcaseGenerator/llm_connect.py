import anthropic
import os

class LlmConnect:
    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-haiku-4-5-20251001"
        self.max_tokens = 2000
        self.jira_jql_prompt = """
        You are JIRA admin, your task is to generate a proper JQL based on user input. 
        
        For ticket_ID:
        
        if the input is a ticket_id then search using the ticket ID and retrieve jql in below format, avoid unwanted analysis
        "project = TNR
        AND (textfields ~ "TNR-15947" OR issuekey = "TNR-15947")
        ORDER BY updated DESC"
        
        if the input is a project_name then search using the project ID and retrieve below sql format, avoid unwanted analysis
        "project = TNR
        ORDER BY updated DESC"
        
        Output should be a JQL, avoid any other unwanted information
        """
        self.system_prompt = "Retrieve JQL for this:"

    def llm_connect(self,jira_id):
        response = self.client.messages.create(
                model= self.model,
                max_tokens=self.max_tokens,
                system=self.system_prompt,
                messages = [
                    {
                        "role":"user",
                        "content":self.jira_jql_prompt +jira_id
                    }
                ]
            )
        result = response.content[0].text.replace("```","").replace("jql","")
        # print(f"JQL result: {result}")
        return result
