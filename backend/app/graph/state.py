from typing import TypedDict


class ResearchState(TypedDict, total=False):
    topic: str
    research_plan: str
    questions: list[str]
    search_results: list[dict]
    evidence: str
    verified_evidence: str
    report: str