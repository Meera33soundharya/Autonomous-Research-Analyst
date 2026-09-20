from app.graph.workflow import research_graph


topic = "Artificial Intelligence in Healthcare"


result = research_graph.invoke({
    "topic": topic
})


print("\n===== RESEARCH PLAN =====\n")
print(result.get("research_plan"))


print("\n===== SEARCH QUESTIONS =====\n")
print(result.get("questions"))


print("\n===== EVIDENCE =====\n")
print(result.get("evidence"))


print("\n===== VERIFIED EVIDENCE =====\n")
print(result.get("verified_evidence"))


print("\n===== FINAL RESEARCH REPORT =====\n")
print(result.get("report"))