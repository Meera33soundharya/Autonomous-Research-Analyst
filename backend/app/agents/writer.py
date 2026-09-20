from app.services.llm_service import ask_llm


def generate_report(topic: str, verified_evidence: str) -> str:
    prompt = f"""
You are a professional research report writer.

Research Topic:
{topic}

Verified Evidence:
{verified_evidence}

Write a professional research report.

Use this structure:

# {topic}

## 1. Executive Summary

## 2. Introduction

## 3. Key Findings

## 4. Evidence Analysis

## 5. Challenges and Limitations

## 6. Future Opportunities

## 7. Conclusion

## References

Rules:
- Use only the verified evidence provided.
- Do not invent facts.
- Keep the writing clear and professional.
- Clearly distinguish evidence from assumptions.
- Include source names and URLs when they are available.
"""

    return ask_llm(prompt)