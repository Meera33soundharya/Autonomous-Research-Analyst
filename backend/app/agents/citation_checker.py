import json
import re
from pathlib import Path

from app.services.llm_service import ask_llm


VALID_STATUSES = {
    "SUPPORTED",
    "PARTIALLY_SUPPORTED",
    "UNSUPPORTED",
}

VALID_RELEVANCE_STATUSES = {
    "RELEVANT",
    "PARTIALLY_RELEVANT",
    "IRRELEVANT",
}


def _extract_status(response: str) -> str:
    match = re.search(
        r"\b(PARTIALLY_SUPPORTED|UNSUPPORTED|SUPPORTED)\b",
        (response or "").upper(),
    )
    return match.group(1) if match else "UNSUPPORTED"


def _extract_relevance(response: str) -> tuple[str, str]:
    match = re.search(
        r"(?im)^\s*(PARTIALLY_RELEVANT|IRRELEVANT|RELEVANT)\b"
        r"\s*(?:\||:|-)?\s*(.*)$",
        response or "",
    )
    if not match:
        return "IRRELEVANT", "No valid relevance decision was returned."
    status, reason = match.groups()
    return status, reason.strip()


def _check_relevance(
    finding: dict,
    topic: str,
    question: str = "",
) -> tuple[str, str]:
    claim = str(finding.get("claim", "")).strip()
    question = question or str(finding.get("question", "")).strip()
    source_content = str(finding.get("source_content", "")).strip()
    if not topic or not claim:
        return "IRRELEVANT", "The topic or claim is missing."

    prompt = f"""
You are a strict research-topic relevance evaluator.
Decide whether the claim directly answers the research topic or its scope.
Citation support alone does not make an unrelated claim relevant.

RESEARCH TOPIC:
{topic}

RESEARCH QUESTION:
{question}

CLAIM:
{claim}

SOURCE CONTEXT:
{source_content[:6000]}

Return one line in this exact form:
RELEVANT | reason
PARTIALLY_RELEVANT | reason
IRRELEVANT | reason

Use RELEVANT only when the claim directly concerns the topic. Use
PARTIALLY_RELEVANT when only a material part does. Do not use outside knowledge.
"""
    try:
        return _extract_relevance(ask_llm(prompt))
    except Exception:
        return "IRRELEVANT", "Relevance evaluation failed."


def _verify_finding(finding: dict) -> str:
    claim = str(finding.get("claim", "")).strip()
    source_content = str(finding.get("source_content", "")).strip()

    if not claim or not source_content:
        return "UNSUPPORTED"

    prompt = f"""
You are a strict citation verification agent.

Determine whether the CLAIM is supported by the SOURCE EVIDENCE.

CLAIM:
{claim}

SOURCE EVIDENCE:
{source_content[:12000]}

Return exactly ONE of these labels:

SUPPORTED
PARTIALLY_SUPPORTED
UNSUPPORTED

Rules:
- SUPPORTED = the source directly supports the main claim.
- PARTIALLY_SUPPORTED = the source supports only part of the claim.
- UNSUPPORTED = the source does not provide sufficient support.
- Do not use outside knowledge.
- Do not rewrite the claim.
- Do not output explanations.
"""

    try:
        response = ask_llm(prompt)
        return _extract_status(response)
    except Exception:
        return "UNSUPPORTED"


def check_citations(evidence: list[dict], topic: str = "") -> list[dict]:
    verified = []

    supported = 0
    partial = 0
    unsupported = 0

    for group in evidence:

        question = group.get("question", "")
        original_findings = group.get("findings", [])

        verified_findings = []

        for finding in original_findings:

            # IMPORTANT:
            # Start with the ORIGINAL finding so that
            # source_title, source_url, source_content,
            # source_quality, source_number, etc. are preserved.
            verified_finding = dict(finding)

            if topic:
                relevance, reason = _check_relevance(finding, topic, question)
                verified_finding["relevance_status"] = relevance
                verified_finding["relevance_reason"] = reason
                if relevance != "RELEVANT":
                    verified_finding["status"] = "UNSUPPORTED"
                    unsupported += 1
                    verified_findings.append(verified_finding)
                    continue

            status = _verify_finding(finding)

            verified_finding["status"] = status

            if status == "SUPPORTED":
                supported += 1

            elif status == "PARTIALLY_SUPPORTED":
                partial += 1

            else:
                unsupported += 1

            verified_findings.append(verified_finding)

        verified.append(
            {
                "question": question,
                "findings": verified_findings,
            }
        )

    print("\n=== Citation Checker ===")
    print(f"Supported: {supported}")
    print(f"Partially supported: {partial}")
    print(f"Unsupported: {unsupported}")

    return verified


def save_verified_evidence(evidence: list[dict]) -> None:

    path = (
        Path(__file__).resolve()
        .parents[3]
        / "reports"
        / "verified_evidence.jsonl"
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        path,
        "w",
        encoding="utf-8"
    ) as file:

        for group in evidence:

            file.write(
                json.dumps(
                    group,
                    ensure_ascii=False
                )
                + "\n"
            )