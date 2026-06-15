# bugs = [
#     {"id": "SCRUM-10", "severity": "P1"},
#     {"id": "SCRUM-11", "severity": "P2"},
#     {"id": "SCRUM-12", "severity": "P1"},
# ]
#
# p1_bugs = [bug.get("id") for bug in bugs if bug.get("severity") == "P1"]
# print(p1_bugs)
#
# data = {}
# data.setdefault("bugs", []).append("SCRUM-10")
# data.setdefault("bugs", []).append("SCRUM-11")
# print(data)

def get_top_chunks(results: dict, top_n=3):
    docs = results["documents"]
    print(docs[0][:top_n])
    return docs[0][:top_n]

results = {"documents": [["doc1", "doc2", "doc3", "doc4"]]}
top = get_top_chunks(results)
print(len(top))  # expected: 3, actual: ?