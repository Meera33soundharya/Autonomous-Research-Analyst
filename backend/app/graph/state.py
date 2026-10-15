from typing import TypedDict


class ResearchState(TypedDict, total=False):

    topic: str

    raw_topic: str

    topic_scope: str

    topic_meta: str

    run_status: str

    execution_status: str

    evidence_status: str

    extraction_status: str

    source_count: int

    extracted_finding_count: int

    cleaner_dropped_count: int

    irrelevant_finding_count: int

    pipeline_diagnostics: dict

    research_quality: dict

    research_questions: list[str]

    search_results: list[dict]

    evidence: list[dict]

    cleaned_evidence: list[dict]

    verified_evidence: list[dict]

    report: str

    markdown_file: str

    pdf_file: str