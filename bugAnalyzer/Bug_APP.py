import streamlit as st
from bug_analyser import BugAnalyser
import pandas as pd

class bug_app:

    def __init__(self):
        self.analyser = BugAnalyser()

    def run(self):

        global result, solution
        st.set_page_config(layout="wide")
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
                    if isinstance(suggestions,dict):
                         for role,text in suggestions.items():
                             st.markdown(f"**{role.title()}:** {text}")
                    elif isinstance(suggestions, list):
                        for s in suggestions:
                            st.markdown(f"- {s}")
                    else:
                        st.write(suggestions)

                    code_analysis = solution.get("code_analysis", "")
                    if code_analysis:
                        st.markdown("**🔍 Code Analysis:**")
                        if isinstance(code_analysis, dict):
                            st.write(f"**Bug Location:** {code_analysis.get('bug_location', 'N/A')}")
                            st.write(f"**Bug Explanation:** {code_analysis.get('explanation', 'N/A')}")
                            col1,col2 = st.columns(2)
                            col1.header("**🐛 Buggy Code:**")
                            buggy = code_analysis.get('bug_code', '').replace('\\n', '\n')
                            col1.code(buggy, language='javascript')

                            col2.header("**✅ Fixed Code:**")
                            fixed = code_analysis.get('fix_code', '').replace('\\n', '\n')
                            col2.code(fixed, language='javascript')

                        if "changed_lines" in code_analysis:
                            st.write("**📍 What Changed:**")
                            st.code(code_analysis.get("changed_lines", ""), language='javascript')
                            st.write("** Verification **")
                            st.info(code_analysis.get("fix_verification", ""))

                        fix_verification = solution.get("fix_verification", "")
                        if fix_verification:
                            verdict = fix_verification.get("verdict", "N/A")
                            confidence = fix_verification.get("confidence", "N/A")
                            reason = fix_verification.get("reason", "N/A")

                            if verdict == "APPROVED":
                                st.success(f"✅ {verdict} — Confidence: {confidence}% | {reason}")
                            else:
                                st.warning(f"⚠️ {verdict} — Confidence: {confidence}% | {reason}")
                        else:
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
        st.info(
            f"Total tokens used — Input: {self.analyser.total_input_tokens} | Output: {self.analyser.total_output_tokens} | Est. cost: ${((self.analyser.total_input_tokens * 0.000015) + (self.analyser.total_output_tokens * 0.000075)):.4f}")

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
