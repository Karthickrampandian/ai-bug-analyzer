import streamlit as st
from bug_analyser import BugAnalyser

class bug_app:

    def __init__(self):
        self.analyser = BugAnalyser()

    def run(self):

        global result
        st.title("Bug Analyzer")

        bug_input = st.text_area("Bug Description", height=150)

        clicked = st.button("Verify Bug report")

        if clicked:
            if bug_input.strip() == "":
                st.error("Bug Reported Error")
            else:
                result = self.analyser.claude_connect(bug_input)
                st.write("Please find the results : " )
                st.write(result)

run = bug_app()
run.run()