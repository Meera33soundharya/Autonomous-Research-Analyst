import re


QUALITY_WEIGHTS = {
    "citation_accuracy": 0.25,
    "topic_relevance": 0.20,
    "source_credibility": 0.15,
    "research_coverage": 0.15,
    "factual_consistency": 0.10,
    "report_quality": 0.10,
    "workflow_reliability": 0.05,
}

REQUIRED_REPORT_SECTIONS = (
    "executive summary",
    "introduction",
    "research objectives",
    "research questions",
    "methodology and source selection",
    "key research findings",
    "evidence analysis",
    "comparative analysis",
    "challenges and limitations",
    "future research opportunities",
    "conclusion",
    "references",
)

_NUMBER_PATTERN = re.compile(r"(?<![A-Za-z])\d[\d,]*(?:\.\d+)?%?")


def _number_values(text: str) -> set[str]:
    return {
        match.replace(",", "")
        for match in _NUMBER_PATTERN.findall(text)
    }


def _finding_list(evidence: list[dict]) -> list[dict]:
    return [
        finding
        for group in evidence
        for finding in group.get("findings", [])
    ]


def _score(value: float) -> float:
    return round(max(0.0, min(10.0, value)), 2)


def _metric(
    score: float | None,
    weight: float,
    criterion: str,
    sample_size: int,
    **details: object,
) -> dict:
    return {
        "score": score,
        "status": "EVALUATED" if score is not None else "NOT_EVALUATED",
        "weight": weight,
        "criterion": criterion,
        "sample_size": sample_size,
        **details,
    }


