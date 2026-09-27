import json
import re

from app.services.llm_service import ask_llm
from app.services.research_memory import get_related_memory


def expand_search_queries(
    topic: str,
    questions: list[str]
) -> dict[str, list[str]]:

    memory = get_related_memory(
        topic,
        limit=6
    )

    memory_text = "\n".join(
        f"- {item.get('question', '')}"
        for item in memory
    )

    prompt = f"""
You are a semantic research search-query planner.

USER TOPIC:
{topic}

RESEARCH QUESTIONS:
{json.dumps(questions, indent=2)}

The exact user topic may be a project title, research title,
startup title, product name, or newly coined phrase.

IMPORTANT:
Do NOT search only for the exact title.

Break the topic into its established research concepts.

For example:

"Explainable and Fair Student Dropout Risk Support
with Human-Led Counselling"

should lead to concepts such as:

- student dropout prediction
- student early warning systems
- explainable AI for education
- fairness in student risk prediction
- educational data mining
- human-in-the-loop intervention
- counselling interventions
- student retention
- learning analytics

Previous verified research memory is shown below.
Use it ONLY to identify research gaps.
Never treat memory as fresh evidence.

{memory_text}

Generate exactly 2 strong search queries for EACH research question.

Rules:
1. Use established terminology.
2. Do not search the whole novel title repeatedly.
3. Include academic/research terminology.
4. Include recent evidence when appropriate.
5. Include systematic reviews when relevant.
6. Include official or institutional terminology when relevant.
7. Do not invent organizations or studies.
8. Return ONLY valid JSON.

Format:

{{
  "question": [
    "query 1",
    "query 2"
  ]
}}
"""

    response = ask_llm(
        prompt
    )

    try:

        match = re.search(
            r"\{.*\}",
            response,
            re.DOTALL
        )

        if match:

            data = json.loads(
                match.group(0)
            )

            cleaned = {}

            for question in questions:

                queries = data.get(
                    question,
                    []
                )

                if not isinstance(
                    queries,
                    list
                ):
                    queries = []

                queries = [
                    str(query).strip()
                    for query in queries
                    if str(query).strip()
                ]

                if not queries:
                    queries = [
                        question,
                        f"{question} research study evidence"
                    ]

                cleaned[question] = queries[:2]

            return cleaned

    except Exception:
        pass

    return {
        question: [
            question,
            f"{question} research study evidence"
        ]
        for question in questions
    }
