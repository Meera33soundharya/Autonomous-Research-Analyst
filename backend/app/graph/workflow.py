from langgraph.graph import StateGraph, START, END

from app.graph.state import ResearchState

from app.agents.planner import create_research_plan
from app.agents.topic_normalizer import normalize_research_topic
from app.agents.searcher import run_search_with_diagnostics
from app.agents.researcher import analyze_sources
from app.agents.evidence_cleaner import clean_evidence
from app.agents.citation_checker import check_citations
from app.agents.writer import generate_report

from app.services.report_service import (
    save_markdown,
    save_pdf
)
from app.services.quality_evaluator import evaluate_research_quality


# ============================================================
# 1. PLANNER AGENT
# ============================================================

def planner_node(state: ResearchState):

    print("\n=== Planner Agent ===")

    raw_topic = state["topic"]
    normalized = normalize_research_topic(raw_topic)
    topic = normalized["topic"]

    if not topic:
        raise ValueError("A research topic is required.")

    print(
        f"Planning research for topic: {topic}"
    )

    questions = create_research_plan(topic, normalized["scope"])

    print(
        f"Generated {len(questions)} research questions."
    )

    for question in questions:
        print(f"- {question}")

    return {
        "topic": topic,
        "raw_topic": normalized["raw_topic"],
        "topic_scope": normalized["scope"],
        "topic_meta": normalized["meta"],
        "research_questions": questions
    }


# ============================================================
# 2. SEARCHER AGENT
# ============================================================

def searcher_node(state: ResearchState):

    print("\n=== Searcher Agent ===")

    questions = state["research_questions"]

    print(
        f"Searching sources for {len(questions)} research questions..."
    )

    results, search_diagnostics = run_search_with_diagnostics(
        state["topic"],
        questions
    )

    print(
        f"Collected {len(results)} web sources."
    )

    return {
        "search_results": results,
        "source_count": len(results),
        "pipeline_diagnostics": {
            **state.get("pipeline_diagnostics", {}),
            "searcher": search_diagnostics,
        },
    }


# ============================================================
# 3. RESEARCHER AGENT
# ============================================================

def researcher_node(state: ResearchState):

    print("\n=== Researcher Agent ===")

    questions = state["research_questions"]
    sources = state["search_results"]

    evidence = []

    for question in questions:

        print(
            f"Analyzing: {question}"
        )

        result = analyze_sources(
            question,
            sources,
            state.get("topic", ""),
            state.get("topic_scope", ""),
        )

        evidence.append(result)

    question_diagnostics = [
        item.get("diagnostics", {})
        for item in evidence
    ]
    extraction_status_counts = {}
    for diagnostic in question_diagnostics:
        status = diagnostic.get("status", "UNKNOWN")
        extraction_status_counts[status] = (
            extraction_status_counts.get(status, 0) + 1
        )
    failure_statuses = (
        "LLM_REQUEST_FAILED",
        "INVALID_LLM_RESPONSE",
        "EXTRACTION_FAILED",
    )
    extraction_status = (
        next(
            (
                status
                for status in failure_statuses
                if status in extraction_status_counts
            ),
            "",
        )
        or (
            "EXTRACTION_COMPLETED"
            if extraction_status_counts.get("EXTRACTION_COMPLETED")
            else "NO_RELEVANT_EVIDENCE"
        )
    )
    extraction_diagnostics = {
        "research_question_count": len(questions),
        "sources_retrieved": len(sources),
        "status_counts": extraction_status_counts,
        "status": extraction_status,
        "usable_sources_by_question": sum(
            item.get("usable_source_count", 0)
            for item in question_diagnostics
        ),
        "extracted_findings": sum(
            len(item.get("findings", []))
            for item in evidence
        ),
        "rejected_findings": sum(
            len(item.get("rejected_findings", []))
            for item in question_diagnostics
        ),
        "rejected_sources": sum(
            len(item.get("rejected_sources", []))
            for item in question_diagnostics
        ),
        "errors": [
            {
                "question": item.get("question", ""),
                "detail": (
                    diagnostic.get("error")
                    or diagnostic.get("status", "Extraction failure")
                ),
            }
            for item, diagnostic in zip(evidence, question_diagnostics)
            if (
                diagnostic.get("error")
                or diagnostic.get("status") in failure_statuses
            )
        ],
        "by_question": [
            {
                "question": item.get("question", ""),
                **item.get("diagnostics", {}),
            }
            for item in evidence
        ],
    }

    print(
        f"Research questions: {len(questions)}; "
        f"sources retrieved: {len(sources)}; "
        f"usable source-question pairs: "
        f"{extraction_diagnostics['usable_sources_by_question']}; "
        f"findings extracted: "
        f"{extraction_diagnostics['extracted_findings']}; "
        f"findings rejected: "
        f"{extraction_diagnostics['rejected_findings']}; "
        f"statuses: {extraction_status_counts}"
    )

    return {
        "evidence": evidence,
        "pipeline_diagnostics": {
            **state.get("pipeline_diagnostics", {}),
            "extraction": extraction_diagnostics,
        },
        "extracted_finding_count": sum(
            len(item.get("findings", [])) for item in evidence
        ),
        "extraction_status": extraction_status,
    }


