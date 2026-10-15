import logging
import json
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlparse

from app.services.llm_service import ask_llm

logger = logging.getLogger(__name__)


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

MAX_VERIFICATION_WORKERS = 2


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
Decide whether the claim directly answers the stated research question and
materially informs the research topic or its scope. The topic may describe a
combined application with distinct components, so a source need not describe
the entire integrated system if it provides evidence about the component
asked about. A shared keyword alone is not enough.

RESEARCH TOPIC:
{topic}

RESEARCH QUESTION:
{question}

CLAIM:
{claim}

SOURCE CONTEXT:
{source_content[:6000]}

For example, generic evidence about a voice assistant is not relevant unless it
informs the voice-based complaint-registration question. Evidence about a
government workflow is not relevant unless it informs the stated grievance or
field-assignment question. Do not infer that independently studied components
have already been integrated into one deployed system.

Return one line in this exact form:
RELEVANT | reason
PARTIALLY_RELEVANT | reason
IRRELEVANT | reason

Use RELEVANT only when the claim directly concerns the topic. Use
PARTIALLY_RELEVANT when only a material part does. Do not use outside knowledge.
"""
    try:
        response = ask_llm(prompt)
        if "model service is unavailable" in response.lower():
            return "IRRELEVANT", response.strip()
        return _extract_relevance(response)
    except Exception as error:
        logger.exception("Relevance evaluation failed for claim %r", claim)
        return (
            "IRRELEVANT",
            f"Relevance evaluation failed ({type(error).__name__}: {error}).",
        )


def _verify_finding(finding: dict) -> tuple[str, str]:
    claim = str(finding.get("claim", "")).strip()
    source_content = str(finding.get("source_content", "")).strip()
    source_url = str(finding.get("source_url", "")).strip()
    supporting_passage = str(finding.get("supporting_passage", "")).strip()

    if not claim or not source_content or not supporting_passage:
        return (
            "UNSUPPORTED",
            "The claim, source content, or traceable supporting passage is missing.",
        )

    parsed_url = urlparse(source_url)
    if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
        return "UNSUPPORTED", "The finding has no valid HTTP(S) source URL."

    normalized_source = re.sub(r"\s+", " ", source_content)
    normalized_passage = re.sub(r"\s+", " ", supporting_passage)
    if normalized_passage not in normalized_source:
        return (
            "UNSUPPORTED",
            "The supporting passage does not occur verbatim in the source content.",
        )

    claim_numbers = {
        value.replace(",", "")
        for value in re.findall(r"(?<![A-Za-z])\d[\d,]*(?:\.\d+)?%?", claim)
    }
    passage_numbers = {
        value.replace(",", "")
        for value in re.findall(
            r"(?<![A-Za-z])\d[\d,]*(?:\.\d+)?%?",
            supporting_passage,
        )
    }
    if not claim_numbers.issubset(passage_numbers):
        missing_numbers = sorted(claim_numbers - passage_numbers)
        return (
            "UNSUPPORTED",
            "Numeric/date tokens in the claim are absent from the cited passage: "
            + ", ".join(missing_numbers),
        )

    prompt = f"""
You are a strict citation verification agent.

Determine whether the CLAIM is supported by the SOURCE EVIDENCE.

CLAIM:
{claim}

VERBATIM SUPPORTING PASSAGE FROM THE CITED SOURCE:
{supporting_passage[:4000]}

Return exactly ONE of these labels:

SUPPORTED
PARTIALLY_SUPPORTED
UNSUPPORTED

Rules:
- SUPPORTED = the quoted passage directly supports the complete claim,
  including its population, conditions, names, dates, and numeric values.
- PARTIALLY_SUPPORTED = the source supports only part of the claim.
- UNSUPPORTED = the source does not provide sufficient support.
- Do not use outside knowledge.
- Do not treat a similar topic as support for the claim.
- Do not rewrite the claim.
- Do not output explanations.
"""

    try:
        response = ask_llm(prompt)
        if "model service is unavailable" in response.lower():
            return "UNSUPPORTED", response.strip()
        status = _extract_status(response)
        if status == "UNSUPPORTED" and not response.strip():
            return status, "The citation checker returned an empty response."
        return status, ""
    except Exception as error:
        logger.exception("Citation verification failed for claim %r", claim)
        return (
            "UNSUPPORTED",
            f"Citation verification failed ({type(error).__name__}: {error}).",
        )


def _verify_claim_task(task: tuple[int, str, dict, str]) -> tuple[int, dict]:
    group_index, question, finding, topic = task
    verified_finding = dict(finding)

    if topic:
        relevance, reason = _check_relevance(finding, topic, question)
        verified_finding["relevance_status"] = relevance
        verified_finding["relevance_reason"] = reason
        if relevance != "RELEVANT":
            verified_finding["status"] = "UNSUPPORTED"
            return group_index, verified_finding

    status, verification_error = _verify_finding(finding)
    verified_finding["status"] = status
    if verification_error:
        verified_finding["verification_reason"] = verification_error
    return group_index, verified_finding


def check_citations(evidence: list[dict], topic: str = "") -> list[dict]:
    verified = [
        {
            "question": group.get("question", ""),
            "findings": [],
        }
        for group in evidence
    ]
    tasks = [
        (group_index, group.get("question", ""), finding, topic)
        for group_index, group in enumerate(evidence)
        for finding in group.get("findings", [])
    ]
    if tasks:
        with ThreadPoolExecutor(
            max_workers=min(MAX_VERIFICATION_WORKERS, len(tasks))
        ) as executor:
            results = executor.map(_verify_claim_task, tasks)
            for group_index, finding in results:
                verified[group_index]["findings"].append(finding)

    supported = sum(
        finding.get("status") == "SUPPORTED"
        for group in verified
        for finding in group["findings"]
    )
    partial = sum(
        finding.get("status") == "PARTIALLY_SUPPORTED"
        for group in verified
        for finding in group["findings"]
    )
    unsupported = sum(
        finding.get("status") == "UNSUPPORTED"
        for group in verified
        for finding in group["findings"]
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