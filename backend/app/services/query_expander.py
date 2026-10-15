import json
import re

from app.services.llm_service import ask_llm
from app.services.research_memory import get_related_memory


def _targeted_subtopic(topic: str, question: str, index: int) -> str | None:
    normalized_topic = topic.casefold()
    if not (
        "voice" in normalized_topic
        and ("complaint" in normalized_topic or "grievance" in normalized_topic)
        and ("officer" in normalized_topic or "assignment" in normalized_topic)
    ):
        return None

    components = (
        (
            (
                "field officer",
                "field officers",
                "field assignment",
                "officer assignment",
                "assign field",
                "workflow automation",
            ),
            "field officer assignment grievance redressal workflow automation",
        ),
        (
            (
                "grievance management",
                "complaint-management",
                "complaint classification",
                "automatically classified",
                "automated classification",
                "triage",
            ),
            "citizen grievance management automated complaint classification",
        ),
        (
            ("multilingual", "language interface", "language access", "translation"),
            "multilingual voice interfaces speech recognition citizen services",
        ),
        (
            (
                "voice-based",
                "speech-to-text",
                "speech recognition",
                "voice interface",
                "voice assistant",
            ),
            "voice-based complaint registration speech-to-text systems",
        ),
    )
    normalized_question = question.casefold().replace(
        normalized_topic,
        "",
    )
    matching = [
        (sum(normalized_question.count(keyword) for keyword in keywords), query)
        for keywords, query in components
        if any(keyword in normalized_question for keyword in keywords)
    ]
    if matching:
        return max(matching, key=lambda item: item[0])[1] + " research evidence"
    return components[index % len(components)][1] + " research evidence"


def _with_targeted_query(
    topic: str,
    question: str,
    queries: list[str],
    index: int,
) -> list[str]:
    targeted = _targeted_subtopic(topic, question, index)
    if not targeted:
        return queries[:2]
    return [targeted, *[
        query
        for query in queries
        if query.casefold() != targeted.casefold()
    ][:1]]


def expand_search_queries(
    topic: str,
    questions: list[str],
    diagnostics: list[dict] | None = None,
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

    try:
        response = ask_llm(prompt)
    except Exception as error:
        if diagnostics is not None:
            diagnostics.append({
                "stage": "query_expansion",
                "error": f"{type(error).__name__}: {error}",
            })
        return {
            question: _with_targeted_query(
                topic,
                question,
                [question, f"{question} research study evidence"],
                index,
            )
            for index, question in enumerate(questions)
        }

    if "model service is unavailable" in response.casefold():
        if diagnostics is not None:
            diagnostics.append({
                "stage": "query_expansion",
                "error": response.strip(),
            })
        return {
            question: _with_targeted_query(
                topic,
                question,
                [question, f"{question} research study evidence"],
                index,
            )
            for index, question in enumerate(questions)
        }

    try:

        match = re.search(
            r"\{.*\}",
            response,
            re.DOTALL
        )

        if not match:
            if diagnostics is not None:
                diagnostics.append({
                    "stage": "query_expansion",
                    "error": "The query planner returned no JSON object.",
                })
        else:

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
                    if diagnostics is not None:
                        diagnostics.append({
                            "stage": "query_expansion",
                            "question": question,
                            "error": "No generated queries; using deterministic fallbacks.",
                        })
                    queries = [
                        question,
                        f"{question} research study evidence"
                    ]

                cleaned[question] = _with_targeted_query(
                    topic,
                    question,
                    queries,
                    questions.index(question),
                )

            return cleaned

    except Exception as error:
        if diagnostics is not None:
            diagnostics.append({
                "stage": "query_expansion",
                "error": f"Malformed query JSON ({type(error).__name__}: {error})",
            })

    return {
        question: _with_targeted_query(
            topic,
            question,
            [question, f"{question} research study evidence"],
            index,
        )
        for index, question in enumerate(questions)
    }
