from app.services.llm_service import ask_llm


def check_citations(evidence: str) -> str:
    prompt = f"""
You are a citation verification agent.

Review the following research evidence:

{evidence}

For every important claim:

1. Identify the claim.
2. Identify the supporting source.
3. Check whether the evidence actually supports the claim.
4. Mark the claim as:
   - SUPPORTED
   - PARTIALLY SUPPORTED
   - UNSUPPORTED
5. Explain the reason briefly.

Do not add new facts.
Do not invent sources.
Only evaluate the evidence provided.

Return a structured citation verification report.
"""

    return ask_llm(prompt)