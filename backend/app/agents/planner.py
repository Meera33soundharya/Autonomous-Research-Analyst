import re

from app.services.llm_service import ask_llm


BAD_PHRASES = [
    "create exactly",
    "research questions specifically",
    "every question must",
    "the questions must",
    "never assume",
    "never use hardcoded",
    "do not assume",
    "do not discuss",
    "do not mention",
    "adapt the questions",
    "supplied topic",
    "requested research topic",
    "your task",
    "output only",
    "rules:",
]


def _fallback_questions(topic: str) -> list[str]:
    return [
        f"What is {topic}, and what are its main concepts and characteristics?",
        f"What are the major applications, uses, or benefits of {topic}?",
        f"What research evidence and findings currently exist about {topic}?",
        f"What are the main challenges, limitations, and risks associated with {topic}?",
        f"What future developments and research opportunities exist for {topic}?",
    ]


def _clean_questions(response: str, topic: str) -> list[str]:
    questions = []

    topic_words = [
        word.lower()
        for word in re.findall(r"[A-Za-z0-9]+", topic)
        if len(word) >= 4
    ]

    for raw_line in response.splitlines():

        line = raw_line.strip()

        if not line:
            continue

        line = re.sub(
            r"^\s*(?:\d+[\.\)]|[-*])\s*",
            "",
            line
        ).strip()

        lower = line.lower()

        # Reject prompt instructions
        if any(bad in lower for bad in BAD_PHRASES):
            continue

        # Must look like a real question
        if "?" not in line:
            continue

        if len(line) < 25:
            continue

        # Must contain at least one important topic word
        if topic_words:
            topic_match = any(
                word in lower
                for word in topic_words
            )

            if not topic_match:
                continue

        line = line.rstrip(" ?") + "?"

        if line not in questions:
            questions.append(line)

    return questions[:5]


def run_planner(topic: str) -> list[str]:

    topic = topic.strip()

    if not topic:
        return []

    prompt = f"""
You are the Planner Agent of an autonomous research analyst.

Research topic:
{topic}

Generate exactly five research questions ONLY about the research topic above.

Question 1 must focus on definition and key concepts.
Question 2 must focus on applications, uses, or benefits.
Question 3 must focus on research evidence and findings.
Question 4 must focus on challenges, limitations, or risks.
Question 5 must focus on future developments and research opportunities.

Do not output explanations.
Do not output instructions.
Do not repeat this prompt.
Do not mention healthcare unless healthcare is actually part of the topic.

Return only five numbered questions.
"""

    try:

        response = ask_llm(prompt)

        if not isinstance(response, str):
            response = str(response)

        questions = _clean_questions(
            response,
            topic
        )

        if len(questions) == 5:
            return questions

    except Exception:
        pass

    return _fallback_questions(topic)


def create_research_plan(topic: str) -> list[str]:
    """
    Compatibility function used by workflow.py.
    """
    return run_planner(topic)