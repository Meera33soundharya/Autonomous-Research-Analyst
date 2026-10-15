import re
from urllib.parse import urlparse


def clean_report_text(text: str) -> str:
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.!?;:])", r"\1", text)
    text = re.sub(r"([,.!?;:])([A-Za-z])", r"\1 \2", text)
    return text.strip()


def _valid_source_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def generate_report(
    topic: str,
    verified_evidence: list[dict],
    run_status: str = "",
    pipeline_diagnostics: dict | None = None,
) -> str:
    """Build a report exclusively from verified findings and their sources."""
    pipeline_diagnostics = pipeline_diagnostics or {}
    report = [f"# {topic}", ""]
    findings = [
        (group.get("question", ""), finding)
        for group in verified_evidence
        for finding in group.get("findings", [])
    ]
    relevant = [
        finding
        for _, finding in findings
        if finding.get("relevance_status") == "RELEVANT"
    ]
    accepted = [
        (question, finding)
        for question, finding in findings
        if (
            finding.get("relevance_status") == "RELEVANT"
            and finding.get("status") in {"SUPPORTED", "PARTIALLY_SUPPORTED"}
            and str(finding.get("claim", "")).strip()
            and _valid_source_url(str(finding.get("source_url", "")).strip())
            and str(finding.get("supporting_passage", "")).strip()
        )
    ]
    supported_count = sum(
        finding.get("status") == "SUPPORTED"
        for _, finding in accepted
    )
    partial_count = len(accepted) - supported_count
    rejected_count = len(findings) - len(accepted)
    final_status = run_status or ("COMPLETED" if accepted else "INCOMPLETE")
    if not accepted and final_status == "COMPLETED":
        final_status = "INCOMPLETE"

    report.extend([
        "## 1. Executive Summary",
        "",
        f"Research status: **{final_status}**.",
        (
            f"The workflow retained {supported_count} supported and "
            f"{partial_count} partially supported, topic-relevant claims. "
            f"{rejected_count} claims were excluded from the report."
            if accepted
            else             "No verified, topic-relevant findings are available. "
            f"The research run status is {final_status}; no successful "
            "evidence report is claimed."
        ),
        "",
        "## 2. Introduction",
        "",
        f"This report examines {topic}. Findings below are limited to "
        "retrieved source material and are included only when they have "
        "a verified citation and traceable supporting passage.",
        "",
        "## 3. Research Objectives",
        "",
        f"The objective was to investigate {topic}, identify source-grounded "
        "evidence, and distinguish supported claims from incomplete or "
        "unsupported claims.",
        "",
        "## 4. Research Questions",
        "",
    ])
    questions = [
        str(group.get("question", "")).strip()
        for group in verified_evidence
        if str(group.get("question", "")).strip()
    ]
    report.extend(f"- {clean_report_text(question)}" for question in questions)
    if not questions:
        report.append("- No research questions were produced.")

    report.extend([
        "",
        "## 5. Methodology and Source Selection",
        "",
        "Research questions were sent through the configured web and scholarly "
        "search integrations. Claims were extracted from retrieved source "
        "content, screened for topic relevance separately from source support, "
        "and checked against a verbatim source passage. Source credibility "
        "scores are metadata/domain heuristics, not an independent peer-review "
        "or publisher audit.",
        "",
        "## 6. Key Research Findings",
        "",
    ])
    if accepted:
        references: list[dict] = []
        reference_ids: dict[str, int] = {}
        accepted_by_question: dict[str, list[tuple[int, dict]]] = {}

        for question, finding in accepted:
            url = str(finding["source_url"]).strip()
            if url not in reference_ids:
                reference_ids[url] = len(references) + 1
                references.append({
                    "title": clean_report_text(
                        str(finding.get("source_title") or "Untitled source")
                    ),
                    "url": url,
                    "authors": finding.get("authors", []),
                    "year": str(finding.get("year") or ""),
                    "doi": str(finding.get("doi") or ""),
                })
            accepted_by_question.setdefault(question, []).append(
                (reference_ids[url], finding)
            )

        for question, question_findings in accepted_by_question.items():
            report.extend([f"### {clean_report_text(question)}", ""])
            for reference_id, finding in question_findings:
                claim = clean_report_text(str(finding.get("claim", "")))
                passage = clean_report_text(
                    str(finding.get("supporting_passage", ""))
                )
                report.append(
                    f"- **Claim [{reference_id}]:** {claim} "
                    f"(**{finding['status']}**)"
                )
                report.append(f'  - **Supporting passage:** "{passage}"')
            report.append("")
    else:
        report.extend([
            "No claims met the relevance, citation, and provenance checks.",
            "",
        ])

    report.extend([
        "## 7. Evidence Analysis",
        "",
        f"Accepted supported claims: {supported_count}.",
        f"Accepted partially supported claims: {partial_count}.",
        f"Rejected or non-relevant claims: {rejected_count}.",
        "",
        "A source discussing a similar subject was not sufficient on its own: "
        "accepted claims required a relevant classification, source support, "
        "a valid URL, and a traceable passage.",
        "",
        "## 8. Comparative Analysis",
        "",
    ])
    if re.search(r"\b(?:versus|vs\.?)\b", topic, re.IGNORECASE) and accepted:
        report.append(
            "The comparison is limited to the verified claims above. "
            "No side-by-side conclusion is added where the collected findings "
            "do not directly compare the alternatives."
        )
    else:
        report.append(
            "A comparative analysis is not applicable to this topic, or the "
            "collected verified evidence does not support a direct comparison."
        )

    search_diagnostics = pipeline_diagnostics.get("searcher", {})
    extraction_diagnostics = pipeline_diagnostics.get("extraction", {})
    cleaner_diagnostics = pipeline_diagnostics.get("evidence_cleaner", {})
    citation_diagnostics = pipeline_diagnostics.get("citation_checker", {})
    report.extend([
        "",
        "## 9. Challenges and Limitations",
        "",
        f"Sources retrieved: {search_diagnostics.get('unique_source_count', 0)}. "
        f"Source-question pairs with usable content: "
        f"{extraction_diagnostics.get('usable_sources_by_question', 0)}. "
        f"Findings extracted: {extraction_diagnostics.get('extracted_findings', 0)}. "
        f"Findings rejected during cleaning: "
        f"{cleaner_diagnostics.get('rejected_findings', 0)}. "
        f"Unsupported claims: {citation_diagnostics.get('unsupported_claims', 0)}.",
        "",
        "Search coverage depends on the availability and response quality of "
        "the configured providers. LLM-based relevance and citation judgments "
        "are not independent human review. This report does not establish that "
        "all relevant literature was retrieved or detect every cross-source "
        "contradiction.",
        "",
        "## 10. Future Research Opportunities",
        "",
        "Research questions without a verified finding identify evidence gaps "
        "for follow-up; they are not evidence of a particular conclusion.",
    ])
    covered_questions = {question for question, _ in accepted}
    uncovered_questions = [
        question for question in questions if question not in covered_questions
    ]
    if uncovered_questions:
        report.extend(
            f"- Seek additional evidence for: {clean_report_text(question)}"
            for question in uncovered_questions
        )
    else:
        report.append("- No uncovered research questions were identified.")

    report.extend([
        "",
        "## 11. Conclusion",
        "",
    ])
    if accepted:
        report.append(
            f"The collected sources support {supported_count} claims and "
            f"partially support {partial_count} claims relevant to {topic}. "
            "Conclusions should remain within those findings and the "
            "limitations above."
        )
    else:
        report.append(
            f"The workflow did not establish verified findings about {topic}. "
            "No substantive conclusion is drawn; further source collection "
            "and verification are required."
        )

    report.extend(["", "## 12. References", ""])
    if accepted:
        for index, reference in enumerate(references, 1):
            authors = reference["authors"]
            author_text = (
                ", ".join(map(str, authors))
                if isinstance(authors, list) and authors
                else "Author unavailable"
            )
            year = reference["year"] or "Date unavailable"
            doi_text = f" DOI: {reference['doi']}." if reference["doi"] else ""
            report.append(
                f"- [{index}] {author_text} ({year}). {reference['title']}. "
                f"{reference['url']}.{doi_text}"
            )
    else:
        report.append("No verified source references were available.")
    report.append("")
    return "\n".join(report)
