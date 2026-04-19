import anthropic
import os

class Cucumber_Generation():
    def __init__(self):
        self.feature = "feature"
        self.step_definition = "step_definition"
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.max_tokens = 2000
        self.file_path = os.path.join(os.getcwd(), "output.feature")
        self.model = "claude-haiku-4-5-20251001"
        self.feature_prompt = """You are a senior automatio engineer and your task is to analyse the ticket and create feature file for it in gherkin format. avoid unwanted infromation and output should only be in gherkin format
                              examples: 
                              Feature: Validate the search functionality for the declaration system
                              
                              background: login to the system and impersonate as this user
                              Scenario: verify the search screen functionality of {which screen or module} 
                              Given I navigate to this {module}
                              When I select the unt code 
                              And I key in the search filters
                              And I click on search button
                              And i verify records generation
                              
                              Ensure you create multiple scenarios to cover all scenario combinations.  
                    
                              """
        self.step_definition_prompt = """
        Your task it to analyse the feature file and create step definition for each line and avoid duplicate step definition.
        Step definition should be in kotlin format, dont look for locators just create the skeleton.
        """

    def write_feature(self,file,result,ticket):
        if file.lower() == self.feature:
            folder = "features"
            filename = f"{ticket}.feature"
        elif file.lower() == self.step_definition:
            folder = "step_definitions"
            filename = f"{ticket}.kt"
        os.makedirs(folder, exist_ok=True)

        with open(os.path.join(folder, filename), "w") as f:
            f.write(result)

    def read_feature(self,ticket):
        with open(os.path.join("features", f"{ticket}.feature"), "r") as f:
            return f.read()

    def generate_feature(self,ticket,summary):
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=self.feature_prompt,
            messages =[{"role":"user","content":summary}]
        )
        result = response.content[0].text.replace("gherkin","").replace("```","")
        self.write_feature(self.feature,result,ticket)

    def generate_stepdefinitions(self,ticket):
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=self.step_definition_prompt,
            messages =[{"role":"user","content":self.read_feature(ticket)}]
        )
        result = response.content[0].text.replace("gherkin","").replace("```","")
        self.write_feature(self.step_definition,result,ticket)

    def generate_cucumberTests(self,ticket,summary):
        self.generate_feature(ticket,summary)
        self.generate_stepdefinitions(ticket)
