from langgraph.graph import StateGraph, START, END

from app.graph.state import ResearchState

from app.agents.searcher import run_search
from app.agents.researcher import analyze_sources
from app.agents.citation_checker import check_citations
from app.agents.writer import generate_report

from app.services.report_service import (
    save_markdown,
    save_pdf
)

from app.agents.planner import create_research_plan


# ============================================================
# 1. PLANNER AGENT
# ============================================================

def planner_node(state: ResearchState):
    
    print("\n=== Planner Agent ===")

    topic = state["topic"]

    print(
        f"Planning research for topic: {topic}"
    )

    questions = create_research_plan(topic)

    print(
        f"Generated {len(questions)} research questions."
    )

    for question in questions:
        print(f"- {question}")

    return {
        "research_questions": questions
    }


# ============================================================
# 2. SEARCHER AGENT
# ============================================================

def searcher_node(state: ResearchState):

    print("\n=== Searcher Agent ===")

    questions = state["research_questions"]

    results = run_search(questions)

    print(
        f"Collected {len(results)} web sources."
    )

    return {
        "search_results": results
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
            sources
        )

        evidence.append(result)

    print(
        f"Evidence groups created: {len(evidence)}"
    )

    return {
        "evidence": evidence
    }


# ============================================================
# 4. CITATION CHECKER AGENT
# ============================================================

def citation_checker_node(state: ResearchState):

    print("\n=== Citation Checker ===")

    evidence = state["evidence"]

    verified = check_citations(
        evidence
    )

    supported = 0
    unsupported = 0

    for item in verified:

        for finding in item.get(
            "findings",
            []
        ):

            if finding.get(
                "status"
            ) == "SUPPORTED":

                supported += 1

            else:

                unsupported += 1

    print(
        f"Supported: {supported}"
    )

    print(
        f"Unsupported: {unsupported}"
    )

    return {
        "verified_evidence": verified
    }


# ============================================================
# 5. WRITER AGENT
# ============================================================

def writer_node(state: ResearchState):

    print("\n=== Writer Agent ===")

    topic = state["topic"]

    verified_evidence = (
        state["verified_evidence"]
    )

    # Generate final report
    report = generate_report(
        topic,
        verified_evidence
    )

    # Save Markdown report
    markdown_file = save_markdown(
        topic,
        report
    )

    # Save PDF report
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


# Add agents
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