from app.services.llm_service import ask_llm


def analyze_sources(question: str, sources: list) -> str:
    source_text = ""

    for i, source in enumerate(sources, start=1):
        source_text += f"""
Source {i}
Title: {source.get('title', '')}
URL: {source.get('url', '')}
Content: {source.get('content', '')}
"""

    prompt = f"""
You are a research evidence analyst.

Research question:
{question}

Analyze these web sources:

{source_text}

For each important finding:
1. State the claim.
2. Give the supporting evidence.
3. Mention the source number.
4. Identify uncertainty or limitations.

Do not invent facts that are not supported by the sources.

Return a structured evidence summary.
"""

    return ask_llm(prompt)