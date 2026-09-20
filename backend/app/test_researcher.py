from app.services.search_service import search_web
from app.agents.researcher import analyze_sources


question = "How is artificial intelligence being used in healthcare?"

sources = search_web(question)

print("SOURCES FOUND:", len(sources))

result = analyze_sources(question, sources)

print("\n===== EVIDENCE ANALYSIS =====\n")
print(result)