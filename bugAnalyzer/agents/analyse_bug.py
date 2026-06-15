from config import collection
from models.state import bug_analyser


def analyse_bug(state:bug_analyser):

    valid_bugs = {}
    duplicate_bugs = {}

    for bug, details in state["claude"].items():
        title = details.get("title","")
        similar = collection.query(query_texts=[title],n_results=2)
        distances = similar["distances"][0] if similar["distances"] else[]
        documents = similar["documents"][0] if similar["documents"] else[]

        if distances and distances[0] < 0.3 and documents:
            duplicate_bugs[bug] = details
        else:
            valid_bugs[bug] = details

        collection.upsert(
            documents=[title],
            metadatas=[{"bug_id":bug}],
            ids=[bug],
        )

    print(f"✅ Valid: {len(valid_bugs)} bugs")
    print(f"⚠️ Duplicates: {len(duplicate_bugs)} bugs")

    return {"analyse": f"Valid Bugs: {len(valid_bugs)}, Duplicate bugs:{len(duplicate_bugs)}",
                "valid_bugs":valid_bugs}



