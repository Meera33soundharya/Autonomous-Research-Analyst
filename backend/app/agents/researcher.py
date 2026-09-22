from app.services.llm_service import ask_llm


def clean_text(text: str) -> str:
    """Clean common webpage extraction problems."""
    if not text:
        return ""

    replacements = {
        "treatmentplanning": "treatment planning",
        "productiveand": "productive and",
        "sourcecontent": "source content",
        "theevidence": "the evidence",
        "standardclinical": "standard clinical",
        "limitthe": "limit the",
        "patientmonitoring": "patient monitoring",
        "clinicalsettings": "clinical settings",
        "medicalimaging": "medical imaging",
        "drugdiscovery": "drug discovery",
        "clinicaldecision": "clinical decision",
        "patientcare": "patient care",
        "healthcareAI": "healthcare AI",
        "healthcarebalance": "healthcare balance",
        "careapproaches": "care approaches",
        "andpotential": "and potential",
        "invarious": "in various",
        "theautonomous": "the autonomous",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return " ".join(text.split())


def analyze_sources(question: str, sources: list[dict]) -> dict:
    """Analyze all collected sources for one research question."""

    relevant_sources = []

    for source in sources:
        source_question = source.get("question", "").strip()

        if source_question == question:
            relevant_sources.append(source)

    if not relevant_sources:
        return {
            "question": question,
            "findings": []
        }

    source_text = []

    for index, source in enumerate(relevant_sources, start=1):
        title = clean_text(source.get("title", ""))
        url = source.get("url", "").strip()
        content = clean_text(source.get("content", ""))

        if not content:
            continue

        source_text.append(
            f"""
SOURCE {index}
Title: {title}
URL: {url}
Content:
{content[:5000]}
"""
        )

    if not source_text:
        return {
            "question": question,
            "findings": []
        }

    combined_sources = "\n".join(source_text)

    prompt = f"""
You are a research evidence extraction agent.

Research question:
{question}

Below are web sources collected for this question.

{combined_sources}

Task:
Extract factual findings that directly answer the research question.

Rules:
1. Use only information supported by the provided sources.
2. Do not invent facts.
3. Do not invent statistics.
4. Do not include webpage navigation or advertisements.
5. Each finding must be a complete sentence.
6. Create 3 to 5 concise findings.
7. Each finding must identify the source that supports it.
8. Do not combine unrelated information.
9. If the sources do not support a claim, do not include it.

Return exactly this format:

FINDING | SOURCE_NUMBER | CLAIM

Example:

FINDING | 1 | Artificial intelligence is used for medical image analysis.
FINDING | 2 | Artificial intelligence can support clinical decision making.
"""

    response = ask_llm(prompt)

    if not response:
        return {
            "question": question,
            "findings": []
        }

    findings = []

    for line in response.splitlines():
        line = line.strip()

        if not line.startswith("FINDING"):
            continue

        parts = line.split("|", 2)

        if len(parts) != 3:
            continue

        source_number = parts[1].strip()
        claim = clean_text(parts[2].strip())

        try:
            source_index = int(source_number) - 1
        except ValueError:
            continue

        if source_index < 0 or source_index >= len(relevant_sources):
            continue

        if len(claim) < 50:
            continue

        source = relevant_sources[source_index]

        findings.append(
            {
                "claim": claim,
                "source_title": clean_text(
                    source.get("title", "")
                ),
                "source_url": source.get("url", "").strip(),
                "source_content": clean_text(
                    source.get("content", "")
                ),
            }
        )

    return {
        "question": question,
        "findings": findings[:5],
    }