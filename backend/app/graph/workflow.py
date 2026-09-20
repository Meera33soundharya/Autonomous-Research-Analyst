from langgraph.graph import StateGraph, START, END

from app.graph.state import ResearchState

from app.agents.planner import create_research_plan
from app.agents.searcher import run_search
from app.agents.researcher import analyze_sources
from app.agents.citation_checker import check_citations
from app.agents.writer import generate_report


def planner_node(state: ResearchState):
    topic = state["topic"]

    plan = create_research_plan(topic)

    return {
        "research_plan": plan
    }


def searcher_node(state: ResearchState):

    questions = [
        "What are the major healthcare applications of AI, such as diagnosis, treatment planning, and drug discovery?",
        "How effective are AI systems in improving clinical outcomes, accuracy, or efficiency?",
        "What are the main ethical, legal, and privacy concerns associated with AI in healthcare?",
        "What barriers limit the adoption of AI in clinical and administrative settings?",
        "How can AI systems be validated, regulated, and monitored to ensure safety and reliability?"
    ]

    results = run_search(questions)

    return {
        "questions": questions,
        "search_results": results
    }


def researcher_node(state: ResearchState):

    questions = state["questions"]
    sources = state["search_results"]

    all_evidence = []

    for question in questions:

        evidence = analyze_sources(
            question,
            sources
        )

        all_evidence.append(
            f"""
Research Question:
{question}

Evidence:
{evidence}
"""
        )

    combined_evidence = "\n\n".join(all_evidence)

    return {
        "evidence": combined_evidence
    }


def citation_node(state: ResearchState):

    evidence = state["evidence"]

    verified = check_citations(evidence)

    return {
        "verified_evidence": verified
    }


def writer_node(state: ResearchState):

    topic = state["topic"]
    verified_evidence = state["verified_evidence"]

    report = generate_report(
        topic,
        verified_evidence
    )

    return {
        "report": report
    }


builder = StateGraph(ResearchState)

builder.add_node("planner", planner_node)
builder.add_node("searcher", searcher_node)
builder.add_node("researcher", researcher_node)
builder.add_node("citation_checker", citation_node)
builder.add_node("writer", writer_node)

builder.add_edge(START, "planner")
builder.add_edge("planner", "searcher")
builder.add_edge("searcher", "researcher")
builder.add_edge("researcher", "citation_checker")
builder.add_edge("citation_checker", "writer")
builder.add_edge("writer", END)

research_graph = builder.compile()