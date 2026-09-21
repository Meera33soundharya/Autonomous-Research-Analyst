from typing import TypedDict


class ResearchState(TypedDict, total=False):

    topic: str

    research_questions: list[str]

    search_results: list[dict]

    evidence: list[dict]

    verified_evidence: list[dict]

    report: str

    markdown_file: str

    pdf_file: str