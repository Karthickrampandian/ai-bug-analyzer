import streamlit as st
from JIRA_CONNECT import JiraConnect
from Cucumber_Generation import Cucumber_Generation

st.title("Test Case Generator")
ticket_id = st.text_input("Enter Jira Ticket ID:")

if st.button("Generate"):
    jira = JiraConnect(ticket_id)
    tickets = jira.get_description()
    st.session_state['tickets'] = tickets

    cucumber = Cucumber_Generation()
    for tid, summary in tickets.items():
        cucumber.generate_cucumberTests(str(tid), summary)

    st.session_state['generated'] = True

if st.session_state.get('generated'):
    tickets = st.session_state['tickets']
    tabs = st.tabs(list(tickets.keys()))

    for tab, (tid, summary) in zip(tabs, tickets.items()):
        with tab:
            st.subheader(summary)
            col1, col2 = st.columns(2)

            with open(f"features/{tid}.feature", "r") as f:
                feature_content = f.read()
            with open(f"step_definitions/{tid}.kt", "r") as f:
                kt_content = f.read()

            with col1:
                st.code(feature_content, language="gherkin")
                st.download_button("Download Feature",
                                   data=feature_content,
                                   file_name=f"{tid}.feature",
                                   key=f"feature_{tid}")
            with col2:
                st.code(kt_content, language="kotlin")
                st.download_button("Download Steps",
                                   data=kt_content,
                                   file_name=f"{tid}.kt",
                                   key=f"steps_{tid}")