# ============================================================
# 4. EVIDENCE CLEANER
# ============================================================

def evidence_cleaner_node(state: ResearchState):

    print("\n=== Evidence Cleaner ===")

    evidence = state["evidence"]

    print(
        "Cleaning extracted research evidence..."
    )

    rejected_findings = []
    cleaned_evidence = clean_evidence(evidence, rejected_findings)

    original_count = sum(
        len(item.get("findings", []))
        for item in evidence
    )

    cleaned_count = sum(
        len(item.get("findings", []))
        for item in cleaned_evidence
    )

    print(
        f"Original findings: {original_count}"
    )

    print(
        f"Clean findings: {cleaned_count}"
    )

    return {
        "cleaned_evidence": cleaned_evidence,
        "cleaner_dropped_count": len(rejected_findings),
        "pipeline_diagnostics": {
            **state.get("pipeline_diagnostics", {}),
            "evidence_cleaner": {
                "input_findings": original_count,
                "retained_findings": cleaned_count,
                "rejected_findings": len(rejected_findings),
                "rejections": rejected_findings,
            },
        },
    }


# ============================================================
# 5. CITATION CHECKER
# ============================================================

def citation_checker_node(state: ResearchState):

    print("\n=== Citation Checker ===")

    cleaned_evidence = state[
        "cleaned_evidence"
    ]

    print(
        "Verifying research claims against sources..."
    )

    verified = check_citations(
        cleaned_evidence,
        state.get("topic", "")
    )

    supported = 0
    partial = 0
    unsupported = 0
    topic_relevant = 0
    irrelevant = 0

    for item in verified:

        for finding in item.get(
            "findings",
            []
        ):

            status = finding.get(
                "status",
                ""
            )
            relevance = finding.get("relevance_status")
            if relevance and relevance != "RELEVANT":
                irrelevant += 1

            if status == "SUPPORTED":

                supported += 1
                if relevance == "RELEVANT":
                    topic_relevant += 1

            elif status == "PARTIALLY_SUPPORTED":

                partial += 1
                if relevance == "RELEVANT":
                    topic_relevant += 1

            else:

                unsupported += 1

    pipeline_diagnostics = state.get("pipeline_diagnostics", {})
    extraction_errors = (
        pipeline_diagnostics.get("extraction", {}).get("errors", [])
    )
    search_errors = (
        pipeline_diagnostics.get("searcher", {}).get("errors", [])
    )
    verification_errors = [
        {
            "question": item.get("question", ""),
            "claim": finding.get("claim", ""),
            "detail": finding.get("verification_reason")
            or finding.get("relevance_reason", ""),
        }
        for item in verified
        for finding in item.get("findings", [])
        if finding.get("verification_reason")
        or "model service is unavailable"
        in str(finding.get("relevance_reason", "")).lower()
    ]
    rejected_claims = [
        {
            "question": item.get("question", ""),
            "claim": finding.get("claim", ""),
            "status": finding.get("status", ""),
            "relevance_status": finding.get("relevance_status", ""),
            "reason": (
                finding.get("verification_reason")
                or finding.get("relevance_reason")
                or "The claim was not verified as supported."
            ),
        }
        for item in verified
        for finding in item.get("findings", [])
        if (
            finding.get("status") == "UNSUPPORTED"
            or finding.get("relevance_status") in {
                "PARTIALLY_RELEVANT",
                "IRRELEVANT",
            }
        )
    ]
    has_errors = bool(extraction_errors or search_errors or verification_errors)
    if topic_relevant and not has_errors:
        run_status = "COMPLETED"
    elif extraction_errors and not topic_relevant:
        run_status = "FAILED"
    elif search_errors and not topic_relevant:
        run_status = "FAILED"
    elif verification_errors and not topic_relevant:
        run_status = "FAILED"
    else:
        run_status = "INCOMPLETE"

    print(
        f"Supported: {supported}"
    )

    print(
        f"Partially supported: {partial}"
    )

    print(
        f"Unsupported: {unsupported}"
    )

    return {
        "verified_evidence": verified,
        "run_status": run_status,
        "irrelevant_finding_count": irrelevant,
        "pipeline_diagnostics": {
            **state.get("pipeline_diagnostics", {}),
            "citation_checker": {
                "supported_claims": supported,
                "partially_supported_claims": partial,
                "unsupported_claims": unsupported,
                "irrelevant_claims": irrelevant,
                "errors": verification_errors,
                "rejected_claims": rejected_claims,
            },
        },
    }


