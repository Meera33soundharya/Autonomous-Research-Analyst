import json
from pathlib import Path
import re

MEMORY_FILE = (
    Path(__file__).resolve().parents[3]
    / "reports"
    / "research_memory.jsonl"
)


def _tokens(text: str) -> set[str]:
    words = re.findall(
        r"[a-zA-Z0-9]+",
        text.lower()
    )

    stopwords = {
        "the", "a", "an", "and", "or",
        "of", "to", "in", "on", "for",
        "with", "is", "are", "was",
        "were", "that", "this", "as",
        "by", "from", "it", "its"
    }

    return {
        word
        for word in words
        if word not in stopwords
    }


def save_verified_evidence(
    evidence: list[dict]
) -> None:

    MEMORY_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        MEMORY_FILE,
        "a",
        encoding="utf-8"
    ) as file:

        for group in evidence:

            question = group.get(
                "question",
                ""
            )

            for finding in group.get(
                "findings",
                []
            ):

                status = finding.get(
                    "status",
                    ""
                )

                if status not in {
                    "SUPPORTED",
                    "PARTIALLY_SUPPORTED"
                }:
                    continue

                record = {
                    "question": question,
                    "claim": finding.get(
                        "claim",
                        ""
                    ),
                    "source_title": finding.get(
                        "source_title",
                        ""
                    ),
                    "source_url": finding.get(
                        "source_url",
                        ""
                    ),
                    "status": status
                }

                file.write(
                    json.dumps(
                        record,
                        ensure_ascii=False
                    )
                    + "\n"
                )


def get_related_memory(
    topic: str,
    limit: int = 8
) -> list[dict]:

    if not MEMORY_FILE.exists():
        return []

    topic_tokens = _tokens(topic)

    matches = []

    with open(
        MEMORY_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:

            try:
                record = json.loads(
                    line
                )
            except json.JSONDecodeError:
                continue

            question_tokens = _tokens(
                record.get(
                    "question",
                    ""
                )
            )

            if not question_tokens:
                continue

            overlap = (
                len(
                    topic_tokens
                    & question_tokens
                )
                / max(
                    1,
                    len(topic_tokens)
                )
            )

            if overlap >= 0.20:
                matches.append(
                    (
                        overlap,
                        record
                    )
                )

    matches.sort(
        key=lambda item: item[0],
        reverse=True
    )

    return [
        item[1]
        for item in matches[:limit]
    ]