def evaluate_research_quality(
    topic: str,
    questions: list[str],
    verified_evidence: list[dict],
    report: str,
    run_status: str,
    pipeline_diagnostics: dict | None = None,
) -> dict:
    """Compute a transparent, evidence-based score; never self-rate with an LLM."""
    pipeline_diagnostics = pipeline_diagnostics or {}
    findings = _finding_list(verified_evidence)
    relevant = [
        item
        for item in findings
        if item.get("relevance_status") == "RELEVANT"
    ]
    accepted = [
        item
        for item in relevant
        if item.get("status") in {"SUPPORTED", "PARTIALLY_SUPPORTED"}
    ]
    supported = sum(item.get("status") == "SUPPORTED" for item in relevant)
    partial = sum(item.get("status") == "PARTIALLY_SUPPORTED" for item in relevant)
    judged_count = len(findings)

    citation_accuracy = (
        _score(10 * (supported + 0.5 * partial) / judged_count)
        if judged_count
        else None
    )
    topic_relevance = (
        _score(
            10
            * sum(
                item.get("relevance_status") == "RELEVANT"
                for item in findings
            )
            / judged_count
        )
        if judged_count
        else None
    )

    source_scores = []
    seen_urls = set()
    for finding in accepted:
        url = str(finding.get("source_url", "")).strip()
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        try:
            source_scores.append(float(finding.get("source_quality", 0)) * 10)
        except (TypeError, ValueError):
            source_scores.append(0.0)
    source_credibility = (
        _score(sum(source_scores) / len(source_scores))
        if source_scores
        else None
    )

    covered_questions = {
        str(item.get("question", "")).strip()
        for group in verified_evidence
        for item in group.get("findings", [])
        if (
            item.get("relevance_status") == "RELEVANT"
            and item.get("status") in {"SUPPORTED", "PARTIALLY_SUPPORTED"}
        )
    }
    research_coverage = (
        _score(
            10
            * len(covered_questions.intersection(questions))
            / len(questions)
        )
        if questions
        else None
    )

    numeric_claims = [
        item
        for item in accepted
        if _number_values(str(item.get("claim", "")))
    ]
    numerically_consistent = sum(
        _number_values(str(item.get("claim", ""))).issubset(
            _number_values(str(item.get("supporting_passage", "")))
        )
        for item in numeric_claims
    )
    factual_consistency = (
        _score(10 * numerically_consistent / len(numeric_claims))
        if numeric_claims
        else None
    )

    normalized_report = report.casefold()
    missing_sections = [
        section
        for section in REQUIRED_REPORT_SECTIONS
        if not re.search(
            rf"(?im)^#+\s+.*{re.escape(section)}",
            normalized_report,
        )
    ]
    traceable_report_findings = sum(
        bool(str(item.get("claim", "")).strip())
        and str(item.get("claim", "")).strip().casefold() in normalized_report
        and str(item.get("source_url", "")).strip().casefold()
        in normalized_report
        for item in accepted
    )
    report_quality = (
        _score(
            5
            * (
                (len(REQUIRED_REPORT_SECTIONS) - len(missing_sections))
                / len(REQUIRED_REPORT_SECTIONS)
                + traceable_report_findings / len(accepted)
            )
        )
        if accepted
        else None
    )

    citation_error_count = sum(
        bool(item.get("verification_reason"))
        or "failed" in str(item.get("relevance_reason", "")).casefold()
        for item in findings
    )
    provider_error_count = len(
        pipeline_diagnostics.get("searcher", {}).get("errors", [])
    )
    extraction_error_count = len(
        pipeline_diagnostics.get("extraction", {}).get("errors", [])
    )
    has_workflow_errors = bool(
        citation_error_count or provider_error_count or extraction_error_count
    )
    reliability = (
        10.0
        if run_status == "COMPLETED" and not has_workflow_errors
        else 5.0
        if run_status == "COMPLETED"
        else 5.0
        if run_status == "INCOMPLETE" and not has_workflow_errors
        else 0.0
    )

    metrics = {
        "citation_accuracy": _metric(
            citation_accuracy,
            QUALITY_WEIGHTS["citation_accuracy"],
            "SUPPORTED=1, PARTIALLY_SUPPORTED=0.5, UNSUPPORTED=0 across judged claims.",
            judged_count,
        ),
        "topic_relevance": _metric(
            topic_relevance,
            QUALITY_WEIGHTS["topic_relevance"],
            "RELEVANT=1 and other or missing relevance decisions=0 across findings.",
            judged_count,
        ),
        "source_credibility": _metric(
            source_credibility,
            QUALITY_WEIGHTS["source_credibility"],
            "Mean heuristic source_quality (0-1) for unique cited accepted sources, scaled to 0-10.",
            len(source_scores),
        ),
        "research_coverage": _metric(
            research_coverage,
            QUALITY_WEIGHTS["research_coverage"],
            "Questions with a relevant supported or partially supported finding divided by planned questions.",
            len(questions),
        ),
        "factual_consistency": _metric(
            factual_consistency,
            QUALITY_WEIGHTS["factual_consistency"],
            "Exact numeric/date token consistency for accepted claims; cross-source contradiction review is not included.",
            len(numeric_claims),
        ),
        "report_quality": _metric(
            report_quality,
            QUALITY_WEIGHTS["report_quality"],
            "Required-heading coverage and traceable representation of accepted claims and source URLs.",
            len(accepted),
            missing_sections=missing_sections,
            traceable_findings=traceable_report_findings,
        ),
        "workflow_reliability": _metric(
            reliability,
            QUALITY_WEIGHTS["workflow_reliability"],
            "COMPLETED without recorded search/extraction/verification errors=10; COMPLETED with errors or INCOMPLETE without errors=5; otherwise=0.",
            1,
        ),
    }

    evaluated_metrics = [
        metric
        for metric in metrics.values()
        if metric["score"] is not None
    ]
    evaluated_weight = sum(
        metric["weight"]
        for metric in evaluated_metrics
    )
    weighted_score = (
        round(
            sum(
                metric["score"] * metric["weight"]
                for metric in evaluated_metrics
            )
            / evaluated_weight,
            2,
        )
        if evaluated_weight
        else 0.0
    )
    has_verified_findings = bool(accepted)
    independent_review_completed = False
    published_score = (
        min(weighted_score, 8.9)
        if has_verified_findings and not independent_review_completed
        else weighted_score
    )
    return {
        "topic": topic,
        "score_out_of_10": published_score if has_verified_findings else 0.0,
        "passing": (
            has_verified_findings
            and independent_review_completed
            and weighted_score >= 9.0
        ),
        "independent_review_completed": independent_review_completed,
        "score_ceiling_applied": (
            has_verified_findings
            and not independent_review_completed
            and weighted_score > 8.9
        ),
        "status": run_status,
        "gate_reason": (
            ""
            if has_verified_findings
            else "No verified, topic-relevant findings; a passing score is prohibited."
        ),
        "weights_sum": round(sum(QUALITY_WEIGHTS.values()), 2),
        "evaluated_weight": round(evaluated_weight, 2),
        "metrics": metrics,
        "limitations": [
            "Citation and relevance labels are evaluated by the configured LLM, not an independent human reviewer.",
            "The published score is capped at 8.9/10 until independent human or external review is completed.",
            "Source credibility is a deterministic metadata/domain heuristic, not a manual publisher audit.",
            "Cross-source contradiction detection is not implemented.",
        ],
    }
