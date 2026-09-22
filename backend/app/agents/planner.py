import re

from app.services.llm_service import ask_llm


def clean_question(question: str) -> str:
    """Clean and normalize a generated research question."""

    if not question:
        return ""

    question = question.strip()

    # Remove bullets
    question = question.lstrip("-• ")

    # Remove numbering such as 1. / 2.
    if "." in question[:4]:
        prefix, rest = question.split(".", 1)

        if prefix.strip().isdigit():
            question = rest.strip()

    # Normalize Unicode dashes
    question = question.replace("–", "-")
    question = question.replace("—", "-")
    question = question.replace("-", "-")

    # Fix common joined words
    replacements = {
        "improvepatient": "improve patient",
        "improvingpatient": "improving patient",
        "theeffectiveness": "the effectiveness",
        "implementationof": "implementation of",
        "implementation ofartificial": "implementation of artificial",

        "regulatoryframeworks": "regulatory frameworks",
        "regulatoryframework": "regulatory framework",

        "artificialintelligence": "artificial intelligence",
        "artificialintelligencein": "artificial intelligence in",

        "healthcareproviders": "healthcare providers",
        "healthcareprovider": "healthcare provider",
        "healthcareinstitutions": "healthcare institutions",
        "healthcareorganizations": "healthcare organizations",

        "patientcare": "patient care",
        "patientmonitoring": "patient monitoring",
        "patientmanagement": "patient management",

        "medicalimaging": "medical imaging",
        "medicaldiagnosis": "medical diagnosis",
        "drugdiscovery": "drug discovery",

        "smartalgorithms": "smart algorithms",
        "theuse": "the use",
        "theimpact": "the impact",
        "findingswere": "findings were",

        "sourcecontent": "source content",

        "Intelligencein": "Intelligence in",
        "intelligencein": "intelligence in",
        "inHealthcare": "in Healthcare",
        "inhealthcare": "in healthcare",

        "integrationwith": "integration with",
        "internationalcollaboration": "international collaboration",

        "diagnostictools": "diagnostic tools",
        "diagnostictool": "diagnostic tool",

        "AI-drivendiagnostic": "AI-driven diagnostic",
        "AI-drivendiagnostictools": "AI-driven diagnostic tools",

        "algorithmicerrors": "algorithmic errors",
        "ethicaluse": "ethical use",
        "ethicalframeworks": "ethical frameworks",

        "safetyand": "safety and",
        "efficacyand": "efficacy and",

        "data privacy": "data privacy",
        "dataprivacy": "data privacy",

        "accountabilityconcerns": "accountability concerns",
        "workflowintegration": "workflow integration",
        "staffacceptance": "staff acceptance",
        "safetystandards": "safety standards",

        "futuredevelopment": "future development",
        "futuredevelopments": "future developments",
    }

    for old, new in replacements.items():
        question = question.replace(old, new)

    # Fix common AI joins
    question = re.sub(
        r"(?i)\bofAI\b",
        "of AI",
        question
    )

    question = re.sub(
        r"(?i)\bforAI\b",
        "for AI",
        question
    )

    question = re.sub(
        r"(?i)\bwithAI\b",
        "with AI",
        question
    )

    question = re.sub(
        r"(?i)\bandAI\b",
        "and AI",
        question
    )

    # Fix joined "AI-based", "AI-driven", etc.
    question = re.sub(
        r"(?i)\bofAI-",
        "of AI-",
        question
    )

    question = re.sub(
        r"(?i)\bforAI-",
        "for AI-",
        question
    )

    question = re.sub(
        r"(?i)\bwithAI-",
        "with AI-",
        question
    )

    # Normalize whitespace
    question = " ".join(question.split())

    # Fix spaces before punctuation
    question = question.replace(" ,", ",")
    question = question.replace(" .", ".")
    question = question.replace(" ?", "?")

    # Ensure question mark
    if question and not question.endswith("?"):
        question += "?"

    return question


def create_research_plan(topic: str) -> list[str]:
    """Generate exactly five research questions."""

    prompt = f"""
You are a research planning agent.

Research topic:
{topic}

Generate exactly 5 research questions.

The questions must cover:

1. Applications
2. Effectiveness and accuracy
3. Risks, limitations, and ethical concerns
4. Adoption barriers
5. Future development, regulation, safety, and ethics

IMPORTANT RULES:

- Return exactly 5 questions.
- Return one question per line.
- Do not number the questions.
- Do not use bullet points.
- Use normal spaces between every word.
- Never join two words together.
- Use clear academic English.
- Each question must be complete.
- Do not include explanations.
- Do not include headings.
- Do not include answers.
- Do not include citations.
- Do not include URLs.

Return ONLY the five questions.
"""

    response = ask_llm(prompt)

    questions = []

    for line in response.splitlines():

        line = line.strip()

        if not line:
            continue

        cleaned = clean_question(line)

        if len(cleaned) < 20:
            continue

        if cleaned.endswith("?"):
            questions.append(cleaned)

    # Remove duplicate questions
    unique_questions = []

    for question in questions:

        if question.lower() not in [
            q.lower()
            for q in unique_questions
        ]:
            unique_questions.append(question)

    # Safe fallback if the LLM does not return 5 questions
    if len(unique_questions) < 5:

        unique_questions = [
            f"What are the major applications of {topic}?",

            f"How effective and accurate is {topic} "
            f"in real-world applications?",

            f"What are the major risks, limitations, "
            f"and ethical concerns of {topic}?",

            f"What are the main barriers to adopting "
            f"{topic}?",

            f"What future developments and regulatory "
            f"considerations are important for {topic}?",
        ]

    return unique_questions[:5]