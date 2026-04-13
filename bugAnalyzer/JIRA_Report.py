import pandas as pd
import os

class JIRA_REPORT:
    def __init__(self, data,date,userselection):
        self.data = data
        self.date = date
        self.userselection = userselection

    def report(self):
        df = self.data.copy()
        if "suggestion" in df.columns:
            df["suggestion"] = df["suggestion"].apply(lambda x: "\n".join(x) if isinstance(x, list) else x)
            date_str = self.date.strftime("%Y-%m-%d")
            filename = f"bug_report_{date_str}.csv"

            if os.path.exists(filename):
                if self.userselection == "Append":
                    self.data.to_csv(filename, mode="a", index=False, header=False)
                else:
                    self.data.to_csv(filename, mode="w", index=False)
            else:
                print("File not found, Creating a new file")
                self.data.to_csv(filename, index=False)





