import streamlit as st
from bug_analyser import BugAnalyser
import pandas as pd

class bug_app:

    def __init__(self):
        self.analyser = BugAnalyser()

    def run(self):

        global result, solution
        st.title("Bug Analyzer")

        bug_input = st.date_input("Select Report date")
        mode = st.radio("If file exists:", ["Append", "Overwrite"])

        if st.button("Verify Bug report"):
            with st.spinner("Claude is analyzing your bugs... please wait"):
                result = self.analyser.claude_connect(bug_input)

            rows = []
            for bug_ID, solution in result.items():
                with st.expander(f"{bug_ID} - {solution.get('title', '')}"):
                    similar = solution.get("similar_bugs", [])
                    if similar:
                        st.markdown("**🔍 Similar Past Bugs:**")
                        for s in similar:
                            st.markdown(f"- {s}")

                    col1,col2, col3 = st.columns(3)
                    col1.metric("Severity",solution.get("severity", ""))
                    col2.metric("Priority",solution.get("priority", ""))
                    col3.markdown(f"**Component**\n\n {solution.get('component', '')}")
                    st.markdown("**Suggestion:**")
                    suggestions = solution.get("suggestion",[])
                    if isinstance(suggestions,list):
                         for s in suggestions:
                             st.markdown(f"- {s}")
                    else:
                        st.write(suggestions)

                    code_analysis = solution.get("code_analysis", "")
                    if code_analysis:
                        st.markdown("**🔍 Code Analysis:**")
                        st.markdown(code_analysis)
                    matched_files = solution.get("matched_files", [])
                    if matched_files:
                        st.markdown("**📁 Files Analyzed:**")
                        for f in matched_files:
                            st.code(f)
                #Build rows for export - OUTSIDE expander
                if isinstance(solution, dict):
                    solution["bugID"] = bug_ID
                    rows.append(solution)
            if rows:
                bugtable = pd.DataFrame(rows)
                st.session_state["bugtable"] = bugtable

                # csv = bugtable.to_csv(index=False)
                # st.download_button(
                #     label="Download Bug Report",
                #     data=csv,
                #     file_name=f"bug_report_{bug_input}.csv",
                #     mime="text/csv")
            else:
                st.warning("No bugs found.")

        if "bugtable" in st.session_state:
            csv  = st.session_state["bugtable"].to_csv(index=False)
            st.download_button(
                label="⬇️ Download Bug Report",
                data=csv,
                file_name=f"bug_report_{bug_input}.csv",
                mime="text/csv"
            )

run = bug_app()
run.run()
