from langgraph.graph import StateGraph, START, END

from app.graph.state import ResearchState

from app.agents.planner import create_research_plan
from app.agents.topic_normalizer import normalize_research_topic
from app.agents.searcher import run_search
from app.agents.researcher import analyze_sources
from app.agents.evidence_cleaner import clean_evidence
from app.agents.citation_checker import check_citations
from app.agents.writer import generate_report

from app.services.report_service import (
    save_markdown,
    save_pdf
)


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

    results = run_search(
        state["topic"],
        questions
    )

    print(
        f"Collected {len(results)} web sources."
    )

    return {
        "search_results": results,
        "source_count": len(results),
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

    print(
        f"Evidence groups created: {len(evidence)}"
    )

    return {
        "evidence": evidence,
        "extracted_finding_count": sum(
            len(item.get("findings", [])) for item in evidence
        ),
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
        "run_status": "COMPLETED" if topic_relevant else "INCOMPLETE",
        "irrelevant_finding_count": irrelevant,
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
        verified_evidence
    )

    # --------------------------------------------------------
    # Save Markdown
    # --------------------------------------------------------

    markdown_file = save_markdown(
        topic,
        report
    )

    # --------------------------------------------------------
    # Save PDF
    # --------------------------------------------------------

    pdf_file = save_pdf(
        topic,
        report
    )

    print(
        "\n=== Report Generated ==="
    )

    print(
        "Markdown:",
        markdown_file
    )

    print(
        "PDF:",
        pdf_file
    )

    return {
        "report": report,
        "markdown_file": markdown_file,
        "pdf_file": pdf_file
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