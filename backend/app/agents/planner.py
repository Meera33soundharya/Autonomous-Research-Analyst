from app.services.llm_service import ask_llm


def create_research_plan(topic: str) -> str:
    prompt = f"""
You are a research planning agent.

Research topic:
{topic}

Create a clear research plan for this topic.

Return:
1. Main research objective
2. 5 important research questions
3. Key areas to investigate
4. Types of sources required

Keep the output concise and structured.
"""

    return ask_llm(prompt)