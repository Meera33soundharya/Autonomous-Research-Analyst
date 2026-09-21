from app.graph.workflow import research_graph


result = research_graph.invoke({
    "topic": "Artificial Intelligence in Healthcare"
})


print("\n================================")
print("AUTONOMOUS RESEARCH ANALYST")
print("================================")

print("\nTOPIC:")
print(result["topic"])

print("\nRESEARCH QUESTIONS:")
for question in result["research_questions"]:
    print("-", question)

print("\nVERIFIED EVIDENCE:")

for item in result["verified_evidence"]:

    print("\nQuestion:")
    print(item["question"])

    for finding in item["findings"]:

        print("\nClaim:")
        print(finding["claim"])

        print("Source:")
        print(finding["source"])

        print("URL:")
        print(finding["url"])

        print("Status:")
        print(finding["status"])

print("\n================================")
print("FINAL RESEARCH REPORT")
print("================================")

print(result["report"])