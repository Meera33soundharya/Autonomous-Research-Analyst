import json
import re
from pathlib import Path

from app.services.llm_service import ask_llm


VALID_STATUSES = {
    "SUPPORTED",
    "PARTIALLY_SUPPORTED",
    "UNSUPPORTED",
}


def _extract_status(response: str) -> str:
    if not response:
        return "PARTIALLY_SUPPORTED"

    text = response.upper()

    if "PARTIALLY_SUPPORTED" in text:
        return "PARTIALLY_SUPPORTED"

    if "SUPPORTED" in text:
        return "SUPPORTED"

    if "UNSUPPORTED" in text:
        return "UNSUPPORTED"

    return "PARTIALLY_SUPPORTED"


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
        return "PARTIALLY_SUPPORTED"


def check_citations(evidence: list[dict]) -> list[dict]:
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