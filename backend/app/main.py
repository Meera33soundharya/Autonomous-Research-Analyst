from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

from app.graph.workflow import research_graph


class ResearchRequest(BaseModel):
    topic: str


app = FastAPI(
    title="Autonomous Multi-Agent Research Analyst",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "Autonomous Research Analyst API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.get("/research")
def run_research_by_query(topic: str = Query(..., min_length=1)):
    if not topic or not topic.strip():
        raise HTTPException(
            status_code=400,
            detail="A non-empty research topic is required."
        )

    result = research_graph.invoke({
        "topic": topic.strip()
    })

    verified_evidence = result.get("verified_evidence", [])

    supported = 0
    partial = 0
    unsupported = 0

    for item in verified_evidence:
        for finding in item.get("findings", []):
            status = (finding.get("status") or "").upper()
            if status == "SUPPORTED":
                supported += 1
            elif status == "PARTIALLY_SUPPORTED":
                partial += 1
            else:
                unsupported += 1

    return {
        "topic": result.get("topic", topic.strip()),
        "research_questions": result.get("research_questions", []),
        "sources_collected": len(result.get("search_results", [])),
        "verified_evidence": verified_evidence,
        "supported_findings": supported,
        "partially_supported_findings": partial,
        "unsupported_findings": unsupported,
        "report": result.get("report", ""),
        "markdown_file": result.get("markdown_file"),
        "pdf_file": result.get("pdf_file"),
    }


@app.post("/research")
def run_research(request: ResearchRequest):
    if not request.topic or not request.topic.strip():
        raise HTTPException(
            status_code=400,
            detail="A non-empty research topic is required."
        )

    return run_research_by_query(request.topic)
