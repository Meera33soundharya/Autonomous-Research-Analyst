import json
import re

from app.services.llm_service import ask_llm


def _extract_questions(response: str) -> list[str]:

    response = response.strip()

    # --------------------------------------------------------
    # First: try JSON
    # --------------------------------------------------------

    try:

        match = re.search(
            r"\[.*\]",
            response,
            re.DOTALL
        )

        if match:

            data = json.loads(
                match.group(0)
            )

            if isinstance(data, list):

                questions = []

                for item in data:

                    if isinstance(item, str):

                        question = item.strip()

                        if (
                            question
                            and "MUST be based" not in question
                            and "Never assume" not in question
                            and "Never use hardcoded" not in question
                            and "Do not mention" not in question
                            and "Adapt the questions" not in question
                        ):

                            questions.append(
                                question
                            )

                if len(questions) >= 5:
                    return questions[:5]

    except Exception:
        pass

    # --------------------------------------------------------
    # Second: parse only lines ending with ?
    # --------------------------------------------------------

    questions = []

    for line in response.splitlines():

        line = line.strip()

        if not line:
            continue

        line = re.sub(
            r"^[\-\*\d\.\)\s]+",
            "",
            line
        ).strip()

        if not line.endswith("?"):
            continue

        if len(line) < 25:
            continue

        blocked = [
            "must be based",
            "never assume",
            "never use hardcoded",
            "do not mention healthcare",
            "adapt the questions",
            "return only",
            "important rules",
        ]

        if any(
            phrase in line.lower()
            for phrase in blocked
        ):
            continue

        questions.append(line)

    return questions[:5]


def create_research_plan(
    topic: str
) -> list[str]:

    topic = topic.strip()

    if not topic:
        return []

    prompt = f"""
You are the Planner Agent of an autonomous research analyst.

USER TOPIC:
{topic}

Create exactly 5 research questions about the USER TOPIC.

The questions must be specific to the topic.

IMPORTANT:
- Generate questions, not instructions.
- Do not explain your process.
- Do not repeat these instructions.
- Do not mention healthcare unless the topic is healthcare.
- Do not use questions from another topic.
- Cover different important aspects of the topic.
- Use established terminology related to the topic.
- Questions should be suitable for web and academic research.
- Return ONLY a JSON array of exactly 5 strings.
- Do not use markdown.
- Do not add any text before or after the JSON.

Example format only:

[
  "What are the main ...?",
  "How does ...?",
  "What are the major ...?",
  "What evidence exists for ...?",
  "What future developments ...?"
]

Generate the questions now for:

{topic}
"""

    response = ask_llm(
        prompt
    )

    questions = _extract_questions(
        response
    )

    # --------------------------------------------------------
    # Safety fallback
    # --------------------------------------------------------

    if len(questions) < 5:

        fallback_prompt = f"""
Generate exactly 5 research questions for this topic:

{topic}

Return only 5 separate question sentences.
Every sentence must end with a question mark.
Do not include instructions, explanations, headings,
rules, examples, or commentary.
"""

        fallback_response = ask_llm(
            fallback_prompt
        )

        questions = _extract_questions(
            fallback_response
        )

    return questions[:5]