# ============================================================
# 6. WRITER AGENT
# ============================================================

def writer_node(state: ResearchState):

    print("\n=== Writer Agent ===")

    topic = state["topic"]

    verified_evidence = (
        state["verified_evidence"]
    )

    print(
        "Generating final research report..."
    )

    # --------------------------------------------------------
    # Generate final report
    # --------------------------------------------------------

    report = generate_report(
        topic,
        verified_evidence,
        state.get("run_status", "INCOMPLETE"),
        state.get("pipeline_diagnostics", {}),
    )

    quality = evaluate_research_quality(
        topic=topic,
        questions=state.get("research_questions", []),
        verified_evidence=verified_evidence,
        report=report,
        run_status=state.get("run_status", "INCOMPLETE"),
        pipeline_diagnostics=state.get("pipeline_diagnostics", {}),
    )
    quality_lines = []
    for name, metric in quality["metrics"].items():
        score = (
            f"{metric['score']}/10"
            if metric["score"] is not None
            else "NOT_EVALUATED"
        )
        quality_lines.append(
            f"- **{name.replace('_', ' ').title()}:** {score} "
            f"(weight {metric['weight'] * 100:.0f}%). "
            f"{metric['criterion']}"
        )
    report += (
        "\n## Research Quality Evaluation\n\n"
        f"**Weighted score:** {quality['score_out_of_10']}/10 "
        f"(**{quality['status']}**; passing threshold: 9/10, "
        f"independently verified findings required: "
        f"{'yes' if quality['passing'] else 'no'}).\n\n"
        + "\n".join(quality_lines)
        + "\n\n**Limitations:** "
        + " ".join(quality["limitations"])
    )

    markdown_file = save_markdown(topic, report)
    pdf_file = save_pdf(topic, report)

    print("\n=== Report Generated ===")
    print("Markdown:", markdown_file)
    print("PDF:", pdf_file)

    return {
        "report": report,
        "markdown_file": markdown_file,
        "pdf_file": pdf_file,
        "research_quality": quality,
        "execution_status": "COMPLETED",
        "evidence_status": (
            "VERIFIED_EVIDENCE_FOUND"
            if any(
                finding.get("relevance_status") == "RELEVANT"
                and finding.get("status") in {
                    "SUPPORTED",
                    "PARTIALLY_SUPPORTED",
                }
                for group in verified_evidence
                for finding in group.get("findings", [])
            )
            else "NO_VERIFIED_EVIDENCE"
        ),
    }


# ============================================================
# LANGGRAPH WORKFLOW
# ============================================================

workflow = StateGraph(
    ResearchState
)


# ============================================================
# ADD NODES
# ============================================================

workflow.add_node(
    "planner",
    planner_node
)

workflow.add_node(
    "searcher",
    searcher_node
)

workflow.add_node(
    "researcher",
    researcher_node
)

workflow.add_node(
    "evidence_cleaner",
    evidence_cleaner_node
)

workflow.add_node(
    "citation_checker",
    citation_checker_node
)

workflow.add_node(
    "writer",
    writer_node
)


# ============================================================
# WORKFLOW CONNECTIONS
# ============================================================

workflow.add_edge(
    START,
    "planner"
)

workflow.add_edge(
    "planner",
    "searcher"
)

workflow.add_edge(
    "searcher",
    "researcher"
)

workflow.add_edge(
    "researcher",
    "evidence_cleaner"
)

workflow.add_edge(
    "evidence_cleaner",
    "citation_checker"
)

workflow.add_edge(
    "citation_checker",
    "writer"
)

workflow.add_edge(
    "writer",
    END
)


# ============================================================
# COMPILE WORKFLOW
# ============================================================

research_graph = workflow.compile()