from app.agents.planner import create_research_plan


topic = "Artificial Intelligence in healthcare"

result = create_research_plan(topic)

print("\n===== RESEARCH PLAN =====\n")
print(result)