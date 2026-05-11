import chromadb

client = chromadb.Client()

collection = client.create_collection(name="bug_reports")

collection.add(
    documents=[  "Login button crashes on mobile Safari",
        "Login fails on iPhone browser after password reset",
        "Payment page not loading on slow 3G connection",
        "Checkout page throws 500 error on submit",
        "User profile picture not updating after save"],
    ids=["bug1", "bug2", "bug3", "bug4", "bug5"]
)

print("Collection Created:",collection.name)
print("Bugs were added successfully")

results = collection.query(
    query_texts=["Login problem on mobile"],
    n_results = 2,
)

print(results["documents"])    # outer list
print(results["documents"][0]) # first query results
print(results["ids"])          # see the IDs too
print(results["distances"])

print ("Query: login problem on mobile")
print("Similar bugs found")
for r,distance in zip(results["documents"][0],results["distances"][0]):
    if distance < 1.0:
        print(f"{r} (Distance:{distance: .2f})")
    else:
        print(f"Week match:{r} (Distance: {distance: .2f})")
